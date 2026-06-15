# Knowledge Agent Mini

> 一个体量小、链路完整、可被 Agent 真实调用的轻量知识库系统

Knowledge Agent Mini 面向本次 Agent 开发笔试场景，实现了从**知识录入、文本切分、向量化、语义检索、流式返回，到 Claude Code 调用 MCP Tool**的完整闭环。

项目不追求堆叠复杂功能，而是重点保证：

- **体量小**：单体 FastAPI 应用，无需安装 MySQL、Redis 或独立向量数据库；
- **链路完整**：知识录入、向量入库、语义检索、流式响应、Agent 调用全部打通；
- **Agent 真调用**：Claude Code 通过 MCP 协议实际调用 `search_knowledge`；
- **异常可控**：空查询、知识库为空、无相关结果、服务不可用、请求超时均有明确处理；
- **快速验收**：依赖与模型准备完成后，可在约五分钟内完成启动和核心功能验证；
- **能力可验证**：项目代码可对应验证简历中的 RAG、Tool Calling、流式交互和异常兜底能力。

------

## 一分钟了解项目

```text
录入文章或上传 TXT
        ↓
保存文章并自动切分
        ↓
生成中文 Embedding 向量
        ↓
向量持久化到 SQLite
        ↓
输入自然语言 Query
        ↓
执行 Top-K 语义检索
        ↓
返回标题、原文、来源和相似度
        ↓
后端流式输出查询结果
        ↓
Claude Code 通过 MCP 调用同一检索能力
```

本项目中的语义检索不是 SQL `LIKE` 关键词匹配，流式展示也不是前端打字机动画。

------

## 核心验收结果

### 1. 语义检索

知识库中录入《春》《故乡》等文章后：

```text
查询：春天
预期：返回《春》
查询：少年闰土
预期：返回《故乡》
```

返回结果包含：

- 文章标题；
- 最相关原文片段；
- 来源文件；
- 语义相似度；
- 请求追踪 ID。

### 2. 无答案拒答

```text
查询：量子芯片制造工艺
```

当知识库中没有足够相关的内容时，系统返回空结果并明确提示：

```text
知识库中未检索到足够相关的内容。
```

系统不会调用大模型编造答案。

### 3. Agent 真实调用

在 Claude Code 中输入：

```text
帮我查询知识库中与春天有关的内容，并告诉我来源。
```

Agent 会根据工具描述自主调用：

```text
search_knowledge(query="春天", top_k=3)
```

完整调用链路：

```text
Claude Code
    ↓ MCP stdio
search_knowledge
    ↓ HTTP
POST /api/search
    ↓
Embedding 语义检索
    ↓
返回知识库原文和来源
```

普通对话不会强制调用工具：

```text
你好，请介绍一下你自己。
```

------

## 运行效果

![image-20260615150025835](C:\Users\20914\AppData\Roaming\Typora\typora-user-images\image-20260615150025835.png)

------

## 已实现功能

### 知识库

-  直接输入文章标题和正文
-  上传 TXT 文件
-  UTF-8、UTF-8 BOM、GB18030 编码兼容
-  文章分页查询
-  自动文本清洗与分块
-  文章与向量事务化入库

### 语义检索

-  中文 Embedding 向量化
-  Top-K 语义相似度检索
-  相似度阈值过滤
-  同一文章结果去重
-  返回标题、片段、来源和相似度
-  无相关内容时拒绝编造

### 流式交互

-  FastAPI `StreamingResponse`
-  浏览器 `ReadableStream`
-  后端逐块发送结果
-  查询 Loading 和按钮禁用
-  失败状态和无结果状态提示

### Agent 与 MCP

-  Python FastMCP Server
-  stdio 传输
-  `search_knowledge` Tool
-  Claude Code 项目级 MCP 配置
-  Agent 自主判断是否调用
-  工具调用日志
-  后端不可用和超时兜底

### 工程质量

-  环境变量配置
-  统一错误响应结构
-  参数和文件校验
-  单元测试
-  API 测试
-  冒烟测试
-  示例数据初始化脚本
-  Windows 启动脚本

------

## 系统架构

```text
┌──────────────────────────────────────┐
│              Web 页面                │
│                                      │
│  文章录入 · TXT上传 · 分页 · 查询     │
│            流式结果展示               │
└──────────────────┬───────────────────┘
                   │ HTTP
                   ▼
┌──────────────────────────────────────┐
│             FastAPI 后端              │
│                                      │
│  Article API                         │
│  Search API                          │
│  Streaming API                       │
│  参数校验与异常处理                   │
└───────────────┬───────────┬──────────┘
                │           │
                ▼           ▼
       ┌──────────────┐  ┌────────────────┐
       │   SQLite     │  │ 中文 Embedding │
       │ 文章 + Chunk │  │ BGE Small ZH   │
       │ + 向量 BLOB  │  │                │
       └──────────────┘  └────────────────┘

┌──────────────────────────────────────┐
│             Claude Code              │
│     判断用户是否需要查询知识库         │
└──────────────────┬───────────────────┘
                   │ MCP stdio
                   ▼
┌──────────────────────────────────────┐
│         Knowledge MCP Server         │
│                                      │
│ search_knowledge(query, top_k)       │
└──────────────────┬───────────────────┘
                   │ HTTP
                   ▼
           FastAPI /api/search
```

