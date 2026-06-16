# Harness Engineering — Vue 3 + FastAPI 迁移设计

**日期**: 2026-06-16
**状态**: 已确认
**目标**: 将现有 Next.js 16 应用迁移为 Vue 3 + FastAPI 前后端分离架构，代码写入 `harness-engineering-py/`，与现有 `harness-engineering/` 共存。

---

## 1. 概述

### 1.1 背景

现有 `harness-engineering/` 是一个基于 Next.js 16 App Router 的单体应用，包含 Skills/Agents 市场 + 使用 Dashboard + Workflow 聊天界面。前端使用 React 19 + Tailwind CSS 3，后端 API 通过 Next.js Route Handlers 实现，AI 引擎通过 ACP 协议驱动本地 OpenCode CLI。

### 1.2 目标

将技术栈迁移为 Vue 3 + FastAPI 前后端分离架构，功能等价，UI 保持一致，代码写入 `harness-engineering-py/` 目录，与原项目共存。

### 1.3 关键决策

| 决策项 | 选择 |
|--------|------|
| 与现有代码关系 | 共存于 `harness-engineering-py/` |
| 后端引擎层 | 保持 OpenCode ACP 子进程方式 |
| UI 语言 | 中文 |
| 项目结构 | 单仓双包（frontend/ + backend/） |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia + composables 混合 |
| 会话存储 | 文件系统 JSON |
| 构建工具 | Vite |
| 图表库 | ECharts |
| CSS 方案 | Element Plus SCSS 变量定制 |

---

## 2. 架构概览

```
┌─────────────── Vue 3 SPA (Vite) ───────────────┐
│                                                   │
│  Dashboard  Skills  Agents  Workflow              │
│  (mock数据) (mock)  (mock)  (SSE 实时)            │
│       │       │       │       │                   │
│       ▼       ▼       ▼       ▼                   │
│  ┌─────────────────────────────────────────────┐  │
│  │         Pinia Stores + Composables          │  │
│  │  chat store │ engine store │ useChatStream  │  │
│  └────────────────────┬───────────────────────┘  │
│                       │ HTTP + SSE                │
└───────────────────────┼──────────────────────────┘
                        │
┌───────────────────────┼──── FastAPI ──────────────┐
│                       ▼                           │
│  ┌─────────────────────────────────────────────┐  │
│  │              API Routers                     │  │
│  │  /api/chat/stream  /api/chat/sessions        │  │
│  │  /api/chat/permission  /api/engines/...      │  │
│  └────────────────────┬───────────────────────┘  │
│                       │                           │
│  ┌────────────────────▼───────────────────────┐  │
│  │            Services Layer                   │  │
│  │  EngineFactory → OpenCodeWrapper → ACPEngine│  │
│  │  SessionStore (文件 JSON)                   │  │
│  └────────────────────┬───────────────────────┘  │
│                       │                           │
│                       ▼                           │
│              opencode acp (子进程)                 │
│              data/chat-sessions/ (JSON)            │
└───────────────────────────────────────────────────┘
```

### 2.1 数据流

1. **Dashboard/Skills/Agents** — Vue 前端直接用 mock 数据渲染，不经过后端
2. **Workflow 聊天** — `POST /api/chat/stream` 发起消息 → 后端创建引擎执行 → `GET /api/chat/stream?id=xxx` SSE 流式返回 → 前端 EventSource 接收
3. **权限流程** — SSE 推送 permission_request → 用户点击选项 → `POST /api/chat/permission` → 后端 resolve → 引擎继续执行
4. **会话管理** — CRUD 通过 `/api/chat/sessions`，存储为 `data/chat-sessions/{id}.json`
5. **开发代理** — Vite dev server 将 `/api/*` 代理到 FastAPI `localhost:8000`

---

## 3. 项目结构

