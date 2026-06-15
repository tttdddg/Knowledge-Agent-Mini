# Knowledge Agent Mini：知识库与 Agent 检索系统开发文档

## 1. 项目定位

### 1.1 项目名称

**Knowledge Agent Mini**

副标题：

> 支持语义检索、流式返回与 MCP Agent 调用的轻量知识库系统

### 1.2 项目目标

在有限开发时间内完成一个：

- 体量小；
- 功能链路完整；
- Agent 能真实调用；
- 异常情况可控；
- 新环境五分钟左右可启动；
- 能证明 RAG、Tool Calling、流式交互和后端工程能力；

的知识库 Agent 项目。

完整业务链路如下：

```text
用户录入文章或上传 TXT
        ↓
文章保存到 SQLite
        ↓
文本切分为多个 Chunk
        ↓
Embedding 模型生成向量
        ↓
向量保存到 SQLite
        ↓
用户输入自然语言 query
        ↓
计算 query 与 Chunk 的语义相似度
        ↓
返回 Top-K 相关内容及来源
        ↓
后端以流式方式输出文字
        ↓
MCP Server 封装 search_knowledge 工具
        ↓
Claude Code 根据用户意图自主调用工具
```

### 1.3 核心验收场景

必须完整演示以下场景。

#### 场景一：知识录入

用户输入：

```text
标题：春

正文：
盼望着，盼望着，东风来了，春天的脚步近了……
```

系统完成：

1. 保存文章；
2. 自动切分文本；
3. 自动生成向量；
4. 文章出现在分页列表中。

#### 场景二：语义查询

用户查询：

```text
春天
```

系统返回：

```text
《春》
盼望着，盼望着，东风来了，春天的脚步近了……
来源：春.txt
相关度：0.83
```

#### 场景三：跨表达查询

知识库中存在《故乡》，用户查询：

```text
少年闰土
```

系统返回《故乡》中的相关段落。

#### 场景四：无答案拒答

用户查询：

```text
量子芯片制造方法
```

知识库中没有相关内容时，系统返回：

```text
知识库中未检索到足够相关的内容。
```

不得让系统编造答案。

#### 场景五：Agent 真实调用

用户在 Claude Code 中输入：

```text
帮我查询知识库中与春天有关的内容。
```

Claude Code 应：

1. 判断需要查询知识库；
2. 调用 `search_knowledge` MCP Tool；
3. 获取检索结果；
4. 根据工具结果回答用户。

#### 场景六：普通对话不调用工具

用户输入：

```text
你好，请简单介绍一下你自己。
```

Claude Code 应直接回答，不调用知识库工具。

------

# 2. 开发范围

## 2.1 必须实现

### 知识管理

- 直接输入文章标题和正文；
- 上传 `.txt` 文件；
- 自动切分文章；
- 自动生成并保存向量；
- 分页查看文章；
- 查看文章标题、来源和创建时间。

### 知识查询

- 输入自然语言 query；
- 语义相似度检索；
- 返回 Top-K 结果；
- 返回文章标题；
- 返回相关原文片段；
- 返回来源；
- 返回相似度；
- 无相关结果时拒绝编造。

### 流式交互

- 后端使用流式 HTTP 响应；
- 前端逐步读取响应内容；
- 页面中文字逐步出现；
- 查询期间显示加载状态；
- 查询失败时显示错误信息。

### Agent 接入

- 实现 Python MCP Server；
- 暴露 `search_knowledge` 工具；
- Claude Code 能连接 MCP Server；
- Agent 能根据用户意图自主调用；
- 工具调用过程有日志可查。

### 工程质量

- 参数校验；
- 文件类型校验；
- 文件大小校验；
- 空 query 处理；
- 知识库为空处理；
- 模型不可用处理；
- MCP 调用超时处理；
- 后端未启动处理；
- README 和启动说明；
- 示例数据；
- 最小测试脚本。

## 2.2 明确不做

本项目不得扩展以下内容：

- 登录注册；
- 用户权限；
- 多租户；
- 多知识库；
- PDF、Word、Excel 解析；
- 知识图谱；
- 多 Agent；
- 强化学习；
  -推荐算法；
- 对话历史；
- Redis；
- MySQL；
- Docker，除非全部核心功能提前完成；
- 接入大模型重新生成知识答案；
- 复杂后台管理；
- 图表和数据大屏；
- 同时实现 Skill 和 MCP。

------

# 3. 技术选型

## 3.1 后端

