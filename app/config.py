"""
Application configuration loaded from environment variables.

All settings have sensible defaults and can be overridden via environment
variables or a ``.env`` file placed in the project root.
"""

import os
from pathlib import Path

# Resolve the project root directory (parent of ``app/``).
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env(key: str, default: str) -> str:
    """Return the value of an environment variable, falling back to *default*."""
    return os.getenv(key, default)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_NAME: str = _env("APP_NAME", "Knowledge Agent Mini")
APP_HOST: str = _env("APP_HOST", "127.0.0.1")
APP_PORT: int = int(_env("APP_PORT", "8000"))

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_PATH: str = _env("DATABASE_PATH", str(PROJECT_ROOT / "data" / "knowledge.db"))

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = _env("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
CHUNK_SIZE: int = int(_env("CHUNK_SIZE", "300"))
CHUNK_OVERLAP: int = int(_env("CHUNK_OVERLAP", "50"))

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
DEFAULT_TOP_K: int = int(_env("DEFAULT_TOP_K", "3"))
MAX_TOP_K: int = int(_env("MAX_TOP_K", "5"))
SIMILARITY_THRESHOLD: float = float(_env("SIMILARITY_THRESHOLD", "0.35"))

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------
MAX_TEXT_LENGTH: int = int(_env("MAX_TEXT_LENGTH", "50000"))
MAX_FILE_SIZE: int = int(_env("MAX_FILE_SIZE", "1048576"))  # 1 MB

# ---------------------------------------------------------------------------
# MCP / external integration
# ---------------------------------------------------------------------------
KNOWLEDGE_API_BASE: str = _env("KNOWLEDGE_API_BASE", "http://127.0.0.1:8000")
MCP_REQUEST_TIMEOUT: float = float(_env("MCP_REQUEST_TIMEOUT", "10"))