```
harness-engineering-py/
├── frontend/                    # Vue 3 + Vite SPA
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── src/
│       ├── App.vue
│       ├── main.ts              # createApp, Pinia, Router, Element Plus
│       ├── router/
│       │   └── index.ts         # 4 条路由
│       ├── types/
│       │   ├── index.ts         # MarketItem, DashboardStats, TrendPoint 等
│       │   └── chat.ts          # ChatMessage, ChatSession, SSEEvent 等
│       ├── mock/
│       │   └── data.ts          # 12 skills + 8 agents + dashboard 数据
│       ├── views/
│       │   ├── DashboardView.vue
│       │   ├── SkillsView.vue
│       │   ├── AgentsView.vue
│       │   └── WorkflowView.vue
│       ├── components/
│       │   ├── layout/
│       │   │   └── Navbar.vue
│       │   ├── dashboard/
│       │   │   ├── StatsCards.vue
│       │   │   ├── UsageTrend.vue
│       │   │   ├── UsageRanking.vue
│       │   │   └── WorkflowCard.vue
│       │   ├── skills/
│       │   │   ├── SkillCard.vue
│       │   │   └── SkillFilter.vue
│       │   ├── agents/
│       │   │   ├── AgentCard.vue
│       │   │   └── AgentFilter.vue
│       │   └── workflow/
│       │       ├── ChatLayout.vue
│       │       ├── ChatSidebar.vue
│       │       ├── ChatStream.vue
│       │       ├── ChatMessage.vue
│       │       ├── ChatInput.vue
│       │       ├── EngineInfo.vue
│       │       ├── PermissionCard.vue
│       │       ├── ThoughtBlock.vue
│       │       └── ToolCallCard.vue
│       ├── composables/
│       │   ├── useChatStream.ts
│       │   └── useMarketFilter.ts
│       └── stores/
│           ├── chat.ts
│           └── engine.ts
│
└── backend/                     # FastAPI
    ├── requirements.txt
    ├── pyproject.toml
    └── app/
        ├── main.py              # FastAPI 入口，CORS 配置
        ├── routers/
        │   ├── chat.py          # POST/GET/DELETE /api/chat/stream, POST /api/chat/permission
        │   ├── sessions.py      # GET/POST/DELETE /api/chat/sessions
        │   └── engines.py       # GET /api/engines/availability
        ├── services/
        │   ├── engine_interface.py    # 抽象基类 Engine
        │   ├── engine_factory.py      # 引擎池 Map + TTL 10min
        │   ├── acp_engine.py          # ACP 协议：spawn opencode acp，stdio JSON-RPC
        │   ├── opencode_wrapper.py    # Engine 实现：包装 ACPEngine
        │   ├── session_store.py       # 文件 JSON CRUD
        │   ├── stream_state.py        # 内存流状态追踪
        │   └── permission_queue.py    # 内存权限请求队列
        └── models/
            └── schemas.py       # Pydantic 模型
```

---

## 4. 前端设计

### 4.1 路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | 重定向到 `/dashboard` | |
| `/dashboard` | `DashboardView.vue` | 仪表盘 |
| `/skills` | `SkillsView.vue` | Skills 市场 |
| `/agents` | `AgentsView.vue` | Agents 市场 |
| `/workflow` | `WorkflowView.vue` | 聊天工作台 |

### 4.2 组件对应关系

| React 组件 | Vue 组件 | Element Plus 替代 |
|-----------|---------|------------------|
| `navbar.tsx` | `Navbar.vue` | `el-menu` 替代手写 nav |
| `stats-cards.tsx` | `StatsCards.vue` | `el-row` / `el-col` / `el-card` |
| `usage-trend.tsx` | `UsageTrend.vue` | ECharts 替代 Recharts |
| `usage-ranking.tsx` | `UsageRanking.vue` | 手写排名列表 |
| `workflow-card.tsx` | `WorkflowCard.vue` | `el-card` |
| `skill-card.tsx` | `SkillCard.vue` | `el-card` |
| `skill-filter.tsx` | `SkillFilter.vue` | `el-input` + `el-tag` |
| `agent-card.tsx` | `AgentCard.vue` | `el-card` |
| `agent-filter.tsx` | `AgentFilter.vue` | `el-input` + `el-tag` |
| `chat-layout.tsx` | `ChatLayout.vue` | 手写布局（定制性强） |
| `chat-sidebar.tsx` | `ChatSidebar.vue` | `el-menu` + `el-select` |
| `chat-message.tsx` | `ChatMessage.vue` | 手写气泡（定制性强） |
| `chat-input.tsx` | `ChatInput.vue` | `el-input` textarea |
| `chat-stream.tsx` | `ChatStream.vue` | 手写滚动容器 |
| `engine-info.tsx` | `EngineInfo.vue` | 手写信息条 |
| `permission-card.tsx` | `PermissionCard.vue` | `el-card` + `el-button` |
| `thought-block.tsx` | `ThoughtBlock.vue` | 手写折叠面板 |
| `tool-call-card.tsx` | `ToolCallCard.vue` | 手写折叠卡片 |

### 4.3 状态管理

**Pinia Stores：**

- `chat.ts` — 当前会话 ID、会话列表、消息列表、流式状态、模型选择
- `engine.ts` — 引擎可用性、模型列表

**Composables：**

- `useChatStream.ts` — SSE 连接管理（sendMessage、resolvePermission、cancelStream），从现有 `use-chat-stream.ts` 迁移
- `useMarketFilter.ts` — Skills/Agents 共用的搜索 + 标签筛选逻辑

### 4.4 样式方案

- Element Plus SCSS 变量定制主题色、圆角、间距
- 局部自定义样式使用 Vue scoped style
- 不引入 Tailwind CSS
- 暗色模式：Element Plus 内置暗色模式支持，通过 `el-config-provider` 切换

---

## 5. 后端设计