```text
Python 3.11
FastAPI
Uvicorn
SQLite
NumPy
sentence-transformers
```

选择理由：

- FastAPI 便于参数校验、接口开发和流式响应；
- SQLite 不需要安装额外数据库；
- NumPy 可直接完成小规模向量相似度计算；
- sentence-transformers 用于本地语义向量生成；
- 系统不依赖业务 API Key。

## 3.2 Embedding 模型

默认模型：

```text
BAAI/bge-small-zh-v1.5
```

环境变量：

```env
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

模型只负责生成向量，不参与回答生成。

首次运行时需要下载模型。模型下载完成后会进入本机缓存，后续启动直接复用。

## 3.3 向量存储

不引入 ChromaDB、Milvus 或 FAISS。

采用：

```text
SQLite BLOB + NumPy
```

方式保存和检索向量。

原因：

- 数据量只有少量测试文章；
- 避免安装和启动额外组件；
- 更容易在新环境运行；
- 可以完整展示文本切分、向量生成和余弦相似度检索；
- 后续可以通过统一接口替换成 ChromaDB。

## 3.4 前端

采用：

```text
HTML
CSS
原生 JavaScript
```

前端由 FastAPI 直接托管，不再创建独立 Node.js 工程。

原因：

- 只需要启动一个 Web 服务；
- 减少 npm 安装和前后端联调问题；
- 把时间投入 RAG 和 MCP 核心能力；
- 保证评审快速运行。

## 3.5 Agent 接入

采用：

```text
Claude Code
Python MCP SDK
FastMCP
stdio transport
```

MCP Tool 通过 HTTP 请求调用知识库后端，Web 查询和 Agent 查询复用同一套检索逻辑。

------

# 4. 系统架构

```text
┌──────────────────────────────────────┐
│             浏览器前端                │
│                                      │
│  文章录入  TXT上传  分页列表  查询框   │
│                  流式结果展示         │
└──────────────────┬───────────────────┘
                   │ HTTP
                   ▼
┌──────────────────────────────────────┐
│             FastAPI 后端              │
│                                      │
│  Article API                         │
│  Search API                          │
│  Streaming API                       │
│  参数校验与统一异常处理               │
└───────────────┬───────────┬──────────┘
                │           │
                ▼           ▼
       ┌──────────────┐  ┌──────────────┐
       │   SQLite     │  │ Embedding    │
       │ 文章与Chunk  │  │ 中文向量模型  │
       └──────────────┘  └──────────────┘

┌──────────────────────────────────────┐
│             Claude Code              │
│                                      │
│ 自主判断是否需要调用知识库工具         │
└──────────────────┬───────────────────┘
                   │ MCP stdio
                   ▼
┌──────────────────────────────────────┐
│        Knowledge MCP Server          │
│                                      │
│ search_knowledge(query, top_k)       │
└──────────────────┬───────────────────┘
                   │ HTTP
                   ▼
             FastAPI Search API
```

------

# 5. 项目目录

```text
knowledge-agent-mini/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── schemas.py
│   ├── exceptions.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chunk_service.py
│   │   ├── embedding_service.py
│   │   └── knowledge_service.py
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── mcp_server/
│   ├── __init__.py
│   └── server.py
├── sample_data/
│   ├── 春.txt
│   ├── 故乡.txt
│   ├── 背影.txt
│   └── 济南的冬天.txt
├── scripts/
│   ├── init_demo_data.py
│   └── smoke_test.py
├── tests/
│   ├── test_chunk.py
│   └── test_api.py
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── screenshots/
├── .env.example
├── .gitignore
├── .mcp.json.example
├── requirements.txt
├── README.md
├── DEVELOPMENT.md
└── start.bat
```

------

# 6. 数据库设计

## 6.1 articles 表

```sql
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_name TEXT,
    created_at TEXT NOT NULL
);
```

字段说明：

| 字段        | 说明         |
| ----------- | ------------ |
| id          | 文章主键     |
| title       | 文章标题     |
| content     | 完整正文     |
| source_type | text 或 file |
| source_name | 原文件名     |
| created_at  | 创建时间     |

## 6.2 chunks 表

```sql
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

建立索引：

```sql
CREATE INDEX IF NOT EXISTS idx_chunks_article_id
ON chunks(article_id);

CREATE INDEX IF NOT EXISTS idx_articles_created_at
ON articles(created_at);
```

Embedding 保存方式：

```python
vector.astype("float32").tobytes()
```

读取方式：

