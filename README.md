# Knowledge Agent Mini

> 支持语义检索、流式返回与 MCP Agent 调用的轻量知识库系统

## 项目简介

Knowledge Agent Mini 是一个体量小、链路完整的知识库系统。支持文章录入、TXT 上传、
文本自动切分、中文 Embedding 向量化、Top-K 语义检索、后端流式响应以及
Claude Code MCP Agent 工具调用。

完整业务链路：

```
用户录入文章或上传 TXT → 保存到 SQLite → 自动切分 → Embedding 向量化
→ 向量持久化 → 用户自然语言查询 → 语义相似度检索 → 返回 Top-K 结果
→ 后端流式输出文字 → MCP Server 封装工具 → Claude Code 自主调用
```

## 功能完成清单

- [x] 文章直接录入（JSON API + Web 表单）
- [x] TXT 文件上传（UTF-8 / UTF-8 BOM / GB18030 自动识别）
- [x] 文章分页查询（标题、来源、分块数、创建时间）
- [x] 文本清洗与滑动窗口切分（300 字符 / 50 重叠）
- [x] 中文 Embedding 向量化（BAAI/bge-small-zh-v1.5）
- [x] Top-K 语义检索（余弦相似度 + 阈值过滤 + 按文章去重）
- [x] 返回标题、原文片段、来源和相似度分数
- [x] 无答案拒答（知识库无相关内容时返回空结果，不编造）
- [x] 后端流式响应（StreamingResponse 逐字输出）
- [x] 前端 ReadableStream 流式接收（非前端动画模拟）
- [x] MCP Server（FastMCP stdio 传输）
- [x] Claude Code Agent 工具调用（search_knowledge）
- [x] MCP 调用日志（`logs/mcp_calls.log`）
- [x] 统一错误响应结构（12 种错误码）
- [x] 参数校验（标题、正文、query、top_k、文件类型、文件大小）
- [x] 36 个自动化测试（15 单元 + 14 API + 7 冒烟）

## 系统架构

```
┌──────────────────────────────────────────┐
│               浏览器前端                   │
│  文章录入 · TXT上传 · 分页列表 · 查询框    │
│             流式结果展示                   │
└──────────────────┬───────────────────────┘
                   │ HTTP
                   ▼
┌──────────────────────────────────────────┐
│              FastAPI 后端                  │
│  Article API · Search API · Stream API    │
│  参数校验 · 统一异常处理 · 静态文件托管     │
└───────────────┬───────────┬──────────────┘
                │           │
                ▼           ▼
       ┌──────────────┐  ┌──────────────────┐
       │   SQLite     │  │  Embedding 模型   │
       │ 文章 + Chunk │  │ BGE-small-zh-v1.5 │
       │ + 向量 BLOB  │  │  (L2 归一化)      │
       └──────────────┘  └──────────────────┘

┌──────────────────────────────────────────┐
│             Claude Code                   │
│  自主判断是否需要调用知识库工具            │
└──────────────────┬───────────────────────┘
                   │ MCP stdio
                   ▼
┌──────────────────────────────────────────┐
│         Knowledge MCP Server              │
│  search_knowledge(query, top_k)           │
│  HTTP → FastAPI /api/search               │
│  日志 → logs/mcp_calls.log               │
└──────────────────────────────────────────┘
```

## 技术选型

| 组件       | 技术                          | 理由                       |
| ---------- | ----------------------------- | -------------------------- |
| 后端框架   | FastAPI + Uvicorn             | 流式响应、参数校验、自动文档 |
| 数据库     | SQLite                        | 零安装、单文件、事务支持    |
| 向量存储   | SQLite BLOB + NumPy           | 无额外组件、规模可控        |
| Embedding  | sentence-transformers         | 本地运行、无需 API Key     |
| 模型       | BAAI/bge-small-zh-v1.5        | 中文优化、512 维、轻量     |
| 前端       | 原生 HTML / CSS / JavaScript  | 无 Node 工程、FastAPI 托管 |
| MCP        | FastMCP (Python MCP SDK)      | stdio 传输、工具注解       |

## 五分钟快速启动

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
```

如果 Hugging Face 不可访问，在 `.env` 中设置镜像：

```env
HF_ENDPOINT=https://hf-mirror.com
```

### 4. 启动服务

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

或双击运行 `start.bat`（Windows）。

### 5. 初始化示例数据

新开一个终端，激活虚拟环境后：

```bash
python scripts/init_demo_data.py
```

此命令读取 `sample_data/` 下的四篇中文文章（《春》《故乡》《背影》《济南的冬天》）
并自动导入。

### 6. 打开 Web 界面

浏览器访问：

```
http://127.0.0.1:8000
```

## Web 页面使用方法

### 知识录入

- **直接输入**：填写标题和正文，点击「保存文章」。系统自动切分并生成向量。
- **上传 TXT**：选择 `.txt` 文件，可选填写标题。支持 UTF-8 / GB18030 编码。
- **文章列表**：分页展示所有文章，显示标题、来源、分块数和创建时间。

### 知识查询

- 输入自然语言查询，点击「查询」或按 Enter。
- 结果文字通过后端流式逐步显示（非前端动画模拟）。
- 支持选择返回数量（1–5 条）。
- 查询期间按钮禁用，失败时显示错误信息。

## MCP 配置方法

### 1. 复制配置文件

```bash
copy .mcp.json.example .mcp.json     # Windows
# cp .mcp.json.example .mcp.json     # macOS / Linux
```

### 2. 启动 Claude Code

确保 FastAPI 后端正在运行，然后在项目根目录打开新终端：

```bash
.venv\Scripts\activate
claude
```

### 3. 检查 MCP 连接

在 Claude Code 中输入：

```
/mcp
```

应看到：

```
knowledge-search
  search_knowledge
  Connected
