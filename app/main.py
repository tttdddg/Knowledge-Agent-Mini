"""
FastAPI application — Knowledge Agent Mini.

Start with::

    uvicorn app.main:app --host 127.0.0.1 --port 8000

API documentation is available at ``http://127.0.0.1:8000/docs``.
The Web UI is served at ``http://127.0.0.1:8000``.
"""

from __future__ import annotations

import asyncio
import math
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Query,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles

from app.config import (
    APP_NAME,
    APP_HOST,
    APP_PORT,
    MAX_FILE_SIZE,
)
from app.database import get_db, init_db, utcnow
from app.exceptions import (
    AppException,
    FileEncodingError,
    FileTooLargeError,
    InvalidFileTypeError,
    app_exception_handler,
    generic_exception_handler,
    request_validation_exception_handler,
)
from app.schemas import (
    ArticleCreate,
    ArticleData,
    ArticleListData,
    ArticleListItem,
    HealthResponse,
    ErrorResponse,
    ErrorDetail,
    SearchRequest,
    SearchResponse,
    SuccessResponse,
)
from app.services.embedding_service import embedding_service
from app.services.knowledge_service import ingest_article, search_knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database on startup."""
    init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
def health(db: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Return server and database status along with the article count."""
    try:
        row = db.execute("SELECT COUNT(*) AS cnt FROM articles").fetchone()
        article_count: int = row["cnt"] if row else 0
        db_ok = "ok"
    except sqlite3.Error:
        article_count = 0
        db_ok = "error"

    return HealthResponse(
        status="ok",
        database=db_ok,
        model_loaded=embedding_service.is_loaded,
        article_count=article_count,
    )


# ---------------------------------------------------------------------------
# Article endpoints
# ---------------------------------------------------------------------------


