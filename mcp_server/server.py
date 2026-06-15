"""
Knowledge Agent Mini — MCP Server.

Exposes the ``search_knowledge`` tool via stdio transport so that Claude Code
can call the knowledge-base search API autonomously.

Start the FastAPI backend first, then configure Claude Code to launch this
server (see ``.mcp.json.example``).

Logging
-------
All diagnostic output goes to **stderr** (never stdout, which would corrupt
the MCP stdio protocol).  Call records are also written to
``logs/mcp_calls.log`` for auditability.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE: str = os.getenv("KNOWLEDGE_API_BASE", "http://127.0.0.1:8000")
TIMEOUT: float = float(os.getenv("MCP_REQUEST_TIMEOUT", "10"))

# Resolve the project root so log paths work regardless of CWD.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging (stderr + file)
# ---------------------------------------------------------------------------

logger = logging.getLogger("mcp.knowledge-search")
logger.setLevel(logging.INFO)

# stderr handler — safe for MCP stdio
_stderr_handler = logging.StreamHandler(sys.stderr)
_stderr_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s")
)
logger.addHandler(_stderr_handler)

# File handler — persistent call log
_file_handler = logging.FileHandler(
    str(_LOG_DIR / "mcp_calls.log"), encoding="utf-8"
)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
# Use a dedicated logger for call records (no level prefix).
call_logger = logging.getLogger("mcp.calls")
call_logger.setLevel(logging.INFO)
call_logger.addHandler(_file_handler)
call_logger.propagate = False  # don't duplicate to stderr

# ---------------------------------------------------------------------------
# FastMCP application
# ---------------------------------------------------------------------------

mcp = FastMCP("knowledge-search")


@mcp.tool()
async def search_knowledge(
    query: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    查询本地知识库中的相关内容。

    当用户要求查询、检索、查找或了解知识库中的内容时使用此工具。
    普通闲聊、代码解释和与知识库无关的问题不要调用此工具。

    Args:
        query: 用户希望查询的自然语言问题或关键词。
        top_k: 最多返回的结果数量，范围为 1 到 5。
    """
    started_at = time.monotonic()
    request_id: str = ""
    result_count: int = 0
    success: bool = False

    # ---- validate query ----------------------------------------------------
    query = query.strip()
    if not query:
        logger.warning("Empty query received — rejecting.")
        return {
            "success": False,
            "error_code": "EMPTY_QUERY",
            "message": "查询内容不能为空",
            "results": [],
        }

    top_k = max(1, min(top_k, 5))

    # ---- call FastAPI -------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE}/api/search",
                json={"query": query, "top_k": top_k},
            )
            response.raise_for_status()
            body = response.json()
            request_id = body.get("request_id", "")
            result_count = len(body.get("results", []))
            success = True
            return body

    except httpx.ConnectError:
        logger.error("Cannot connect to knowledge API at %s", API_BASE)
        return {
            "success": False,
            "error_code": "SERVICE_UNAVAILABLE",
            "message": "知识库服务未启动或无法连接。请先启动 FastAPI 后端。",
            "results": [],
        }

    except httpx.TimeoutException:
        logger.error("Request to knowledge API timed out after %.0fs", TIMEOUT)
        return {
            "success": False,
            "error_code": "SEARCH_TIMEOUT",
            "message": f"知识库查询超时（{TIMEOUT}s），请稍后重试。",
            "results": [],
        }

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Knowledge API returned error status %d", exc.response.status_code
        )
        return {
            "success": False,
            "error_code": "BACKEND_ERROR",
            "message": f"知识库服务返回错误：HTTP {exc.response.status_code}",
            "results": [],
        }

    except Exception:
        logger.exception("Unexpected MCP tool error")
        return {
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "知识库工具执行失败",
            "results": [],
        }

    finally:
        duration_ms = round((time.monotonic() - started_at) * 1000)
        call_logger.info(
            'query="%s" top_k=%d request_id=%s result_count=%d duration_ms=%d success=%s',
            query,
            top_k,
            request_id,
            result_count,
            duration_ms,
            str(success).lower(),
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
