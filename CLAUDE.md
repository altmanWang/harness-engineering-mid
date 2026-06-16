# Harness Engineering

Skills & Agents 市场 + Workflow 聊天界面的前后端分离应用。两个版本共存：

- `harness-engineering/` — Next.js 16 单体版
- `harness-engineering-py/` — Vue 3 + FastAPI 前后端分离版

---

## har

要写就写全吧。我把整个 CLAUDE.md 重写，覆盖两个版本的技术栈和启动方式。



<｜DSML｜tool_calls>
<｜DSML｜invoke name="Write">
<｜DSML｜parameter name="content" string="true"># Harness Engineering

Skills & Agents 市场 + Workflow 聊天界面的前端应用。两个版本共存：

- `harness-engineering/` — Next.js 16 单体版
- `harness-engineering-py/` — Vue 3 + FastAPI 前后端分离版

---

## harness-engineering（Next.js 单体版）

### 技术栈

- **框架**: Next.js 16 (App Router)
- **语言**: TypeScript 6
- **UI**: React 19 + Tailwind CSS 3 + lucide-react 图标
- **图表**: Recharts 3
- **AI 集成**: @agentclientprotocol/sdk
- **CSS 工具**: clsx + tailwind-merge + tailwindcss-animate

### 构建 & 启动

```bash
cd harness-engineering
npm install        # node_modules ~700MB
npm run dev        # next dev，默认端口 3000，首页自动跳转 /dashboard
npm run build      # next build，生产构建
npm run start      # next start，运行生产服务
```

### 项目结构

```
harness-engineering/src/
├── app/                    # Next.js App Router
│   ├── api/
│   │   ├── chat/stream/    # SSE 流式聊天（核心路由）
│   │   ├── chat/sessions/  # 会话管理
│   │   ├── chat/permission/# 权限请求
│   │   └── engines/        # 引擎可用性检测
│   ├── agents/             # Agents 页面
│   ├── dashboard/          # Dashboard 页面
│   ├── skills/             # Skills 页面
│   └── workflow/           # Workflow 页面
├── components/             # React 组件
├── hooks/                  # use-chat-stream
├── lib/
│   ├── chat/               # 流状态、会话存储、权限队列
│   ├── engines/            # 引擎抽象层（opencode-wrapper、acp-engine、engine-factory）
│   ├── mock-data.ts
│   └── utils.ts
└── types/                  # TypeScript 类型定义
```

---

## harness-engineering-py（Vue 3 + FastAPI 前后端分离版）

### 技术栈

- **前端**: Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router
- **后端**: FastAPI + uvicorn + Pydantic + aiofiles
- **AI 集成**: 通过子进程 stdio 与 OpenCode ACP CLI 通信

### 构建 & 启动

```bash
# 后端（端口 8000）
cd harness-engineering-py/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（端口 3000，/api 代理到后端 8000）
cd harness-engineering-py/frontend
npm install
npm run dev
```

启动后访问 `http://localhost:3000`，首页自动跳转 `/skills`。

### 项目结构

```
harness-engineering-py/
├── frontend/                    # Vue 3 + Vite SPA
│   └── src/
│       ├── App.vue
│       ├── main.ts              # createApp, Pinia, Router, Element Plus
│       ├── router/index.ts      # /skills, /agents, /workflow 三条路由
│       ├── types/
│       │   ├── index.ts         # MarketItem, Skill, Agent
│       │   └── chat.ts          # ChatMessage, ChatSession, SSEEvent 等
│       ├── mock/data.ts         # 12 skills + 8 agents 静态数据
│       ├── views/
│       │   ├── SkillsView.vue
│       │   ├── AgentsView.vue
│       │   └── WorkflowView.vue
│       ├── components/
│       │   ├── layout/Navbar.vue
│       │   ├── skills/SkillCard.vue, SkillFilter.vue
│       │   ├── agents/AgentCard.vue, AgentFilter.vue
│       │   └── workflow/ChatLayout.vue, ChatSidebar.vue, ChatStream.vue,
│       │               ChatMessage.vue, ChatInput.vue, EngineInfo.vue,
│       │               PermissionCard.vue, ThoughtBlock.vue, ToolCallCard.vue
│       ├── composables/
│       │   ├── useChatStream.ts    # SSE 流式聊天
│       │   └── useMarketFilter.ts  # Skills/Agents 共用筛选
│       └── stores/
│           ├── chat.ts             # Pinia 聊天状态
│           └── engine.ts           # Pinia 引擎可用性
│
└── backend/                     # FastAPI
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
        │   ├── session_store.py       # 文件 JSON 会话 CRUD
        │   ├── stream_state.py        # 内存流状态追踪
        │   └── permission_queue.py    # 内存权限请求队列
        └── models/schemas.py     # Pydantic 模型
```

### 引擎架构

- `Engine` 抽象基类定义在 `services/engine_interface.py`
- `engine_factory.py` 管理引擎池（Map + TTL 10 分钟自动回收）
- 当前唯一实现：`OpenCodeEngineWrapper`，通过本地 OpenCode CLI 驱动
- `routers/chat.py` 通过 asyncio.Queue 实现 SSE 推送（text/thought/permission_request/error）

### 注意事项

- 路径别名：`@/*` → `./src/*`（前端）
- SSE 连接使用内存存储，重启服务后会话丢失
- 会话数据持久化在 `backend/data/chat-sessions/` 目录（JSON 文件）
- Vite dev server 自动代理 `/api/*` → `http://localhost:8000`
- 生产部署：前端 `npm run build` 产出静态文件，后端 `uvicorn` 或 gunicorn 运行
- Windows 开发环境：开启系统代理/VPN 可能导致 WebSocket 连接失败