```python
np.frombuffer(blob, dtype=np.float32)
```

------

# 7. 配置设计

创建 `.env.example`：

```env
APP_NAME=Knowledge Agent Mini
APP_HOST=127.0.0.1
APP_PORT=8000

DATABASE_PATH=./data/knowledge.db

EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
CHUNK_SIZE=300
CHUNK_OVERLAP=50

DEFAULT_TOP_K=3
MAX_TOP_K=5
SIMILARITY_THRESHOLD=0.35

MAX_TEXT_LENGTH=50000
MAX_FILE_SIZE=1048576

KNOWLEDGE_API_BASE=http://127.0.0.1:8000
MCP_REQUEST_TIMEOUT=10
```

配置必须通过环境变量覆盖，代码内提供默认值。

------

# 8. 文本处理设计

## 8.1 文本清洗

处理步骤：

1. 删除首尾空白；
2. 统一 Windows 和 Unix 换行；
3. 连续三个以上空行压缩；
4. 保留中文标点；
5. 不删除正文中的必要换行。

## 8.2 文本切分

默认参数：

```text
chunk_size = 300 字符
chunk_overlap = 50 字符
```

基础实现：

```python
def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    text = text.strip()

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size].strip()

        if not chunk:
            continue

        if len(chunk) < 30 and chunks:
            chunks[-1] += chunk
        else:
            chunks.append(chunk)

    return chunks
```

约束：

- overlap 必须小于 chunk_size；
- 空正文不得生成 Chunk；
- 过短尾块合并到上一块；
- 每个 Chunk 保留文章 ID 和序号。

------

# 9. Embedding 服务

## 9.1 服务职责

`embedding_service.py` 负责：

- 延迟加载模型；
- 生成文章 Chunk 向量；
- 生成查询向量；
- 向量归一化；
- 模型加载失败处理。

## 9.2 延迟加载

模型不在模块导入时立即加载，防止 API 启动长时间阻塞。

```python
class EmbeddingService:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model
```

## 9.3 生成向量

```python
def encode(self, texts: list[str]) -> np.ndarray:
    model = self.get_model()

    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return np.asarray(vectors, dtype=np.float32)
```

由于向量已经归一化，查询时可以直接使用点积计算余弦相似度：

```python
scores = document_matrix @ query_vector
```

------

# 10. 知识入库流程

## 10.1 直接输入文章

流程：

```text
校验标题和正文
    ↓
保存 articles
    ↓
切分正文
    ↓
批量生成 Embedding
    ↓
保存 chunks 和 embedding
    ↓
返回文章信息和 Chunk 数量
```

必须使用数据库事务。

如果生成向量失败：

- 回滚文章写入；
- 不得出现只有文章、没有 Chunk 的不完整数据。

## 10.2 TXT 文件上传

要求：

- 只接受 `.txt`；
- 最大 1 MB；
- 标题为空时使用文件名；
- 尝试识别常见中文编码。

解码顺序：

```python
encodings = ["utf-8-sig", "utf-8", "gb18030"]
```

全部失败时返回：

```text
FILE_ENCODING_ERROR
无法识别文本文件编码，请转换为 UTF-8 后重新上传。
```

------

# 11. 搜索算法

## 11.1 搜索步骤

```text
校验 query
    ↓
检查知识库是否为空
    ↓
生成 query embedding
    ↓
读取全部 Chunk embedding
    ↓
计算余弦相似度
    ↓
按分数降序排序
    ↓
过滤低于阈值的结果
    ↓
按 article_id 去重
    ↓
返回 Top-K 文章
```

## 11.2 去重策略

一篇文章可能有多个相关 Chunk，但最终结果中同一文章只出现一次。

每篇文章保留相似度最高的 Chunk。

伪代码：

```python
best_by_article = {}

for result in sorted_results:
    article_id = result["article_id"]

    if article_id not in best_by_article:
        best_by_article[article_id] = result

results = list(best_by_article.values())[:top_k]
```

## 11.3 搜索返回结构

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

无相关结果：

```json
{
  "success": true,
  "request_id": "92e7c4d1",
  "query": "量子芯片制造方法",
  "results": [],
  "message": "知识库中未检索到足够相关的内容"
}
```

注意：

- 无结果不是服务异常；
- 无结果返回 HTTP 200；
- Agent 必须根据空数组明确拒答；
- 不得返回虚构内容。

------

# 12. API 设计

## 12.1 健康检查

```http
GET /api/health
```

响应：

