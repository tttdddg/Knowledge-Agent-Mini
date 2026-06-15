# Knowledge Agent Mini — 启动和使用指南

本文档从零开始，逐步完成环境搭建、服务启动、知识录入、语义查询和 MCP Agent 接入。

---

## 目录

1. [环境准备](#1-环境准备)
2. [安装依赖](#2-安装依赖)
3. [配置环境变量](#3-配置环境变量)
4. [启动服务](#4-启动服务)
5. [初始化示例数据](#5-初始化示例数据)
6. [Web 界面使用](#6-web-界面使用)
7. [API 调用示例](#7-api-调用示例)
8. [MCP Agent 接入](#8-mcp-agent-接入)
9. [运行测试](#9-运行测试)
10. [常见问题](#10-常见问题)

---

## 1. 环境准备

### 前提条件

- Python 3.11 或更高版本
- 能够访问 Hugging Face 或 hf-mirror.com（用于下载 Embedding 模型）
- Windows / macOS / Linux

### 创建虚拟环境

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

激活成功后，终端提示符前会出现 `(.venv)` 标记。

---

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

核心依赖包括：

| 包                   | 用途                     |
| --------------------- | ------------------------ |
| fastapi + uvicorn     | Web 框架和 ASGI 服务器   |
| pydantic              | 请求参数校验             |
| sentence-transformers | Embedding 模型加载与推理 |
| numpy                 | 向量相似度计算           |
| httpx                 | MCP Server 调用后端 API  |
| mcp                   | MCP Server 框架          |
| pytest                | 测试框架                 |

首次安装约需 2–3 分钟，包含 PyTorch 和模型依赖。

---

## 3. 配置环境变量

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
```

**.env 文件内容及说明：**

```env
# -- 服务配置 --
APP_NAME=Knowledge Agent Mini
APP_HOST=127.0.0.1
APP_PORT=8000

# -- 数据库路径 --
DATABASE_PATH=./data/knowledge.db

# -- Embedding 模型 --
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
HF_ENDPOINT=https://huggingface.co        # 如无法访问，改为 https://hf-mirror.com
CHUNK_SIZE=300
CHUNK_OVERLAP=50

# -- 搜索默认值 --
DEFAULT_TOP_K=3
MAX_TOP_K=5
SIMILARITY_THRESHOLD=0.35

# -- 上传限制 --
MAX_TEXT_LENGTH=50000
MAX_FILE_SIZE=1048576                       # 1 MB

# -- MCP 连接 --
KNOWLEDGE_API_BASE=http://127.0.0.1:8000
MCP_REQUEST_TIMEOUT=10
```

> **注意**：如果 Hugging Face 不可访问，将 `HF_ENDPOINT` 改为 `https://hf-mirror.com`。

---

## 4. 启动服务

### 方式一：命令行启动

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 方式二：Windows 一键启动

双击 `start.bat`。

### 验证启动成功

浏览器访问：http://127.0.0.1:8000

看到 Web 界面即表示启动成功。

或者访问 API 文档：http://127.0.0.1:8000/docs

### 启动日志

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 5. 初始化示例数据

新开一个终端，激活虚拟环境后执行：

```bash
python scripts/init_demo_data.py
```

此脚本读取 `sample_data/` 目录下的四篇中文文章并自动导入：

| 文件               | 标题       | 作者   | 字数 |
| ------------------ | ---------- | ------ | ---- |
| 春.txt             | 春         | 朱自清 | ~700 |
| 故乡.txt           | 故乡       | 鲁迅   | ~900 |
| 背影.txt           | 背影       | 朱自清 | ~950 |
| 济南的冬天.txt     | 济南的冬天 | 老舍   | ~650 |

执行输出示例：

```
Found 4 TXT file(s) in sample_data/
Connected to http://127.0.0.1:8000 — status: ok
  [OK]  '背影' → 4 chunks
  [OK]  '春' → 3 chunks
  [OK]  '故乡' → 3 chunks
  [OK]  '济南的冬天' → 3 chunks

Done.  success=4  skipped=0  failed=0
```

> 脚本可重复执行，已导入的文章会自动跳过。

---

## 6. Web 界面使用

### 6.1 界面布局

```
┌──────────────────────────────────────────────────┐
│  Knowledge Agent Mini             服务状态：正常   │
├─────────────────────┬────────────────────────────┤
│ 知识录入             │ 知识查询                    │
│                     │                            │
│ [标题输入框]         │ [查询输入框] [查询]         │
│ [正文文本框]         │ 返回数量: [3 ▼]            │
│ [保存文章]           │                            │
│                     │ ┌────────────────────────┐ │
│ 上传 TXT 文件        │ │ 查询结果（逐字显示）    │ │
│ [选择文件] [上传]    │ │                        │ │
│                     │ └────────────────────────┘ │
├─────────────────────┤                            │
│ 文章列表             │                            │
│ 标题 │ 来源 │ 时间   │                            │
│ 春   │ 春.txt│06-15 │                            │
│ [上一页] 第1/1页    │                            │
└─────────────────────┴────────────────────────────┘
```

### 6.2 录入文章

**直接输入：**

1. 在「文章标题」输入框填写标题（1–100 字）
2. 在「文章正文」文本框粘贴或输入正文（最少 10 字）
3. 点击「保存文章」
4. 状态显示「保存成功！已切分为 N 个片段」

**上传 TXT 文件：**

1. 点击「选择文件」，选择 `.txt` 文件
2. 可选填写标题（留空则使用文件名）
3. 点击「上传」
4. 状态显示上传结果

支持编码：UTF-8、UTF-8 BOM、GB18030。上传其他格式文件会提示「仅支持上传 .txt 文件」。

### 6.3 查看文章列表

文章列表自动刷新，显示：
- 标题
- 来源（文件名或 text）
- 分块数量
- 创建时间

支持分页浏览，每页 5 条。

### 6.4 语义查询

1. 在「知识查询」输入框输入自然语言查询
2. 选择返回数量（1–5）
3. 点击「查询」或按 Enter
4. 结果文字逐字显示（后端流式输出）

**示例查询：**

| 查询         | 期望结果         |
| ------------ | ---------------- |
| 春天         | 《春》中的段落   |
| 少年闰土     | 《故乡》中的段落 |
| 父亲的背影   | 《背影》中的段落 |
| 冬天的小雪   | 《济南的冬天》   |

### 6.5 交互状态说明

| 状态       | 表现                         |
| ---------- | ---------------------------- |
| 保存中     | 按钮禁用 + "保存中…"         |
| 上传中     | 按钮禁用 + "上传中…"         |
| 查询中     | 按钮禁用 + 结果显示区高亮    |
| 成功       | 绿色状态文字                 |
| 参数错误   | 红色状态文字 + 具体错误信息  |
| 服务不可用 | 页面顶部状态栏变红           |

---

## 7. API 调用示例

### 7.1 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

响应：

```json
{
  "status": "ok",
  "database": "ok",
  "model_loaded": true,
  "article_count": 4
}
```

### 7.2 新增文章

```bash
curl -X POST http://127.0.0.1:8000/api/articles \
  -H "Content-Type: application/json" \
  -d '{"title": "春", "content": "盼望着，盼望着，东风来了，春天的脚步近了……"}'
```

响应：

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "春",
    "chunk_count": 3
  }
}
```

### 7.3 上传 TXT 文件

```bash
curl -X POST http://127.0.0.1:8000/api/articles/upload \
  -F "file=@sample_data/春.txt" \
  -F "title=春"
```

### 7.4 分页查询

```bash
curl "http://127.0.0.1:8000/api/articles?page=1&page_size=5"
```

### 7.5 语义检索（JSON）

```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "春天", "top_k": 3}'
```

响应：

```json
{
  "success": true,
  "request_id": "92e7c4d1",
  "query": "春天",
  "results": [
    {
      "article_id": 1,
      "title": "春",
      "snippet": "盼望着，盼望着，东风来了，春天的脚步近了……",
      "source_name": "春.txt",
      "score": 0.8321
    }
  ],
  "message": "共找到 1 条相关内容"
}
```

### 7.6 流式检索

```bash
curl "http://127.0.0.1:8000/api/search/stream?query=春天&top_k=3"
```

响应（文本，逐步返回）：

```
找到 1 条相关内容。

【1】《春》
盼望着，盼望着，东风来了，春天的脚步近了……
来源：春.txt
相关度：83.21%
```

---

## 8. MCP Agent 接入

### 8.1 复制 MCP 配置

```bash
copy .mcp.json.example .mcp.json
```

### 8.2 检查当前 MCP 配置

```bash
claude mcp list
```

### 8.3 在 Claude Code 中验证

启动 Claude Code 后输入：

```
/mcp
```

应显示：

```
knowledge-search — Connected
  search_knowledge(query, top_k)
```

### 8.4 测试 Agent 调用

**应调用工具的场景：**

```
帮我查询知识库中与春天有关的内容，并告诉我来源。
```

Agent 行为：判断需要查询知识库 → 调用 search_knowledge → 获取带来源的结果 → 回答用户。

**不应调用工具的场景：**

```
你好，请简单介绍一下你自己。
```

Agent 行为：直接回答，不调用知识库工具。

### 8.5 查看调用日志

```bash
type logs\mcp_calls.log       # Windows
# cat logs/mcp_calls.log      # macOS / Linux
```

日志格式：

```
2026-06-15 14:32:18 query="春天" top_k=3 request_id=92e7c4d1 result_count=1 duration_ms=214 success=true
```

### 8.6 后端未启动时的表现

如果 FastAPI 未启动，Claude Code 中调用工具会收到：

```json
{
  "success": false,
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "知识库服务未启动或无法连接。请先启动 FastAPI 后端。",
  "results": []
}
```

Agent 会将此错误告知用户，建议先启动后端。

---

## 9. 运行测试

### 9.1 单元测试（文本切分）

```bash
pytest tests/test_chunk.py -v
```

覆盖：空文本、短文本、长文本、overlap、尾块合并、参数校验等 15 个用例。

### 9.2 API 集成测试

```bash
pytest tests/test_api.py -v
```

覆盖：健康检查、文章 CRUD、分页、语义检索、流式查询等 14 个用例。
使用独立临时数据库，不依赖运行中的服务。

### 9.3 冒烟测试

```bash
# 需要先启动服务
python scripts/smoke_test.py
```

覆盖：从健康检查到流式查询的 7 个端到端场景。

### 9.4 一键运行全部

```bash
pytest tests/ -v && python scripts/smoke_test.py
```

预期输出：

```
tests/test_chunk.py::TestCleanText::test_strip_whitespace PASSED
...
tests/test_api.py::TestStreamingSearch::test_stream_search_returns_text PASSED
======================= 29 passed =======================

[PASS] API health
[PASS] Create article
[PASS] Article pagination
[PASS] Semantic search
[PASS] Empty query validation
[PASS] No-result fallback
[PASS] Streaming search

All smoke tests passed.
```

---

## 10. 常见问题

### Q: 启动时报错 "No module named 'fastapi'"

虚拟环境未激活或依赖未安装。执行：

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### Q: 首次保存文章时长时间无响应

Embedding 模型正在下载（约 100 MB）。等待 1–2 分钟即可。
后续启动直接使用缓存，无需重新下载。

### Q: 模型下载失败 (getaddrinfo failed)

无法访问 huggingface.co。在 `.env` 中设置镜像：

```env
HF_ENDPOINT=https://hf-mirror.com
```

然后重启服务。

### Q: 中文 TXT 上传后乱码

确认文件编码为 UTF-8。系统也支持 GB18030，但 UTF-8 是最可靠的选择。
可以用记事本另存为 UTF-8 编码。

### Q: MCP Server 连接失败

1. 确认 FastAPI 后端正在运行：访问 http://127.0.0.1:8000/api/health
2. 确认 `.mcp.json` 配置正确
3. 确认虚拟环境已激活
4. 使用 `/mcp` 检查连接状态

### Q: 空查询返回了结果

Embedding 模型对某些随机文本也会产生 >0.35 的相似度分数。
这是模型特性，阈值（`SIMILARITY_THRESHOLD`）可在 `.env` 中调高。

### Q: 如何清空知识库

删除数据库文件即可：

```bash
del data\knowledge.db        # Windows
# rm data/knowledge.db       # macOS / Linux
```

重启服务后会自动创建空数据库。

### Q: 如何添加更多示例文章

将 `.txt` 文件放入 `sample_data/` 目录，然后重新运行：

```bash
python scripts/init_demo_data.py
```

已导入的文章会自动跳过，不会重复导入。
