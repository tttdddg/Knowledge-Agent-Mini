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

Then open http://127.0.0.1:8000/docs for the interactive API documentation.

## API Endpoints

| Method | Path            | Description       |
| ------ | --------------- | ----------------- |
| GET    | `/api/health`   | Health check      |
| POST   | `/api/articles` | Create an article |
| GET    | `/api/articles` | List articles     |

## Project Status

This project is under active development. See `DEVELOPMENT.md` for details.