```json
{
  "status": "ok",
  "database": "ok",
  "model_loaded": false,
  "article_count": 4
}
```

## 12.2 新增文章

```http
POST /api/articles
Content-Type: application/json
```

请求：

```json
{
  "title": "春",
  "content": "盼望着，盼望着，东风来了……"
}
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

## 12.3 上传 TXT

```http
POST /api/articles/upload
Content-Type: multipart/form-data
```

参数：

```text
file: TXT 文件
title: 可选标题
```

## 12.4 分页查询文章

```http
GET /api/articles?page=1&page_size=5
```

响应：

```json
{
  "success": true,
  "data": {
    "items": [],
    "page": 1,
    "page_size": 5,
    "total": 12,
    "total_pages": 3
  }
}
```

## 12.5 普通语义查询

```http
POST /api/search
Content-Type: application/json
```

请求：

```json
{
  "query": "春天",
  "top_k": 3
}
```

该接口同时供 MCP Server 调用。

## 12.6 流式查询

```http
GET /api/search/stream?query=春天&top_k=3
```

返回类型：

```text
text/plain; charset=utf-8
```

输出示例：

```text
正在检索知识库……

找到 1 条相关内容。

【1】《春》
盼望着，盼望着，东风来了，春天的脚步近了……
来源：春.txt
相关度：83.21%
```

后端先完成语义检索，再将格式化结果逐字符或逐短句发送。

实现示例：

```python
async def stream_text(text: str):
    for char in text:
        yield char
        await asyncio.sleep(0.015)

return StreamingResponse(
    stream_text(result_text),
    media_type="text/plain; charset=utf-8",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
)
```

------

# 13. 参数校验

## 13.1 标题

```text
最短：1 字符
最长：100 字符
```

## 13.2 正文

```text
最短：10 字符
最长：50000 字符
```

## 13.3 query

```text
去除首尾空格后不得为空
最大长度：500 字符
```

## 13.4 top_k

```text
最小：1
最大：5
默认：3
```

## 13.5 文件

```text
扩展名：.txt
最大大小：1 MB
```

------

# 14. 异常处理

## 14.1 统一错误结构

```json
{
  "success": false,
  "error": {
    "code": "EMPTY_QUERY",
    "message": "查询内容不能为空",
    "details": null
  }
}
```

## 14.2 错误码

| 错误码               | HTTP 状态 | 说明                   |
| -------------------- | --------- | ---------------------- |
| EMPTY_QUERY          | 400       | query 为空             |
| INVALID_TITLE        | 400       | 标题不合法             |
| INVALID_CONTENT      | 400       | 正文不合法             |
| INVALID_FILE_TYPE    | 400       | 上传的不是 TXT         |
| FILE_TOO_LARGE       | 413       | 文件超过限制           |
| FILE_ENCODING_ERROR  | 400       | 文件解码失败           |
| KNOWLEDGE_BASE_EMPTY | 409       | 知识库为空             |
| MODEL_UNAVAILABLE    | 503       | Embedding 模型不可用   |
| DATABASE_ERROR       | 500       | 数据库异常             |
| SERVICE_UNAVAILABLE  | 503       | MCP 无法连接知识库服务 |
| SEARCH_TIMEOUT       | 504       | 查询超时               |
| INTERNAL_ERROR       | 500       | 未知异常               |

## 14.3 无答案与异常的区别

以下情况不是异常：

```text
查询执行成功，但没有内容超过相似度阈值。
```

应该返回：

```json
{
  "success": true,
  "results": [],
  "message": "知识库中未检索到足够相关的内容"
}
```

------

# 15. 前端页面设计

## 15.1 页面结构

```text
┌────────────────────────────────────────────┐
│ Knowledge Agent Mini       服务状态：正常   │
├───────────────────┬────────────────────────┤
│ 知识录入           │ 知识查询                │
│                   │                        │
│ 标题输入框         │ query 输入框            │
│ 正文输入框         │ 查询按钮                │
│ 保存按钮           │                        │
│ TXT 上传           │ 流式结果区域            │
│                   │                        │
├───────────────────┤                        │
│ 文章列表           │                        │
│ 标题 / 来源 / 时间 │                        │
│ 上一页 / 下一页    │                        │
└───────────────────┴────────────────────────┘
```

## 15.2 必须具备的交互状态

- 保存中；
- 上传中；
- 查询中；
- 查询按钮禁用；
- 成功提示；
- 参数错误提示；
- 服务不可用提示；
- 流式文字展示；
- 上一页、下一页禁用状态；
- 空列表状态。

## 15.3 查询前端逻辑

使用 `fetch` 读取流：

```javascript
const response = await fetch(
  `/api/search/stream?query=${encodeURIComponent(query)}&top_k=3`
);