------

## 技术选型

| 模块       | 技术                    | 选择原因                            |
| ---------- | ----------------------- | ----------------------------------- |
| 后端       | FastAPI + Uvicorn       | 支持参数校验、流式响应和 Swagger    |
| 数据库     | SQLite                  | 无需安装服务，单文件便于交付        |
| 向量存储   | SQLite BLOB             | 减少额外组件和启动步骤              |
| 相似度计算 | NumPy                   | 适合本项目的小规模知识数据          |
| Embedding  | BAAI/bge-small-zh-v1.5  | 中文语义效果较好，模型体积相对可控  |
| 前端       | HTML + CSS + JavaScript | 无需 Node.js，后端直接托管          |
| MCP        | Python FastMCP          | 标准工具协议，可被 Claude Code 调用 |

------

## 为什么没有使用复杂技术栈

本项目有意控制体量。

没有引入：

- MySQL；
- Redis；
- ChromaDB；
- Milvus；
- 独立 Vue/React 工程；
- 在线大模型生成接口；
- 登录和权限系统；
- 多 Agent 工作流。

原因不是无法实现，而是这些内容不会提升本题核心链路的可信度，反而会增加安装、配置和联调成本。

本项目优先保证：

```text
可以运行
> 可以检索
> 可以流式返回
> Agent 可以真实调用
> 异常情况下不会崩溃
```

------

# 快速启动

## 环境要求

```text
Python 3.10+
Windows / macOS / Linux
```

> 首次安装 Python 依赖和下载 Embedding 模型的时间取决于网络环境。依赖与模型准备完成后，系统可在约五分钟内完成启动、示例数据导入和功能验证。

### 首次运行

首次运行需要先创建虚拟环境、安装依赖并初始化示例数据：

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_demo_data.py
```

完成后，后续均可直接双击 `start.bat` 启动。

## 1. 创建虚拟环境

Windows：

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 创建环境配置

Windows：

```bash
copy .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

无法直接访问 Hugging Face 时，可以在 `.env` 中配置：

```env
HF_ENDPOINT=https://hf-mirror.com
```

## 4. 启动 Web 服务

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows 也可以运行：

```bash
start.bat
```

## 5. 初始化示例数据

新开一个终端并激活虚拟环境：

```bash
python scripts/init_demo_data.py
```

示例数据包括：

- 《春》
- 《故乡》
- 《背影》
- 《济南的冬天》

## 6. 打开页面

```text
http://127.0.0.1:8000
```

Swagger 接口文档：

```text
http://127.0.0.1:8000/docs
```

------

# 五分钟验收路径

服务启动后，按照以下顺序即可快速验证核心链路。

## 第一步：检查服务状态

```text
GET http://127.0.0.1:8000/api/health
```

预期：

```json
{
  "status": "ok"
}
```

## 第二步：检查文章分页

打开 Web 页面，确认示例文章已经出现在文章列表中。

## 第三步：验证语义检索

依次查询：

```text
春天
少年闰土
```

确认分别返回《春》和《故乡》。

## 第四步：验证无答案拒答

查询：

```text
量子芯片制造工艺
```

确认系统明确提示没有足够相关内容。

## 第五步：验证 Agent 调用

启动 Claude Code，通过 `/mcp` 确认 `knowledge-search` 已连接，再输入：

```text
帮我查询知识库中与春天有关的内容，并告诉我来源。
```

确认 Claude Code 调用了 `search_knowledge`。

------

# Claude Code MCP 配置

## 1. 复制配置文件

Windows：

```bash
copy .mcp.json.example .mcp.json
```

macOS / Linux：

```bash
cp .mcp.json.example .mcp.json
```

配置示例：

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

## 2. 启动 Claude Code

确保 FastAPI 已运行，然后从项目根目录启动：

```bash
claude
```

## 3. 检查 MCP 状态

在 Claude Code 中输入：

```text
/mcp
```

预期看到：

```text
knowledge-search
search_knowledge
Connected
```

## 4. Agent 调用测试

### 应调用工具

```text
帮我查询知识库中与春天有关的内容，并告诉我来源。
知识库里是否有少年闰土相关内容？
请从知识库查找描写父爱的文章。
```

### 不应调用工具

```text
你好。
解释一下 Python 列表推导式。
```

### 应调用但返回无结果

```text
查询知识库中关于量子芯片制造工艺的内容。
```

------

# API 一览

