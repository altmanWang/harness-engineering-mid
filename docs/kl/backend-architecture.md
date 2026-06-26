# 后端架构总览

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI >= 0.115.0 |
| ASGI | uvicorn[standard] >= 0.30.0 |
| 数据验证 | pydantic >= 2.0 |
| 异步 I/O | aiofiles >= 24.0.0 |
| 外部依赖 | OpenCode CLI (需在 PATH) |

## 目录结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用、CORS、路由注册
│   ├── models/
│   │   └── schemas.py             # 所有 Pydantic 模型
│   ├── routers/
│   │   ├── chat.py                # SSE 流式聊天 + 权限处理
│   │   ├── sessions.py            # 会话 CRUD
│   │   ├── engines.py             # 引擎可用性检测
│   │   └── skills.py              # Skill 上传/下载/加载
│   └── services/
│       ├── engine_interface.py    # Engine 抽象基类
│       ├── opencode_wrapper.py    # Engine 接口实现
│       ├── acp_engine.py          # ACP JSON-RPC 通信层
│       ├── engine_factory.py      # 引擎池管理 (TTL 10min)
│       ├── session_store.py       # 文件 JSON 持久化
│       ├── stream_state.py        # 内存流状态缓冲
│       ├── permission_queue.py    # 内存权限注册/解决
│       ├── worktree_manager.py    # 工作区目录隔离
│       └── skill_store.py         # Skill 元数据 + ZIP 存储
├── data/
│   ├── chat-sessions/             # 会话 JSON 文件
│   ├── skills/                    # Skill ZIP + metadata.json
│   └── worktrees/                 # 每会话隔离目录
├── a_stock_client/                # 独立 A 股 K 线库 (未 API 集成)
└── tests/
    └── test_acp_engine.py
```

## API 路由表

| Method | Path | Router | 说明 |
|--------|------|--------|------|
| `GET` | `/api/health` | inline | 健康检查 |
| `GET` | `/api/chat/sessions` | sessions | 列出所有会话 |
| `POST` | `/api/chat/sessions` | sessions | 创建会话 |
| `DELETE` | `/api/chat/sessions` | sessions | 删除会话 |
| `POST` | `/api/chat/stream` | chat | 启动聊天 (返回 chatId) |
| `GET` | `/api/chat/stream` | chat | SSE 流 (id=chatId) |
| `DELETE` | `/api/chat/stream` | chat | 取消聊天 |
| `POST` | `/api/chat/permission` | chat | 解决权限请求 |
| `GET` | `/api/engines/availability` | engines | 引擎状态 |
| `GET` | `/api/skills` | skills | Skill 列表 |
| `POST` | `/api/skills` | skills | 上传 Skill (multipart) |
| `GET` | `/api/skills/{id}/download` | skills | 下载 Skill ZIP |
| `DELETE` | `/api/skills/{id}` | skills | 删除 Skill |
| `POST` | `/api/skills/{id}/load` | skills | 加载 Skill 到 worktree |

## 引擎通信层

```
Engine (ABC)                          ← 抽象接口
  └── OpenCodeEngineWrapper           ← 实现层
        └── ACPEngine                  ← 传输层
              └── subprocess: opencode acp --cwd <worktree>
                    └── JSON-RPC 2.0 over stdin/stdout (ndjson)
```

## Pydantic 模型

| 模型 | 关键字段 |
|------|---------|
| `ChatSession` | id, title, engine, model, agentSessionId, messages[], createdAt, updatedAt |
| `ChatMessage` | id, role, content, thoughtContent, timestamp, toolCalls[], permissionRequest, isStreaming |
| `PermissionRequest` | id, type, description, detail, options[], timestamp |
| `PermissionOption` | id, label, style |
| `EngineAvailability` | available, name, version, models[], defaultModel |
| `ModelInfo` | id, name |
| `SendMessageRequest` | message, model, sessionId, agentSessionId? |

## 核心服务

| 服务 | 职责 |
|------|------|
| `engine_factory.py` | 引擎池 (Map + TTL 600s, 60s 清理) |
| `session_store.py` | 异步 JSON 文件会话持久化 |
| `stream_state.py` | 内存流缓冲 (content buffer + status) |
| `permission_queue.py` | 内存权限 request_id → engine 映射 |
| `worktree_manager.py` | `data/worktrees/{sid}/.opencode/skills/` 隔离 |
| `skill_store.py` | Skill 元数据 JSON + ZIP 存储 + worktree 解压 |

## 开发命令

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