```

### 4. Claude Code 测试提示词

**应调用工具：**

- "帮我查询知识库中与春天有关的内容，并告诉我来源。"
- "知识库里是否有少年闰土相关内容？"
- "请从本地知识库查找描写父爱的文章。"

**不应调用工具：**

- "你好。"
- "解释一下 Python 列表推导式。"
- "帮我给变量起一个名字。"

**无结果测试：**

- "查询知识库中关于量子芯片制造工艺的内容。"

Agent 应调用工具后明确表示知识库中没有足够相关内容。

## 项目目录

```
knowledge-agent-mini/
├── app/                          # FastAPI 应用
│   ├── __init__.py
│   ├── main.py                   # 路由、异常处理、静态文件
│   ├── config.py                 # 环境变量配置
│   ├── database.py               # SQLite 初始化与连接
│   ├── schemas.py                # Pydantic 请求/响应模型
│   ├── exceptions.py             # 统一异常类与处理器
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chunk_service.py      # 文本清洗与切分
│   │   ├── embedding_service.py  # 模型延迟加载与向量生成
│   │   └── knowledge_service.py  # 知识入库与语义检索
│   └── static/
│       ├── index.html            # Web 前端页面
│       ├── app.js                # 前端逻辑与流式读取
│       └── style.css             # 样式
├── mcp_server/
│   ├── __init__.py
│   └── server.py                 # FastMCP stdio 服务
├── sample_data/                  # 示例数据（TXT 文件）
│   ├── 春.txt
│   ├── 故乡.txt
│   ├── 背影.txt
│   └── 济南的冬天.txt
├── scripts/
│   ├── init_demo_data.py         # 示例数据初始化脚本
│   └── smoke_test.py             # 冒烟测试脚本
├── tests/
│   ├── test_chunk.py             # 文本切分单元测试
│   └── test_api.py               # API 集成测试
├── data/                         # SQLite 数据库目录
├── logs/                         # 日志目录
├── screenshots/                  # 运行截图目录
├── .env.example                  # 环境变量示例
├── .gitignore
├── .mcp.json.example             # MCP 配置示例
├── requirements.txt              # 项目依赖
├── requirements-lock.txt         # 锁定版本依赖
├── start.bat                     # Windows 一键启动
└── README.md
```

## API 文档

启动服务后访问 http://127.0.0.1:8000/docs 查看交互式 Swagger 文档。

### 接口一览

| 方法   | 路径                       | 说明              |
| ------ | -------------------------- | ----------------- |
| GET    | `/api/health`              | 健康检查          |
| POST   | `/api/articles`            | 新增文章（JSON）  |
| POST   | `/api/articles/upload`     | 上传 TXT 文件     |
| GET    | `/api/articles`            | 分页查询文章列表  |
| POST   | `/api/search`              | 语义检索（JSON）  |
| GET    | `/api/search/stream`       | 流式语义检索      |

### 统一错误格式

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

### 错误码说明

| 错误码               | HTTP | 说明                          |
| -------------------- | ---- | ----------------------------- |
| EMPTY_QUERY          | 400  | query 为空                    |
| INVALID_TITLE        | 400  | 标题不合法                    |
| INVALID_CONTENT      | 400  | 正文不合法                    |
| INVALID_FILE_TYPE    | 400  | 上传的不是 .txt 文件          |
| FILE_TOO_LARGE       | 413  | 文件超过 1 MB 限制            |
| FILE_ENCODING_ERROR  | 400  | 文件编码无法识别              |
| KNOWLEDGE_BASE_EMPTY | 409  | 知识库中暂无文章              |
| MODEL_UNAVAILABLE    | 503  | Embedding 模型不可用          |
| DATABASE_ERROR       | 500  | 数据库操作失败                |
| SERVICE_UNAVAILABLE  | 503  | MCP 无法连接知识库后端        |
| SEARCH_TIMEOUT       | 504  | 查询超时                      |
| INTERNAL_ERROR       | 500  | 未知内部错误                  |

## 运行测试

```bash
# 单元测试（文本切分）
pytest tests/test_chunk.py -v

# API 集成测试
pytest tests/test_api.py -v

# 冒烟测试（需先启动服务）
python scripts/smoke_test.py

# 运行全部测试
pytest tests/ -v && python scripts/smoke_test.py
```

## 设计取舍

本项目面向小规模笔试场景，做出以下取舍：

- **SQLite 替代 MySQL/PostgreSQL**：零安装，单文件，部署成本最低。
- **SQLite BLOB + NumPy 替代 FAISS/ChromaDB**：避免引入额外向量数据库依赖。
  向量存储逻辑封装在 `knowledge_service.py` 中，后续可通过统一接口替换。
- **sentence-transformers 替代 API 服务**：本地运行，无 API Key，无网络依赖。
- **原生前端替代 React/Vue**：FastAPI 直接托管静态文件，无需 Node 工程，
  评审时只需启动一个服务。
- **不生成大模型回答**：系统只做检索和片段返回，不调用 LLM 重新合成答案，
  保证返回内容是原文、可追溯、不编造。
- **MCP 而非 Skill**：选择 MCP stdio 协议，工具定义标准、日志可审计、
  与 Claude Code 集成零配置。

## 项目来源说明

本项目根据笔试要求独立实现，核心能力包括文本切分、Embedding 向量化、
余弦相似度语义检索、流式响应以及 MCP Agent 工具接入。

项目实现过程使用 AI 编程工具辅助代码生成、审查和测试，
但系统设计、功能验收与最终交付由本人完成。
