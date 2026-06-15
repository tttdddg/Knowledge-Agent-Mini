# Knowledge Agent Mini

A lightweight knowledge-base system supporting article storage, semantic search,
streaming responses, and MCP Agent tool calling.

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment configuration
copy .env.example .env    # Windows
# cp .env.example .env    # macOS / Linux

# 4. Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 for the Web UI, or http://127.0.0.1:8000/docs for the
interactive API documentation.

## API Endpoints

| Method | Path                     | Description            |
| ------ | ------------------------ | ---------------------- |
| GET    | `/api/health`            | Health check           |
| POST   | `/api/articles`          | Create an article      |
| POST   | `/api/articles/upload`   | Upload a TXT file      |
| GET    | `/api/articles`          | List articles (paged)  |
| POST   | `/api/search`            | Semantic search (JSON) |
| GET    | `/api/search/stream`     | Streaming search       |

## MCP Configuration

The project includes an MCP server that exposes semantic search to Claude Code.

### Setup

1. Make sure the FastAPI backend is running (see Quick Start above).
2. Copy the example MCP config:

```bash
copy .mcp.json.example .mcp.json    # Windows
# cp .mcp.json.example .mcp.json    # macOS / Linux
```

3. Launch Claude Code from the project root:

```bash
claude
```

4. Verify the MCP connection:

```
/mcp
```

You should see:

```
knowledge-search
  search_knowledge
  Connected
```

### Test Prompts

**Should call the tool:**

- "帮我查询知识库中与春天有关的内容，并告诉我来源。"
- "知识库里是否有少年闰土相关内容？"
- "请从本地知识库查找描写父爱的文章。"

**Should NOT call the tool:**

- "你好。"
- "解释一下 Python 列表推导式。"

**No-result test:**

- "查询知识库中关于量子芯片制造工艺的内容。"

Agent should respond that no relevant content was found.

### MCP Logs

Tool call records are written to `logs/mcp_calls.log`:

```
2026-06-15 14:32:18 query="春天" top_k=3 request_id=92e7c4d1 result_count=1 duration_ms=214 success=true
```

## Project Status

Under active development. Core features:

- [x] Article entry (JSON + TXT upload)
- [x] Text chunking & embedding
- [x] Top-K semantic search with dedup
- [x] Streaming response (backend-driven)
- [x] MCP Server for Claude Code
- [ ] Tests & smoke scripts
- [ ] Final documentation & screenshots
