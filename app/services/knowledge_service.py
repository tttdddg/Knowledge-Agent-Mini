"""
Knowledge-base ingestion and semantic search.

All search operations go through the module-level singleton
:class:`EmbeddingService` so the model is loaded once and reused.
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from app.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DEFAULT_TOP_K,
    MAX_TOP_K,
    SIMILARITY_THRESHOLD,
    MAX_TEXT_LENGTH,
)
from app.database import utcnow
from app.exceptions import (
    EmptyQueryError,
    KnowledgeBaseEmptyError,
    ModelUnavailableError,
    DatabaseError,
)
from app.services.chunk_service import clean_text, chunk_text
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single de-duplicated search hit."""

    article_id: int
    title: str
    snippet: str
    source_name: Optional[str]
    score: float


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


def ingest_article(article_id: int, content: str, db: sqlite3.Connection) -> int:
    """
    Chunk *content*, generate embeddings, and persist them to the ``chunks`` table.

    Returns the number of chunks created.

    All inserts happen inside the already-open *db* transaction.  The caller
    is responsible for committing or rolling back.
    """
    cleaned = clean_text(content)
    chunks = chunk_text(cleaned, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    if not chunks:
        logger.warning("Article %d produced no chunks after cleaning.", article_id)
        return 0

    try:
        vectors = embedding_service.encode(chunks)
    except ModelUnavailableError:
        raise
    except Exception as exc:
        logger.exception("Embedding generation failed for article %d", article_id)
        raise ModelUnavailableError(
            message=f"向量生成失败：{exc}"
        ) from exc

    now = utcnow()
    for idx, (text, vec) in enumerate(zip(chunks, vectors)):
        db.execute(
            """
            INSERT INTO chunks (article_id, chunk_index, content, embedding, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (article_id, idx, text, vec.astype("float32").tobytes(), now),
        )

    logger.info(
        "Article %d ingested with %d chunks (model: %s)",
        article_id,
        len(chunks),
        embedding_service.model_name,
    )
    return len(chunks)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_knowledge(
    query: str,
    db: sqlite3.Connection,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = SIMILARITY_THRESHOLD,
) -> dict[str, Any]:
    """
    Run a semantic search over the knowledge base.

    Parameters
    ----------
    query:
        Natural-language query string (must not be empty / blank).
    db:
        Open SQLite connection.
    top_k:
        Maximum number of results to return (clamped to ``[1, MAX_TOP_K]``).
    threshold:
        Minimum cosine-similarity score (0–1).  Hits below this value are
        discarded.

    Returns
    -------
    dict
        A dictionary matching the ``SearchResponse`` schema (see
        :ref:`app.schemas`).
    """
    request_id = uuid.uuid4().hex[:8]
    started_at = time.monotonic()

    # ---- validate query ----------------------------------------------------
    query = query.strip()
    if not query:
        raise EmptyQueryError()

    if len(query) > 500:
        raise EmptyQueryError(message="查询内容不能超过 500 个字符")

    top_k = max(1, min(top_k, MAX_TOP_K))

    # ---- check knowledge base ----------------------------------------------
    try:
        row = db.execute("SELECT COUNT(*) AS cnt FROM chunks").fetchone()
        chunk_total: int = row["cnt"] if row else 0
    except sqlite3.Error as exc:
        raise DatabaseError(message=f"查询知识库失败：{exc}") from exc

    if chunk_total == 0:
        raise KnowledgeBaseEmptyError()

    # ---- embed query -------------------------------------------------------
    try:
        query_vec = embedding_service.encode([query])[0]
    except ModelUnavailableError:
        raise
    except Exception as exc:
        logger.exception("Failed to embed query")
        raise ModelUnavailableError(message=f"查询向量生成失败：{exc}") from exc

    # ---- load all chunk embeddings -----------------------------------------
    try:
        rows = db.execute(
            """
            SELECT ch.id,
                   ch.article_id,
                   ch.content,
                   ch.embedding,
                   a.title,
                   a.source_name
            FROM chunks ch
            JOIN articles a ON a.id = ch.article_id
            """
        ).fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(message=f"读取向量数据失败：{exc}") from exc

    if not rows:
        raise KnowledgeBaseEmptyError()

    # ---- compute cosine similarity (dot product on normalised vectors) -----
    results: list[dict[str, Any]] = []
    for row in rows:
        try:
            chunk_vec = np.frombuffer(row["embedding"], dtype=np.float32)
            score = float(np.dot(query_vec, chunk_vec))
        except Exception:
            continue

        if score < threshold:
            continue

        results.append(
            {
                "article_id": row["article_id"],
                "title": row["title"],
                "snippet": row["content"],
                "source_name": row["source_name"],
                "score": round(score, 4),
            }
        )

    # ---- sort, deduplicate, top-k ------------------------------------------
    results.sort(key=lambda r: r["score"], reverse=True)

    # Keep only the best result per article.
    best_by_article: dict[int, dict[str, Any]] = {}
    for r in results:
        aid = r["article_id"]
        if aid not in best_by_article:
            best_by_article[aid] = r

    final = list(best_by_article.values())[:top_k]

    duration_ms = round((time.monotonic() - started_at) * 1000)

    if not final:
        message = "知识库中未检索到足够相关的内容"
    else:
        message = f"共找到 {len(final)} 条相关内容"

    logger.info(
        "search request_id=%s query=%r top_k=%d result_count=%d duration_ms=%d",
        request_id,
        query,
        top_k,
        len(final),
        duration_ms,
    )

    return {
        "success": True,
        "request_id": request_id,
        "query": query,
        "results": final,
        "message": message,
    }