### 5.1 API 端点

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| `GET` | `/api/chat/sessions` | 列出所有会话 | — | `{ sessions: ChatSession[] }` |
| `POST` | `/api/chat/sessions` | 创建新会话 | `{ engine?, model? }` | `{ id, title, ... }` |
| `DELETE` | `/api/chat/sessions` | 删除会话 | `{ id }` | `{ deleted: true }` |
| `POST` | `/api/chat/stream` | 发起消息执行 | `{ message, model, sessionId, agentSessionId }` | `{ chatId }` |
| `GET` | `/api/chat/stream` | SSE 流式连接 | `?id=chatId` | SSE 事件流 |
| `DELETE` | `/api/chat/stream` | 取消执行 | `?id=chatId` | `{ cancelled: true }` |
| `POST` | `/api/chat/permission` | 解析权限请求 | `{ requestId, optionId }` | `{ resolved: true }` |
| `GET` | `/api/engines/availability` | 引擎可用性 | — | `{ engines: EngineAvailability[] }` |

### 5.2 SSE 事件类型

| 事件名 | 数据 | 触发时机 |
|--------|------|---------|
| `connected` | `{ chatId }` | SSE 连接建立 |
| `delta` | `{ content }` | AI 文本增量 |
| `thinking` | `{ content }` | 思考过程增量 |
| `permission_request` | `{ request }` | 引擎请求权限 |
| `engine_error` | `{ message }` | 引擎级错误 |
| `done` | `{ result, sessionId, isError }` | 执行完成 |
| `failed` | `{ message }` | 执行失败 |

SSE 使用 FastAPI `StreamingResponse` + `text/event-stream`，格式为 `event: <type>\ndata: <json>\n\n`。

### 5.3 服务层

| 模块 | 职责 | 对应原模块 |
|------|------|-----------|
| `engine_interface.py` | 抽象基类 Engine，定义 execute/cancel/isAvailable/resolvePermission | `engine-interface.ts` |
| `engine_factory.py` | 引擎池 Map，TTL 10 分钟自动回收，get_or_create_engine() | `engine-factory.ts` |
| `acp_engine.py` | spawn `opencode acp` 子进程，stdio JSON-RPC 通信，事件发射 | `acp-engine.ts` |
| `opencode_wrapper.py` | 实现 Engine 接口，包装 ACPEngine，翻译事件格式 | `opencode-wrapper.ts` |
| `session_store.py` | 文件系统 JSON 会话 CRUD（`data/chat-sessions/`） | `session-store.ts` |
| `stream_state.py` | 内存字典追踪活跃流（chatId → StreamState） | `stream-state.ts` |
| `permission_queue.py` | 内存字典存储待处理权限请求（requestId → engine） | `permission-queue.ts` |

### 5.4 依赖

```
fastapi
uvicorn[standard]
pydantic
aiofiles
```

---

## 6. 错误处理

### 6.1 前端

| 场景 | 处理方式 |
|------|---------|
| 引擎不可用 | EngineInfo 显示"引擎未连接"警告，禁用发送按钮 |
| SSE 连接中断 | EventSource.onerror → 显示"连接中断，正在重连..."，3 秒后重试（最多 3 次） |
| 流式返回错误 | SSE `engine_error` → 消息气泡显示红色错误文本 |
| 执行失败 | SSE `failed` → 消息气泡显示"执行失败: {message}" |
| 权限请求超时 | 无超时（等待用户操作，与现有行为一致） |
| 会话加载失败 | 侧边栏显示空状态，允许新建会话 |
| 发送消息失败 | el-message 错误提示，不移除用户消息 |
| 网络断开 | 所有 API catch → el-message "网络连接失败" |

### 6.2 后端

| 场景 | 处理方式 |
|------|---------|
| opencode 未安装 | isAvailable() 返回 false |
| opencode 进程崩溃 | catch 子进程 exit → engine_error SSE 事件，清理流状态 |
| 会话文件不存在 | getSession() 返回 None → API 返回 404 |
| 会话文件损坏 | JSON 解析失败 → 500，日志记录文件路径 |
| chatId 无效 | getStream() 返回 None → SSE 返回 failed 后关闭 |
| 并发发送消息 | 同一 session 有活跃流 → POST 返回 409 Conflict |
| 权限请求不存在 | resolvePermission 找不到 requestId → 404 |
| 引擎池 TTL 过期 | 自动回收，下次消息创建新引擎 |

### 6.3 边界情况

- **空会话列表**：侧边栏显示"暂无会话，点击新建"
- **空消息列表**：聊天区显示"发送消息开始对话"
- **超长消息**：word-break: break-word，不溢出
- **极快连续 SSE 事件**：requestAnimationFrame 批量更新 DOM
- **页面切换时正在流式传输**：onUnmounted 关闭 EventSource，后端继续执行（不取消）
- **模型列表为空**：模型选择器显示"无可用模型"，使用默认值

---

## 7. 测试策略

### 7.1 前端

- 组件渲染测试（Vitest + @vue/test-utils）
- composables 单元测试
- Pinia stores 单元测试

### 7.2 后端

- pytest + httpx AsyncClient 端点测试
- 服务层单元测试（mock 子进程）
- SSE 流集成测试

---

## 8. 启动方式

```bash
# 后端
cd harness-engineering-py/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（Vite dev server 代理 /api → localhost:8000）
cd harness-engineering-py/frontend
npm install
npm run dev
```
