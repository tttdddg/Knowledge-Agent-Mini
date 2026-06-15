"""
SQLite database initialisation and connection helpers.

Creates the ``articles`` and ``chunks`` tables on first use and exposes a
simple ``get_db`` dependency for FastAPI path functions.
"""

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

from app.config import DATABASE_PATH


def _ensure_data_dir() -> None:
    """Make sure the directory containing the database file exists."""
    data_dir = Path(DATABASE_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """
    Create the database tables and indexes if they do not already exist.

    Safe to call at application startup — uses ``CREATE TABLE IF NOT EXISTS``
    so existing data is never destroyed.
    """
    _ensure_data_dir()

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                source_type TEXT    NOT NULL,
                source_name TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id  INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT    NOT NULL,
                embedding   BLOB    NOT NULL,
                created_at  TEXT    NOT NULL,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_article_id
                ON chunks(article_id);

            CREATE INDEX IF NOT EXISTS idx_articles_created_at
                ON articles(created_at);
            """
        )


def get_db() -> sqlite3.Connection:
    """
    Return a new SQLite connection with WAL mode and foreign keys enabled.

    Intended for use as a FastAPI dependency::

        @app.get("/items")
        def list_items(db: sqlite3.Connection = Depends(get_db)):
            ...
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def utcnow() -> str:
    """Return the current UTC time as an ISO‑8601 string."""
    return datetime.now(timezone.utc).isoformat()
