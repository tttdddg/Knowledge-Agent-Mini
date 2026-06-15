"""
Application exceptions and FastAPI exception handlers.

Every error returned to the client follows the unified structure::

    {
      "success": false,
      "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable description",
        "details": null
      }
    }
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ErrorDetail, ErrorResponse


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------


class AppException(Exception):
    """
    Base application exception.

    Subclasses carry a stable *code*, a human-readable *message*, an HTTP
    *status_code*, and optional *details*.
    """

    code: str = "INTERNAL_ERROR"
    message: str = "服务器内部错误"
    status_code: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        details: Any = None,
    ) -> None:
        self._message = message or self.message
        self.details = details
        super().__init__(self._message)

    @property
    def error_message(self) -> str:
        return self._message


# ---------------------------------------------------------------------------
# Validation errors (400)
# ---------------------------------------------------------------------------


class InvalidTitleError(AppException):
    code = "INVALID_TITLE"
    message = "文章标题不合法"
    status_code = 400


class InvalidContentError(AppException):
    code = "INVALID_CONTENT"
    message = "文章正文不合法"
    status_code = 400


class EmptyQueryError(AppException):
    code = "EMPTY_QUERY"
    message = "查询内容不能为空"
    status_code = 400


class InvalidFileTypeError(AppException):
    code = "INVALID_FILE_TYPE"
    message = "仅支持上传 .txt 文件"
    status_code = 400


class FileEncodingError(AppException):
    code = "FILE_ENCODING_ERROR"
    message = "无法识别文本文件编码，请转换为 UTF-8 后重新上传"
    status_code = 400


# ---------------------------------------------------------------------------
# Request entity errors (413)
# ---------------------------------------------------------------------------


class FileTooLargeError(AppException):
    code = "FILE_TOO_LARGE"
    message = "上传文件过大"
    status_code = 413


# ---------------------------------------------------------------------------
# Conflict / state errors (409)
# ---------------------------------------------------------------------------


class KnowledgeBaseEmptyError(AppException):
    code = "KNOWLEDGE_BASE_EMPTY"
    message = "知识库中暂无文章"
    status_code = 409


# ---------------------------------------------------------------------------
# Service errors (503 / 504)
# ---------------------------------------------------------------------------


class ModelUnavailableError(AppException):
    code = "MODEL_UNAVAILABLE"
    message = "Embedding 模型不可用"
    status_code = 503


class ServiceUnavailableError(AppException):
    code = "SERVICE_UNAVAILABLE"
    message = "知识库服务未启动或无法连接"
    status_code = 503


class SearchTimeoutError(AppException):
    code = "SEARCH_TIMEOUT"
    message = "知识库查询超时"
    status_code = 504


# ---------------------------------------------------------------------------
# Database / internal (500)
# ---------------------------------------------------------------------------


class DatabaseError(AppException):
    code = "DATABASE_ERROR"
    message = "数据库操作失败"
    status_code = 500


class InternalError(AppException):
    code = "INTERNAL_ERROR"
    message = "服务器内部错误"
    status_code = 500


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------


def _to_error_response(
    code: str,
    message: str,
    details: Any = None,
    status_code: int = 400,
) -> JSONResponse:
    """Build a ``JSONResponse`` conforming to the unified error schema."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, details=details),
        ).model_dump(),
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all ``AppException`` subclasses."""
    return _to_error_response(
        code=exc.code,
        message=exc.error_message,
        details=exc.details,
        status_code=exc.status_code,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI request validation errors with the unified error format."""
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field,
                "message": error["msg"],
            }
        )

    return _to_error_response(
        code="VALIDATION_ERROR",
        message="请求参数校验失败",
        details=errors if errors else None,
        status_code=422,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    return _to_error_response(
        code="INTERNAL_ERROR",
        message="服务器内部错误",
        status_code=500,
    )
