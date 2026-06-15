# Knowledge Agent Mini PR 开发计划

## PR 1：初始化项目与知识库基础接口

### PR 标题

```text
feat: initialize FastAPI project and article storage
```

### 主要开发内容

- 创建 FastAPI 项目目录；
- 配置 SQLite 数据库；
- 创建 `articles` 和 `chunks` 数据表；
- 实现健康检查接口；
- 实现文章直接录入接口；
- 实现文章分页查询接口；
- 增加基础参数校验；
- 创建 `.env.example` 和 `requirements.txt`。

### 本次提交文件

```text
app/main.py
app/config.py
app/database.py
app/schemas.py
app/exceptions.py
app/__init__.py
data/.gitkeep
.env.example
.gitignore
requirements.txt
README.md
```

### 验收标准

- 项目可以正常启动；
- `/api/health` 返回正常；
- 可以新增文章；
- 可以分页查询文章；
- 空标题、空正文能够返回明确错误。

### Commit

```text
feat: initialize FastAPI project and article storage
```

------

## PR 2：实现文本切分、向量化和语义检索

### PR 标题

```text
feat: add embedding pipeline and semantic search
```

### 主要开发内容

- 实现文本清洗；
- 实现文章 Chunk 切分；
- 接入中文 Embedding 模型；
- 将 Chunk 向量保存到 SQLite；
- 实现 Query 向量化；
- 使用余弦相似度进行 Top-K 检索；
- 返回标题、相关片段、来源和相似度；
- 实现相似度阈值；
- 实现无答案拒答；
- 同一篇文章只保留最高分结果。

### 本次提交文件

```text
app/services/chunk_service.py
app/services/embedding_service.py
app/services/knowledge_service.py
app/services/__init__.py
app/database.py
app/main.py
app/schemas.py
tests/test_chunk.py
```

### 验收标准

- 查询“春天”能够找到《春》；
- 查询“少年闰土”能够找到《故乡》；
- 返回结果包含标题、片段、来源和相似度；
- 无关查询返回空结果；
- 查询不是通过 SQL LIKE 实现。

### Commit

```text
feat: add embedding pipeline and semantic search
```

------

## PR 3：实现 TXT 上传、页面管理和流式查询

### PR 标题

```text
feat: add knowledge UI, txt upload and streaming search
```

### 主要开发内容

- 实现 TXT 文件上传；
- 支持 UTF-8、UTF-8 BOM 和 GB18030 编码；
- 增加文件类型和文件大小校验；
- 创建知识库管理页面；
- 实现文章输入表单；
- 实现 TXT 上传表单；
- 实现文章分页列表；
- 实现语义查询页面；
- 使用 `StreamingResponse` 实现后端流式输出；
- 前端使用 `ReadableStream` 接收文字；
- 增加保存中、查询中、失败和无结果状态。

### 本次提交文件

```text
app/main.py
app/services/knowledge_service.py
app/static/index.html
app/static/app.js
app/static/style.css
sample_data/春.txt
sample_data/故乡.txt
sample_data/背影.txt
sample_data/济南的冬天.txt
```

### 验收标准

- 可以直接输入文章；
- 可以上传 TXT 文件；
- 文章列表可以分页；
- 查询结果文字逐步显示；
- 流式效果来自后端，不是纯前端动画；
- 上传错误文件时有明确提示；
- 中文 TXT 不乱码。

### Commit

```text
feat: add knowledge UI, txt upload and streaming search
```

------

## PR 4：实现 MCP Server 和 Agent 真实调用

### PR 标题

```text
feat: expose semantic search through MCP tool
```

### 主要开发内容

- 创建 Python MCP Server；
- 使用 FastMCP 实现 stdio 服务；
- 暴露 `search_knowledge` 工具；
- 工具参数包括 `query` 和 `top_k`；
- MCP Tool 调用 FastAPI `/api/search`；
- 增加空 Query 校验；
- 增加服务不可用处理；
- 增加请求超时处理；
- 增加后端错误处理；
- 创建 Claude Code MCP 配置示例；
- 记录 MCP 调用日志；
- 验证 Agent 能自主决定是否调用工具。