| 方法 | 接口                   | 说明          |
| ---- | ---------------------- | ------------- |
| GET  | `/api/health`          | 健康检查      |
| POST | `/api/articles`        | 直接录入文章  |
| POST | `/api/articles/upload` | 上传 TXT 文件 |
| GET  | `/api/articles`        | 分页查询文章  |
| POST | `/api/search`          | JSON 语义检索 |
| GET  | `/api/search/stream`   | 流式语义检索  |

普通检索接口同时供 Web 页面和 MCP Tool 复用，避免维护两套检索逻辑。

------

# 异常处理

系统对以下情况进行了明确处理：

| 场景                 | 系统行为                 |
| -------------------- | ------------------------ |
| query 为空           | 返回参数错误，不执行模型 |
| 标题或正文为空       | 拒绝入库并提示原因       |
| 上传非 TXT 文件      | 返回文件类型错误         |
| 文件过大             | 返回文件大小错误         |
| 文件编码无法识别     | 提示转换为 UTF-8         |
| 知识库为空           | 提示先录入知识           |
| 无相关结果           | 返回空结果，不编造       |
| Embedding 模型不可用 | 返回模型服务错误         |
| 数据库操作失败       | 回滚事务并返回错误       |
| MCP 无法连接后端     | 返回服务不可用           |
| MCP 请求超时         | 返回超时错误             |
| 未知异常             | 记录日志并返回统一错误   |

统一错误格式：

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

------

# 测试

运行单元测试和 API 测试：

```bash
pytest tests/ -v
```

运行冒烟测试：

```bash
python scripts/smoke_test.py
```

测试覆盖：

- 文本清洗与分块；
- 文章录入；
- TXT 上传；
- 分页查询；
- 语义检索；
- 空 Query；
- 知识库为空；
- 无答案拒答；
- 文件类型和编码错误；
- 流式接口；
- 服务健康状态。

> README 中不固定声明测试通过数量，以实际提交版本的运行结果为准。

------

# 项目目录

```text
knowledge-agent-mini/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── schemas.py
│   ├── exceptions.py
│   ├── services/
│   │   ├── chunk_service.py
│   │   ├── embedding_service.py
│   │   └── knowledge_service.py
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── mcp_server/
│   └── server.py
├── sample_data/
├── scripts/
│   ├── init_demo_data.py
│   └── smoke_test.py
├── tests/
├── screenshots/
├── data/
├── logs/
├── .env.example
├── .mcp.json.example
├── requirements.txt
├── requirements-lock.txt
├── start.bat
└── README.md
```

------

# 与个人简历能力的验证映射

这个项目不是独立于简历之外的展示 Demo，而是对简历中 Agent 应用开发能力的一次可运行验证。

| 简历能力       | 项目中的可验证实现                 |
| -------------- | ---------------------------------- |
| RAG 检索问答   | 文本切分、Embedding、Top-K 检索    |
| 来源引用       | 返回文章标题、来源文件和原文片段   |
| 无答案拒答     | 相似度阈值与空结果兜底             |
| Tool Calling   | `search_knowledge` MCP Tool        |
| Agent 工具调用 | Claude Code 自主判断并调用 MCP     |
| FastAPI 后端   | 文章、搜索、流式和健康接口         |
| 流式消息展示   | StreamingResponse + ReadableStream |
| 参数校验       | Pydantic 与业务参数校验            |
| 异常兜底       | 统一错误码、超时和服务不可用处理   |
| 前后端联调     | Web 页面调用 FastAPI 接口          |
| 工程交付       | 环境配置、测试、日志和运行文档     |

评审可以通过以下方式直接验证：

1. 查看 Web 页面；
2. 调用 Swagger API；
3. 运行自动化测试；
4. 查看 MCP 配置；
5. 在 Claude Code 中触发 Tool Calling；
6. 查看 `logs/mcp_calls.log` 中的真实调用记录。

------

# 设计边界

当前版本定位为轻量笔试交付项目，适合少量文章和本地单用户场景。

生产环境可进一步扩展：

- 将 SQLite 替换为 PostgreSQL；
- 将向量 BLOB 替换为 ChromaDB、FAISS 或 Milvus；
- 增加文档删除和向量同步；
- 增加用户权限和多知识库；
- 增加模型重排；
- 增加 Agent 会话管理；
- 增加 Docker 和自动化部署。

这些内容不属于本次笔试核心范围，因此当前版本优先保证核心链路的稳定性和可验证性。

------

# 项目说明

本项目根据笔试要求完成，核心能力包括：

- 知识录入；
- 文本切分；
- Embedding 向量化；
- 语义相似度检索；
- 流式响应；
- MCP Tool；
- Agent Tool Calling；
- 参数校验；
- 异常处理；
- 测试与运行文档。

开发过程中使用 AI 编程工具辅助代码生成、检查和测试，系统设计、功能取舍、运行验证和最终交付由本人完成。
