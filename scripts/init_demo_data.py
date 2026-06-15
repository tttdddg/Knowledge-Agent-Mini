"""
Initialise the knowledge base with sample TXT files.

Usage::

    python scripts/init_demo_data.py

The script reads every ``.txt`` file under ``sample_data/``, uploads it to the
running FastAPI backend, and reports success / skip / failure counts.

Files whose title (filename stem) already exists in the database are skipped
so the script is safe to run multiple times.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

# Resolve directories relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SAMPLE_DIR = _PROJECT_ROOT / "sample_data"

API_BASE = os.getenv("KNOWLEDGE_API_BASE", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("MCP_REQUEST_TIMEOUT", "120"))

_TXT_ENCODINGS = ["utf-8-sig", "utf-8", "gb18030"]


def decode_file(path: Path) -> str:
    """Try to decode *path* using the supported encoding list."""
    raw = path.read_bytes()
    last_err: Exception | None = None
    for enc in _TXT_ENCODINGS:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError) as exc:
            last_err = exc
            continue
    raise ValueError(
        f"无法解码 {path.name}，尝试的编码：{_TXT_ENCODINGS}"
    ) from last_err


def get_existing_titles(client: httpx.Client) -> set[str]:
    """Fetch all article titles currently in the knowledge base."""
    titles: set[str] = set()
    page = 1
    while True:
        r = client.get(
            f"{API_BASE}/api/articles", params={"page": page, "page_size": 50}
        )
        r.raise_for_status()
        body = r.json()
        if not body.get("success"):
            break
        data = body["data"]
        for item in data["items"]:
            titles.add(item["title"])
        if data["page"] >= data["total_pages"]:
            break
        page += 1
    return titles


def main() -> int:
    """Run the initialisation and return 0 on success, 1 on partial failure."""
    if not _SAMPLE_DIR.is_dir():
        print(f"[ERROR] Sample data directory not found: {_SAMPLE_DIR}")
        return 1

    txt_files = sorted(_SAMPLE_DIR.glob("*.txt"))
    if not txt_files:
        print("[WARN] No .txt files found in sample_data/")
        return 0

    print(f"Found {len(txt_files)} TXT file(s) in {_SAMPLE_DIR}")

    success = 0
    skipped = 0
    failed = 0

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        # Check connectivity
        try:
            r = client.get(f"{API_BASE}/api/health")
            r.raise_for_status()
            print(f"Connected to {API_BASE} — status: ok")
        except Exception as exc:
            print(f"[ERROR] Cannot reach {API_BASE}: {exc}")
            print("Please start the FastAPI backend first:")
            print("  uvicorn app.main:app --host 127.0.0.1 --port 8000")
            return 1

        existing = get_existing_titles(client)
        if existing:
            print(f"Existing titles in DB: {len(existing)}")

        for path in txt_files:
            title = path.stem
            if title in existing:
                print(f"  [SKIP] '{title}' — already exists")
                skipped += 1
                continue

            try:
                content = decode_file(path)
                r = client.post(
                    f"{API_BASE}/api/articles/upload",
                    files={"file": (path.name, content.encode("utf-8"), "text/plain")},
                    data={"title": title},
                )
                r.raise_for_status()
                body = r.json()
                if body.get("success"):
                    chunk_count = body["data"]["chunk_count"]
                    print(f"  [OK]  '{title}' → {chunk_count} chunks")
                    success += 1
                    existing.add(title)
                else:
                    msg = body.get("error", {}).get("message", "unknown")
                    print(f"  [FAIL] '{title}' — {msg}")
                    failed += 1
            except Exception as exc:
                print(f"  [FAIL] '{title}' — {exc}")
                failed += 1

    print()
    print(f"Done.  success={success}  skipped={skipped}  failed={failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