if (!response.ok) {
  throw new Error("查询失败");
}

const reader = response.body.getReader();
const decoder = new TextDecoder("utf-8");

while (true) {
  const { value, done } = await reader.read();

  if (done) break;

  resultText += decoder.decode(value, { stream: true });
  resultElement.textContent = resultText;
}
```

不得一次性等待完整响应后，再使用前端定时器伪造流式效果。

------

# 16. MCP Server 设计

## 16.1 MCP 工具

工具名称：

```text
search_knowledge
```

工具功能：

```text
根据自然语言 query 查询本地知识库，并返回最相关的原文、来源和相关度。
```

参数：

```text
query: str
top_k: int = 3
```

工具描述必须告诉 Agent 什么时候使用：

```text
当用户要求查询、检索、查找或了解本地知识库中的内容时使用此工具。
普通闲聊、代码解释和与知识库无关的问题不要调用此工具。
```

## 16.2 MCP Server 核心实现

```python
import os
import sys
import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("knowledge-search")

API_BASE = os.getenv(
    "KNOWLEDGE_API_BASE",
    "http://127.0.0.1:8000"
)

TIMEOUT = float(os.getenv("MCP_REQUEST_TIMEOUT", "10"))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(message)s"
)


@mcp.tool()
async def search_knowledge(
    query: str,
    top_k: int = 3
) -> dict[str, Any]:
    """
    查询本地知识库中的相关内容。

    当用户要求查询、检索、查找或了解知识库中的内容时使用。
    普通闲聊或与知识库无关的问题不要调用。

    Args:
        query: 用户希望查询的自然语言问题或关键词。
        top_k: 最多返回的结果数量，范围为 1 到 5。
    """

    query = query.strip()

    if not query:
        return {
            "success": False,
            "error_code": "EMPTY_QUERY",
            "message": "查询内容不能为空",
            "results": []
        }

    top_k = max(1, min(top_k, 5))

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE}/api/search",
                json={
                    "query": query,
                    "top_k": top_k
                }
            )

            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        return {
            "success": False,
            "error_code": "SERVICE_UNAVAILABLE",
            "message": "知识库服务未启动或无法连接",
            "results": []
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error_code": "SEARCH_TIMEOUT",
            "message": "知识库查询超时",
            "results": []
        }

    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "error_code": "BACKEND_ERROR",
            "message": f"知识库服务返回错误：{exc.response.status_code}",
            "results": []
        }

    except Exception:
        logging.exception("MCP tool execution failed")

        return {
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "知识库工具执行失败",
            "results": []
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## 16.3 MCP 日志要求

stdio MCP Server 不得使用普通 `print()` 输出日志。

所有日志必须：

- 写入 stderr；
- 或写入日志文件。

增加文件日志：

```text
logs/mcp_calls.log
```

每次调用记录：

```text
时间
query
top_k
request_id
结果数量
耗时
是否成功
```

示例：

```text
2026-06-15 14:32:18 query="春天" top_k=3 request_id=92e7c4d1 result_count=1 duration_ms=214 success=true
```

该日志可用于证明 Agent 确实调用了 MCP Tool。

------

# 17. Claude Code 接入

## 17.1 项目级配置示例

创建 `.mcp.json.example`：

```json
{
  "mcpServers": {
    "knowledge-search": {
      "type": "stdio",
      "command": "python",
      "args": [
        "mcp_server/server.py"
      ],
      "env": {
        "KNOWLEDGE_API_BASE": "http://127.0.0.1:8000",
        "MCP_REQUEST_TIMEOUT": "10"
      }
    }
  }
}
```

使用前：

1. 激活 Python 虚拟环境；
2. 启动 FastAPI；
3. 从项目根目录启动 Claude Code；
4. 检查 MCP Server 状态。

也可以通过命令添加：

```bash
claude mcp add --scope project --transport stdio knowledge-search -- python mcp_server/server.py
```

检查：

```bash
claude mcp list
```

进入 Claude Code 后执行：

```text
/mcp
```

应看到：

```text
knowledge-search
search_knowledge
Connected
```

## 17.2 Agent 测试提示词

### 应调用工具

```text
帮我查询知识库中与春天有关的内容，并告诉我来源。
知识库里是否有少年闰土相关内容？
请从本地知识库查找描写父爱的文章。
```

### 不应调用工具

```text
你好。
解释一下 Python 列表推导式。
帮我给变量起一个名字。
```

### 无结果测试

```text
查询知识库中关于量子芯片制造工艺的内容。
```

期望：

```text
Agent 调用工具后发现 results 为空，并明确说明知识库中没有足够相关内容。
```

------

# 18. 日志与可观测性

## 18.1 API 日志

保存到：

```text
logs/app.log
```

搜索日志格式：

```text
timestamp
request_id
query
top_k
threshold
result_count
duration_ms
```

## 18.2 MCP 日志

保存到：

```text
logs/mcp_calls.log
```

## 18.3 request_id

每次搜索生成：

```python
request_id = uuid.uuid4().hex[:8]
```

request_id 同时出现在：

- API 响应；
- API 日志；
- MCP 返回；
- MCP 日志。

这样可以证明：

```text
Claude Code 工具调用
→ MCP Server
→ FastAPI
→ 检索结果
```

属于同一次真实请求。

------

# 19. 示例数据

至少准备四篇文章：

```text
春.txt
故乡.txt
背影.txt
济南的冬天.txt
```

每篇约 300～1000 字，不要放入过大的完整作品。

初始化脚本：

```bash
python scripts/init_demo_data.py
```

要求：

- 自动读取 `sample_data` 下所有 TXT；
- 文件名作为标题；
- 已存在同名文章时跳过；
- 输出成功、跳过和失败数量；
- 任何单篇失败不影响其他文件继续导入。

------

# 20. 测试要求

## 20.1 单元测试

### 文本切分

测试：

- 空字符串；
- 短文本；
- 长文本；
- overlap；
- 末尾短 Chunk 合并。

### 参数校验

测试：

- 空标题；
- 空正文；
- 空 query；
- top_k 超出范围；
- 非 TXT 文件；
- 超大文件。

## 20.2 API 测试

至少覆盖：

```text
GET /api/health
POST /api/articles
GET /api/articles
POST /api/search
GET /api/search/stream
```

## 20.3 冒烟测试

`scripts/smoke_test.py` 完成：

1. 检查健康接口；
2. 新增测试文章；
3. 查询文章分页；
4. 搜索“春天”；
5. 验证存在结果；
6. 搜索无关问题；
7. 验证系统不崩溃。

执行：

```bash
python scripts/smoke_test.py
```

成功输出：

```text
[PASS] API health
[PASS] Create article
[PASS] Article pagination
[PASS] Semantic search
[PASS] Empty query validation
[PASS] No-result fallback

All smoke tests passed.
```

------

# 21. 安装与启动

## 21.1 创建虚拟环境

Windows：

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS 或 Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 21.2 安装依赖

`requirements.txt`：

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-multipart
numpy
sentence-transformers
httpx
mcp[cli]>=1.2.0
pytest
```

安装：

```bash
pip install -r requirements.txt
```

开发完成并验证成功后生成锁定版本：

```bash
pip freeze > requirements-lock.txt
```

## 21.3 初始化示例知识

```bash
python scripts/init_demo_data.py
```

## 21.4 启动 Web 服务

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 21.5 启动 Claude Code

保持 FastAPI 运行，在项目根目录打开另一个终端：

```bash
.venv\Scripts\activate
claude
```

然后输入：

```text
/mcp
```

确认工具连接成功。

------

# 22. Windows 一键启动脚本

创建 `start.bat`：

```bat
@echo off
setlocal

if not exist .venv (
    echo [ERROR] Virtual environment not found.
    echo Please run: python -m venv .venv
    exit /b 1
)

call .venv\Scripts\activate

if not exist data (
    mkdir data
)

if not exist logs (
    mkdir logs
)

echo Starting Knowledge Agent Mini...
echo Open http://127.0.0.1:8000

uvicorn app.main:app --host 127.0.0.1 --port 8000
```

不得在启动脚本中自动执行耗时且不可控的依赖安装。

------

# 23. README 必须包含的内容

README 按以下顺序编写：

## 23.1 项目简介

用一段话说明：

```text
这是一个支持文章录入、TXT 上传、语义检索、流式返回和 MCP Agent 调用的轻量知识库系统。
```

## 23.2 已完成功能

用勾选列表展示：

```text
[x] 文章直接录入
[x] TXT 上传
[x] 分页查询
[x] 文本切分
[x] Embedding 向量化
[x] Top-K 语义检索
[x] 来源和相似度展示
[x] 无答案拒答
[x] 后端流式响应
[x] MCP Tool
[x] Claude Code Agent 调用
[x] 参数校验与异常处理
```

## 23.3 系统架构

放入简洁架构图。

## 23.4 快速启动

确保所有命令可以直接复制。

## 23.5 MCP 配置

包含：

- MCP 配置文件；
- 添加命令；
- `/mcp` 检查方式；
- 测试提示词。

## 23.6 演示截图

至少包括：

1. 知识录入页面；
2. 分页文章列表；
3. 流式查询结果；
4. Claude Code MCP 已连接；
5. Agent 调用 `search_knowledge`；
6. 无答案拒答；
7. MCP 调用日志。

## 23.7 设计取舍

写明：

```text
本项目面向小规模笔试场景，采用 SQLite 保存文章和向量，并通过 NumPy 完成余弦相似度检索。该方案避免依赖额外向量数据库，降低部署成本，同时保留向量存储抽象，后续可以替换为 ChromaDB、FAISS 或 Milvus。
```

## 23.8 项目来源说明

如实写：

```text
本项目根据笔试要求独立实现，核心能力包括文本切分、Embedding、语义检索、流式响应以及 MCP Agent 工具接入。项目实现过程使用 AI 编程工具辅助代码生成、审查和测试，但系统设计、功能验收与最终交付由本人完成。
```

------

# 24. 开发顺序与时间安排

## 10:30—10:50：项目初始化

完成：

- 创建目录；
- 创建虚拟环境；
- 安装依赖；
- 建立 FastAPI；
- 建立 SQLite；
- `/api/health` 可访问。

验收：

```text
浏览器能够打开页面；
/api/health 返回 status=ok。
```

## 10:50—12:00：知识入库

完成：

- 数据库表；
- 文章新增；
- TXT 上传；
- 文本切分；
- Embedding；
- 向量保存；
- 分页列表。

验收：

```text
能够录入《春》和《故乡》；
数据库中存在文章和 Chunk；
列表可以翻页。
```

## 12:00—13:00：语义检索

完成：

- query 向量；
- 相似度计算；
- Top-K；
- 阈值；
- 按文章去重；
- 来源和分数。

验收：

```text
春天 → 春
少年闰土 → 故乡
无关查询 → 空结果
```

## 13:00—13:45：前端与流式输出

完成：

- 录入表单；
- 文件上传；
- 分页列表；
- 查询框；
- 流式结果；
- 加载和错误状态。

验收：

```text
文字由后端逐步返回并在页面逐步出现。
```

## 13:45—15:00：MCP Server

完成：

- FastMCP；
- search_knowledge；
- HTTP 调用后端；
- 参数校验；
- 超时和服务不可用；
- Claude Code 配置。

验收：

```text
Claude Code 能看到 search_knowledge 工具；
Agent 能完成一次真实调用。
```

## 15:00—15:40：Agent 验证

完成测试：

- 应调用工具；
- 不应调用工具；
- 无结果；
- 空 query；
- 后端停止；
- 调用日志。

## 15:40—16:20：测试

完成：

- 核心单元测试；
- API 测试；
- 冒烟脚本；
- 修复关键问题。

## 16:20—17:00：README 和截图

完成：

- 架构说明；
- 快速启动；
- MCP 配置；
- 测试提示词；
- 七张关键截图。

## 17:00—17:25：干净环境验证

重新执行：

```text
创建环境
安装依赖
初始化数据
启动服务
打开页面
查询知识
连接 MCP
Agent 调用
```

检查是否存在：

- 绝对路径；
- 缺失文件；
- 未提交的配置；
- API Key；
- 中文乱码；
- 数据库路径错误；
- MCP stdout 日志污染。

## 17:25—17:40：打包提交

17:40 前完成首次发送。

最后 20 分钟只用于处理：

- 邮件发送失败；
- 附件过大；
- 文件名错误；
- 压缩包损坏；
- 漏放简历。

------

# 25. Git 提交建议

建议保留四个清晰 Commit：

```text
feat: scaffold knowledge base API and SQLite storage
feat: add embedding retrieval and streaming search
feat: expose knowledge search through MCP tool
test: add smoke tests and complete run documentation
```

不要制造十几个没有实际意义的小 Commit，也不要最后只有一个“完成项目”的 Commit。

------

# 26. 最终验收清单

## 知识库

-  可以输入标题和正文；
-  可以上传 TXT；
-  上传后自动生成向量；
-  文章列表带分页；
-  中文文件不会乱码。

## 检索

-  使用 Embedding，而不是 SQL LIKE；
-  查询“春天”可以找到《春》；
-  查询“少年闰土”可以找到《故乡》；
-  返回标题、片段、来源和分数；
-  同一文章不会重复出现；
-  无结果时不会编造。

## 流式输出

-  后端使用 StreamingResponse；
-  前端读取 ReadableStream；
-  返回文字逐步出现；
-  中断或失败有提示。

## MCP

-  MCP Server 能启动；
-  Claude Code 显示 Connected；
-  能看到 search_knowledge；
-  Agent 能自主调用；
-  普通问题不调用；
-  后端停止时返回可读错误；
-  调用过程写入日志。

## 工程交付

-  requirements.txt 完整；
-  `.env.example` 完整；
-  README 命令可以复制；
-  示例数据齐全；
-  不包含个人 API Key；
-  不包含 `.venv`；
-  不包含大型模型文件；
-  简历已放入提交目录；
-  压缩包命名符合要求；
-  邮件主题符合要求。

------

# 27. 交给 Claude Code 的总开发提示词

```text
请严格按照项目根目录 DEVELOPMENT.md 开发 Knowledge Agent Mini。

目标不是扩展功能，而是完成一个体量小、链路完整、Agent 真调用、异常可控、五分钟可运行的笔试项目。

必须遵守以下规则：

1. 使用 Python 3.11、FastAPI、SQLite、NumPy 和 sentence-transformers。
2. 前端使用 FastAPI 托管的原生 HTML、CSS 和 JavaScript，不创建独立 Node 工程。
3. 支持直接录入文章、TXT 上传和分页列表。
4. 文章必须经过文本切分、Embedding 和向量持久化。
5. 搜索必须是真实语义检索，不能使用 SQL LIKE 代替。
6. 搜索返回标题、相关片段、来源和相似度。
7. 无相关结果时返回空结果并拒绝编造。
8. 使用 StreamingResponse 实现真实后端流式输出。
9. 实现 Python FastMCP stdio Server。
10. 只暴露一个 search_knowledge 工具。
11. MCP Tool 必须调用 FastAPI 的 /api/search 接口，不能复制另一套检索逻辑。
12. 处理空 query、知识库为空、文件错误、模型失败、服务不可用和超时。
13. MCP Server 不得向 stdout 输出日志，只能使用 stderr 或日志文件。
14. 不实现登录、权限、多知识库、多 Agent、PDF、Redis、MySQL、Docker、知识图谱或大模型答案生成。
15. 每完成一个阶段先运行测试，再进入下一阶段。
16. 不擅自修改 DEVELOPMENT.md 中确定的技术方案和目录。
17. 所有代码必须包含必要的类型标注、错误处理和简洁注释。
18. README 必须提供从创建环境到 Claude Code 调用 MCP 的完整命令。

请按以下阶段执行：

阶段一：建立项目目录、配置、数据库和健康接口。
阶段二：完成文章录入、TXT 上传、切分、向量化和分页。
阶段三：完成 Top-K 语义检索、阈值、来源和无答案兜底。
阶段四：完成前端页面和后端流式输出。
阶段五：完成 MCP Server 和 Claude Code 配置。
阶段六：完成测试、示例数据、日志、README 和启动脚本。

每个阶段完成后，输出：
- 已修改文件；
- 已实现功能；
- 执行的测试；
- 当前仍存在的问题；
- 下一阶段计划。

现在先完成阶段一，不要一次性生成所有未经测试的代码。
```

------

# 28. 最终交付标准

最终作品不以代码行数或页面复杂度评价，而以以下结果评价：

```text
评审打开 README
    ↓
五分钟左右启动系统
    ↓
导入或查看示例文章
    ↓
输入“春天”获得语义结果
    ↓
看到真实流式返回
    ↓
在 Claude Code 中提出知识查询
    ↓
Agent 自动调用 search_knowledge
    ↓
工具返回带来源的内容
    ↓
无答案和服务异常均有明确提示
```

只要这条链路稳定跑通，就已经完整证明了：

- FastAPI 后端开发；
- RAG 基础链路；
- 文本切分与 Embedding；
- Top-K 语义检索；
- 来源追溯；
- 无答案拒答；
- 流式消息展示；
- MCP Tool 开发；
- Agent Tool Calling；
- 参数校验；
- 异常兜底；
- 项目工程化交付能力。