@app.post("/api/articles", status_code=201)
def create_article(
    body: ArticleCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> JSONResponse:
    """
    Create a new article from a JSON payload.

    The article is saved, chunked, and embedded inside a single transaction.
    If embedding fails the article insert is rolled back so the database never
    contains an article without chunks.
    """
    try:
        cursor = db.execute(
            """
            INSERT INTO articles (title, content, source_type, source_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                body.title,
                body.content,
                body.source_type,
                body.source_name,
                utcnow(),
            ),
        )
        article_id = cursor.lastrowid

        # Chunk + embed inside the same transaction.
        chunk_count = ingest_article(article_id, body.content, db)

        db.commit()
    except (sqlite3.Error, AppException):
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise AppException(
            message=f"保存文章失败：{exc}",
        ) from exc

    return JSONResponse(
        status_code=201,
        content=SuccessResponse(
            data=ArticleData(
                id=article_id,
                title=body.title,
                chunk_count=chunk_count,
            )
        ).model_dump(),
    )


@app.get("/api/articles")
def list_articles(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=5, ge=1, le=20, description="每页条数"),
    db: sqlite3.Connection = Depends(get_db),
) -> JSONResponse:
    """Return a paginated list of articles ordered by creation time (newest first)."""
    try:
        # Total count
        total_row = db.execute("SELECT COUNT(*) AS cnt FROM articles").fetchone()
        total: int = total_row["cnt"] if total_row else 0
        total_pages: int = max(1, math.ceil(total / page_size))

        # Bounded page
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size

        rows = db.execute(
            """
            SELECT a.id,
                   a.title,
                   a.source_type,
                   a.source_name,
                   a.created_at,
                   COUNT(ch.id) AS chunk_count
            FROM articles a
            LEFT JOIN chunks ch ON ch.article_id = a.id
            GROUP BY a.id
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()

        items = [
            ArticleListItem(
                id=row["id"],
                title=row["title"],
                source_type=row["source_type"],
                source_name=row["source_name"],
                created_at=row["created_at"],
                chunk_count=row["chunk_count"],
            )
            for row in rows
        ]
    except sqlite3.Error as exc:
        raise AppException(
            message=f"查询文章列表失败：{exc}",
        ) from exc

    return JSONResponse(
        status_code=200,
        content=SuccessResponse(
            data=ArticleListData(
                items=items,
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            )
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

# Resolve the project root for static and sample directories.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Encoding detection order for TXT uploads.
_TXT_ENCODINGS = ["utf-8-sig", "utf-8", "gb18030"]


def _decode_file_content(raw: bytes, filename: str) -> str:
    """Try to decode *raw* bytes using the supported encoding list."""
    last_error: Optional[Exception] = None
    for enc in _TXT_ENCODINGS:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError) as exc:
            last_error = exc
            continue
    raise FileEncodingError(
        message=f"无法识别文件编码（{filename}），请转换为 UTF-8 后重新上传。",
        details={"tried_encodings": _TXT_ENCODINGS},
    )


@app.post("/api/articles/upload", status_code=201)
def upload_article(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    db: sqlite3.Connection = Depends(get_db),
) -> JSONResponse:
    """
    Upload a ``.txt`` file as a new article.

    - Only ``.txt`` files are accepted.
    - File size is validated against ``MAX_FILE_SIZE`` (default 1 MB).
    - Encodings are tried in order: UTF-8 BOM → UTF-8 → GB18030.
    - If *title* is omitted the original filename (minus extension) is used.
    """
    # --- file-type check ----------------------------------------------------
    filename: str = file.filename or "unknown"
    if not filename.lower().endswith(".txt"):
        raise InvalidFileTypeError(
            message=f"仅支持上传 .txt 文件，收到：{filename}",
            details={"filename": filename},
        )

    # --- read (with size guard) ---------------------------------------------
    raw = file.file.read(MAX_FILE_SIZE + 1)
    if len(raw) > MAX_FILE_SIZE:
        raise FileTooLargeError(
            message=f"文件过大（最大 1 MB），实际大小：{len(raw)} 字节",
            details={"size": len(raw), "max_size": MAX_FILE_SIZE},
        )

    # --- decode -------------------------------------------------------------
    content = _decode_file_content(raw, filename)

    # --- fallback title -----------------------------------------------------
    article_title = (title or "").strip()
    if not article_title:
        article_title = Path(filename).stem

    # --- persist article + chunks (transactional) ---------------------------
    try:
        cursor = db.execute(
            """
            INSERT INTO articles (title, content, source_type, source_name, created_at)
            VALUES (?, ?, 'file', ?, ?)
            """,
            (article_title, content, filename, utcnow()),
        )
        article_id = cursor.lastrowid
        chunk_count = ingest_article(article_id, content, db)
        db.commit()
    except (sqlite3.Error, AppException):
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise AppException(message=f"上传文章失败：{exc}") from exc

    return JSONResponse(
        status_code=201,
        content=SuccessResponse(
            data=ArticleData(
                id=article_id,
                title=article_title,
                chunk_count=chunk_count,
            )
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Search endpoints
# ---------------------------------------------------------------------------


@app.post("/api/search")
def search(
    body: SearchRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> JSONResponse:
    """
    Semantic search over the knowledge base.

    Returns the top-K articles whose chunks are most similar to *query*,
    together with the matching snippet, source, and similarity score.
    """
    result = search_knowledge(
        query=body.query,
        db=db,
        top_k=body.top_k,
    )
    return JSONResponse(status_code=200, content=result)


@app.get("/api/search/stream")
async def search_stream(
    query: str = Query(..., min_length=1, description="自然语言查询"),
    top_k: int = Query(default=3, ge=1, le=5, description="返回数量"),
) -> StreamingResponse:
    """
    Streaming semantic search — returns results character-by-character.

    The backend performs a full semantic search first, then streams the
    formatted text back to the client using ``text/plain; charset=utf-8``.
    A fresh database connection is opened inside the async handler to avoid
    SQLite thread-safety issues.
    """
    from app.database import get_db

    # Open a fresh connection for this request (thread-safe).
    db = get_db()
    try:
        result = search_knowledge(query=query, db=db, top_k=top_k)
    finally:
        db.close()

    # Build the response text.
    lines: list[str] = []
    if result["results"]:
        lines.append(f"找到 {len(result['results'])} 条相关内容。\n")
        for i, item in enumerate(result["results"], 1):
            percentage = round(item["score"] * 100, 2)
            lines.append(
                f"【{i}】《{item['title']}》\n"
                f"{item['snippet']}\n"
                f"来源：{item.get('source_name') or '未知'}\n"
                f"相关度：{percentage}%\n"
            )
    else:
        lines.append("知识库中未检索到足够相关的内容。\n")

    full_text = "".join(lines)

    async def stream_text(text: str):
        """Yield characters one at a time for a streaming effect."""
        for char in text:
            yield char
            await asyncio.sleep(0.015)

    return StreamingResponse(
        stream_text(full_text),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Static files and root page
# ---------------------------------------------------------------------------

_STATIC_DIR = _PROJECT_ROOT / "app" / "static"

if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the single-page Web UI."""
    index_path = _STATIC_DIR / "index.html"
    if index_path.is_file():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Knowledge Agent Mini</h1>", status_code=200)


# ---------------------------------------------------------------------------
# Run (for development convenience)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
    )
