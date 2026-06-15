"""
API integration tests for Knowledge Agent Mini.

Uses FastAPI's ``TestClient`` so the server does not need to be running.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, DATABASE_PATH

# ---------------------------------------------------------------------------
# Test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """Return a TestClient pointed at an isolated SQLite database."""
    db_path = str(tmp_path / "test_knowledge.db")
    # Patch both the config module AND the database module (which imported
    # DATABASE_PATH at module level).
    monkeypatch.setattr("app.config.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.DATABASE_PATH", db_path)
    # Ensure fresh tables in the isolated database.
    init_db()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert data["article_count"] == 0


# ---------------------------------------------------------------------------
# Articles — creation
# ---------------------------------------------------------------------------


class TestCreateArticle:
    def test_create_valid_article(self, client):
        r = client.post(
            "/api/articles",
            json={
                "title": "Test Article",
                "content": "This content is long enough to pass the minimum validation requirement for the API.",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Article"
        assert data["data"]["chunk_count"] >= 1

    def test_create_article_empty_title(self, client):
        r = client.post(
            "/api/articles",
            json={
                "title": "   ",
                "content": "A valid content body that meets the minimum length requirement.",
            },
        )
        assert r.status_code == 422
        data = r.json()
        assert data["success"] is False or "detail" in data

    def test_create_article_short_content(self, client):
        r = client.post(
            "/api/articles",
            json={"title": "Test", "content": "short"},
        )
        assert r.status_code == 422
        data = r.json()
        assert data["success"] is False or "detail" in data

    def test_create_article_missing_fields(self, client):
        r = client.post("/api/articles", json={})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Articles — pagination
# ---------------------------------------------------------------------------


class TestListArticles:
    def test_empty_list(self, client):
        r = client.get("/api/articles", params={"page": 1, "page_size": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    def test_pagination_with_data(self, client):
        # Create 3 articles
        for i in range(3):
            client.post(
                "/api/articles",
                json={
                    "title": f"Article {i}",
                    "content": f"This is article number {i} with enough text to pass validation requirements.",
                },
            )
        r = client.get("/api/articles", params={"page": 1, "page_size": 2})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total_pages"] == 2

        # Page 2
        r = client.get("/api/articles", params={"page": 2, "page_size": 2})
        assert r.status_code == 200
        data = r.json()
        assert len(data["data"]["items"]) == 1

    def test_invalid_page_parameters(self, client):
        r = client.get("/api/articles", params={"page": 0, "page_size": 5})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.fixture(autouse=True)
    def _seed(self, client):
        """Ensure at least one article exists for search tests."""
        client.post(
            "/api/articles",
            json={
                "title": "Spring",
                "content": "Spring is a beautiful season. Flowers bloom and birds sing in the springtime. The weather becomes warmer and days grow longer.",
            },
        )

    def test_search_valid_query(self, client):
        r = client.post(
            "/api/search",
            json={"query": "spring season", "top_k": 3},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "request_id" in data
        assert len(data["results"]) >= 1
        result = data["results"][0]
        assert "article_id" in result
        assert "title" in result
        assert "snippet" in result
        assert "score" in result

    def test_search_empty_query(self, client):
        r = client.post(
            "/api/search",
            json={"query": "   ", "top_k": 3},
        )
        assert r.status_code == 422

    def test_search_no_results(self, client):
        r = client.post(
            "/api/search",
            json={"query": "量子芯片制造工艺详解手册指南", "top_k": 3},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # The database only contains English articles, so a Chinese query
        # about quantum chips should return no results.
        assert len(data["results"]) == 0

    def test_search_top_k_clamped(self, client):
        r = client.post(
            "/api/search",
            json={"query": "spring", "top_k": 100},
        )
        assert r.status_code == 422  # top_k max is 5


# ---------------------------------------------------------------------------
# Streaming search
# ---------------------------------------------------------------------------


class TestStreamingSearch:
    @pytest.fixture(autouse=True)
    def _seed(self, client):
        client.post(
            "/api/articles",
            json={
                "title": "Stream Test",
                "content": "The stream flows gently through the valley, carrying leaves and petals along its path toward the distant sea.",
            },
        )

    def test_stream_search_returns_text(self, client):
        r = client.get(
            "/api/search/stream",
            params={"query": "flowing stream", "top_k": 3},
        )
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")
        content = r.text
        assert len(content) > 0

    def test_stream_search_empty_query(self, client):
        r = client.get(
            "/api/search/stream",
            params={"query": "   ", "top_k": 3},
        )
        assert r.status_code >= 400
