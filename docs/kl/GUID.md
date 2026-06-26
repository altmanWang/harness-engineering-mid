# Harness Engineering — Knowledge Base Index

> 生成时间: 2026-06-25 | 基于代码实际状态

---

## 架构总览

| 文档 | 描述 |
|------|------|
| [前端架构总览](frontend-architecture.md) | Vue 3 + Vite + Element Plus + Pinia 技术栈，路由、布局、状态管理 |
| [后端架构总览](backend-architecture.md) | FastAPI + SSE + ACP 协议，引擎池、会话存储、工作区隔离 |

## 前端模块

| 文档 | 描述 |
|------|------|
| [侧边栏 (AppSidebar)](frontend-sidebar.md) | 左侧导航栏结构、路由联动、历史会话列表、折叠逻辑 |
| [聊天流 (Chat Stream)](frontend-chat-stream.md) | useChatStream composable、SSE 事件处理、消息生命周期 |
| [视图层 (Views)](frontend-views.md) | HomeView / SkillsView / AgentsView 三个页面的结构与数据流 |
| [状态管理 (Stores)](frontend-stores.md) | chatStore (Pinia)、engineStore 的 state/actions 定义 |
| [类型定义 (Types)](frontend-types.md) | ChatMessage、ChatSession、Skill 等 TypeScript 接口 |
| [组件清单](frontend-components.md) | 19 个 Vue 组件的分类、职责与依赖关系 |

## 后端模块

| 文档 | 描述 |
|------|------|
| [聊天流 API](backend-chat-flow.md) | POST/GET/DELETE /api/chat/stream 的两步 SSE 模式 |
| [引擎抽象层](backend-engine-layer.md) | Engine 接口 → OpenCodeEngineWrapper → ACPEngine (JSON-RPC) |
| [会话存储](backend-sessions.md) | 文件 JSON 持久化、CRUD、消息追加、agentSessionId |
| [Skill 管理](backend-skills.md) | 上传/下载/加载到 worktree 的完整流程 |
| [权限队列](backend-permissions.md) | 内存注册 → SSE 推送 → 前端回调 → JSON-RPC 响应 |
| [AStockClient 模块](a-stock-client.md) | 独立 A 股 K 线数据获取库，多数据源故障切换 |

## 数据流

```
前端 (Vue 3)
  │  POST /api/chat/stream { message, sessionId, model }
  ▼
后端 chat.py
  │  get_or_create_engine() → engine_factory.py (TTL pool)
  │  engine.execute() → OpenCodeEngineWrapper → ACPEngine
  │  ACPEngine subprocess: opencode acp --cwd <worktree>
  │  JSON-RPC 2.0 over stdin/stdout (ndjson)
  ▼
前端 EventSource: GET /api/chat/stream?id=<chatId>
  │  SSE events: delta → thinking → permission_request → done/failed
  ▼
消息持久化: data/chat-sessions/{sessionId}.json
```

## 关键约定

- **路由前缀**: 所有 API 挂载在 `/api` 下
- **会话 ID 格式**: `session-{unix_ms}-{6位随机}`
- **Chat ID 格式**: `chat-{unix_ms}`
- **引擎池 TTL**: 10 分钟未使用自动回收
- **工作区隔离**: `data/worktrees/{sessionId}/.opencode/skills/`
- **Skill 加载**: ZIP 解压到 worktree 目录，`.loaded` 标记文件防重复
- **前端代理**: Vite dev server 代理 `/api` 到 `localhost:8000`
