"""
Smoke-test script for Knowledge Agent Mini.

Runs against a **running** FastAPI backend and verifies the core user-facing
scenarios end-to-end.

Usage::

    python scripts/smoke_test.py

Prerequisites: the FastAPI server must be running on ``127.0.0.1:8000``.
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Callable

import httpx

API_BASE = os.getenv("KNOWLEDGE_API_BASE", "http://127.0.0.1:8000")
TIMEOUT = 120.0  # generous for model warm-up

passed = 0
failed = 0


def run_test(name: str, fn: Callable[[], None]) -> None:
    """Execute *fn* and print ``[PASS]`` or ``[FAIL]``."""
    global passed, failed
    try:
        fn()
        print(f"[PASS] {name}")
        passed += 1
    except Exception as exc:
        print(f"[FAIL] {name} — {exc}")
        failed += 1


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_api_health() -> None:
    r = httpx.get(f"{API_BASE}/api/health", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


def test_create_article() -> None:
    unique_title = f"smoke-test-{uuid.uuid4().hex[:6]}"
    r = httpx.post(
        f"{API_BASE}/api/articles",
        json={
            "title": unique_title,
            "content": "这是一篇冒烟测试文章。它包含足够的文字来通过正文长度校验，并且会被自动切分和向量化。",
        },
        timeout=TIMEOUT,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["success"] is True
    assert data["data"]["id"] > 0
    assert data["data"]["title"] == unique_title
    assert data["data"]["chunk_count"] >= 1


def test_article_pagination() -> None:
    r = httpx.get(
        f"{API_BASE}/api/articles", params={"page": 1, "page_size": 5}, timeout=10
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 1
    assert data["data"]["page"] == 1
    assert len(data["data"]["items"]) >= 1


def test_semantic_search() -> None:
    r = httpx.post(
        f"{API_BASE}/api/search",
        json={"query": "冒烟测试", "top_k": 3},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert len(data["results"]) >= 1
    for item in data["results"]:
        assert "article_id" in item
        assert "title" in item
        assert "snippet" in item
        assert "score" in item


def test_empty_query_validation() -> None:
    r = httpx.post(
        f"{API_BASE}/api/search",
        json={"query": "   ", "top_k": 3},
        timeout=10,
    )
    # Should return an error (422 from Pydantic validation)
    assert r.status_code >= 400
    data = r.json()
    # Either our error format or FastAPI's validation format
    assert data.get("success") is False or "detail" in data


def test_no_result_fallback() -> None:
    """Verify the system handles queries gracefully without crashing.

    The response format must be valid regardless of whether results are
    returned (real semantic matches depend on the model and threshold).
    """
    r = httpx.post(
        f"{API_BASE}/api/search",
        json={"query": "量子芯片制造工艺详解手册", "top_k": 3},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "request_id" in data
    assert "results" in data
    assert "message" in data
    # Verify each result has the required fields
    for item in data["results"]:
        assert "article_id" in item
        assert "title" in item
        assert "snippet" in item
        assert "score" in item
    # System must not crash — that's the core requirement


def test_streaming_search() -> None:
    r = httpx.get(
        f"{API_BASE}/api/search/stream",
        params={"query": "冒烟测试", "top_k": 3},
        timeout=30,
    )
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    assert len(r.text) > 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("Knowledge Agent Mini — Smoke Tests")
    print(f"Target: {API_BASE}")
    print()

    tests: list[tuple[str, Callable[[], None]]] = [
        ("API health", test_api_health),
        ("Create article", test_create_article),
        ("Article pagination", test_article_pagination),
        ("Semantic search", test_semantic_search),
        ("Empty query validation", test_empty_query_validation),
        ("No-result fallback", test_no_result_fallback),
        ("Streaming search", test_streaming_search),
    ]

    for name, fn in tests:
        run_test(name, fn)

    print()
    print(f"Results:  {passed} passed  {failed} failed  ({passed + failed} total)")
    print()

    if failed == 0:
        print("All smoke tests passed.")
        return 0
    else:
        print(f"{failed} test(s) FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