### 本次提交文件

```text
mcp_server/server.py
mcp_server/__init__.py
.mcp.json.example
app/main.py
logs/.gitkeep
README.md
```

### 验收标准

- Claude Code 中 MCP 状态显示 Connected；
- 可以看到 `search_knowledge` 工具；
- 输入知识库查询时 Agent 会调用工具；
- 普通问候时 Agent 不调用工具；
- 后端关闭时 MCP 返回可读错误；
- MCP Server 不向 stdout 输出普通日志；
- `logs/mcp_calls.log` 中能看到调用记录。

### Commit

```text
feat: expose semantic search through MCP tool
```

------

## PR 5：补充异常处理、测试和示例数据

### PR 标题

```text
test: add validation, fallback handling and smoke tests
```

### 主要开发内容

- 统一接口错误返回结构；
- 补充空 Query 处理；
- 补充知识库为空处理；
- 补充模型加载失败处理；
- 补充数据库异常处理；
- 补充文件编码错误处理；
- 增加单元测试；
- 增加 API 测试；
- 增加冒烟测试脚本；
- 增加示例数据初始化脚本；
- 为搜索请求增加 `request_id`；
- 记录搜索耗时和返回数量。

### 本次提交文件

```text
app/exceptions.py
app/main.py
app/database.py
app/services/embedding_service.py
app/services/knowledge_service.py
scripts/init_demo_data.py
scripts/smoke_test.py
tests/test_api.py
tests/test_chunk.py
```

### 验收标准

- 空 Query 返回明确错误；
- 知识库为空时不会崩溃；
- 无相关结果时不会编造答案；
- Embedding 模型失败时返回明确提示；
- 冒烟测试可以一次运行完成；
- 核心测试全部通过。

### Commit

```text
test: add validation, fallback handling and smoke tests
```

------

## PR 6：完善 README、启动脚本和最终交付

### PR 标题

```text
docs: complete setup guide and delivery documentation
```

### 主要开发内容

- 完善项目简介；
- 添加功能完成清单；
- 添加系统架构说明；
- 添加五分钟启动步骤；
- 添加示例数据初始化方法；
- 添加 Web 页面使用方法；
- 添加 MCP 配置方法；
- 添加 Claude Code 测试提示词；
- 添加异常处理说明；
- 添加项目设计取舍；
- 添加运行截图；
- 添加 Windows 启动脚本；
- 检查敏感信息和本地绝对路径；
- 检查最终提交目录。

### 本次提交文件

```text
README.md
DEVELOPMENT.md
PR_PLAN.md
start.bat
requirements-lock.txt
screenshots/
```

### 验收标准

- 根据 README 可以从零启动；
- 所有命令能够直接复制执行；
- Web 服务可以正常查询；
- Claude Code 可以调用 MCP Tool；
- README 中有 Agent 调用截图；
- 项目中没有 API Key；
- 项目中没有 `.venv` 和模型文件；
- 提交目录中包含个人简历。

### Commit

```text
docs: complete setup guide and delivery documentation
```

------

# 建议的开发顺序

```text
PR 1：项目基础和文章管理
    ↓
PR 2：语义检索核心链路
    ↓
PR 3：前端页面和流式返回
    ↓
PR 4：MCP 与 Agent 真实调用
    ↓
PR 5：异常处理和测试
    ↓
PR 6：README、截图和最终交付
```

# 时间不足时的处理原则

如果时间明显不足，不要删除 PR 4。优先保证：

```text
PR 1
→ PR 2
→ PR 4
→ PR 3
→ PR 5
→ PR 6
```

其中：

- PR 1、PR 2、PR 4 是核心能力；
- PR 3 必须至少实现简单页面和流式返回；
- PR 5 只保留核心异常和冒烟测试；
- PR 6 至少完成启动说明、MCP 配置和截图。

# 最终建议保留的 Commit

```text
feat: initialize FastAPI project and article storage
feat: add embedding pipeline and semantic search
feat: add knowledge UI, txt upload and streaming search
feat: expose semantic search through MCP tool
test: add validation, fallback handling and smoke tests
docs: complete setup guide and delivery documentation
```