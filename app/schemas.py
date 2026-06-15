"""
Pydantic schemas for request validation and response serialisation.

Every response follows the ``{success: bool, ...}`` envelope so clients can
reliably distinguish success from error payloads.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Utility wrappers
# ---------------------------------------------------------------------------

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Envelope for successful responses carrying a ``data`` payload."""

    success: bool = True
    data: T


class ErrorDetail(BaseModel):
    """Structured error information returned on failure."""

    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard envelope for all error responses."""

    success: bool = False
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Returned by ``GET /api/health``."""

    status: str = "ok"
    database: str = "ok"
    model_loaded: bool = False
    article_count: int = 0


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

class ArticleCreate(BaseModel):
    """Payload for ``POST /api/articles`` (JSON)."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="文章标题，1–100 字符",
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="文章正文，10–50000 字符",
    )
    source_type: str = Field(
        default="text",
        description="来源类型：text 或 file",
    )
    source_name: Optional[str] = Field(
        default=None,
        description="原始文件名（上传时填充）",
    )

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("标题不能为空白字符")
        return stripped

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("正文不能为空白字符")
        return stripped

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if v not in ("text", "file"):
            raise ValueError("source_type 必须为 text 或 file")
        return v


class ArticleData(BaseModel):
    """Article payload inside a success response."""

    id: int
    title: str
    chunk_count: int = 0


class ArticleListItem(BaseModel):
    """A single row shown in the article pagination list."""

    id: int
    title: str
    source_type: str
    source_name: Optional[str] = None
    created_at: str
    chunk_count: int = 0


class ArticleListData(BaseModel):
    """Pagination wrapper returned by ``GET /api/articles``."""

    items: list[ArticleListItem]
    page: int
    page_size: int
    total: int
    total_pages: int
