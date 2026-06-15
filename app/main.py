"""
FastAPI application — Knowledge Agent Mini.

Start with::

    uvicorn app.main:app --host 127.0.0.1 --port 8000

API documentation is available at ``http://127.0.0.1:8000/docs``.
"""

from __future__ import annotations

import math
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import APP_NAME, APP_HOST, APP_PORT
from app.database import get_db, init_db, utcnow
from app.exceptions import (
    AppException,
    InvalidContentError,
    InvalidTitleError,
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
    SuccessResponse,
)


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
        model_loaded=False,  # Embedding model is lazy-loaded later
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

    The article is saved immediately; text chunking and embedding
    generation happen in a later processing step.
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
        db.commit()
        article_id = cursor.lastrowid
    except sqlite3.Error as exc:
        db.rollback()
        raise AppException(
            message=f"保存文章失败：{exc}",
            details=None,
        ) from exc

    return JSONResponse(
        status_code=201,
        content=SuccessResponse(
            data=ArticleData(
                id=article_id,
                title=body.title,
                chunk_count=0,
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
# Static files — served at the root path
# ---------------------------------------------------------------------------

# Moved to a later PR when static files exist.
# @app.get("/")
# async def root():
#     ...


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
