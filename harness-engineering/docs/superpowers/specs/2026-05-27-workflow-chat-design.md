# 工作流 Chat 对话框 Design Spec

## 概述

在 harness-engineering 平台新增工作流功能，通过 ACP（Agent Client Protocol）对接本地 Claude Code 和 OpenCode，实现完整的 Chat 对话框，支持流式消息、工具调用展示、权限交互请求，以及多会话管理。

## 技术栈

- `@agentclientprotocol/sdk` — ACP 协议通信
- SSE（Server-Sent Events）— 流式消息推送
- 文件系统 JSON — 会话持久化

## 整体架构

```
用户消息 → Engine Factory → 启动 Agent 进程 (ACP/stdio)
                ↓
         ACP 协议握手 (JSON-RPC over stdio)
                ↓
         创建 Session → 发送 Prompt
                ↓
         事件流 ──→ message (流式文本)
              ├──→ thought (思考过程)
              ├──→ tool_call (工具调用)
              └──→ permission_request (权限请求，交互式)
                     ↓
               Chat UI 展示权限卡片
               用户点击选项
                     ↓
               ACP 协议回传 decision
               Agent 继续或终止执行
```

## 页面与路由

### 新增路由

- `/workflow` — Chat 工作流页面

### 导航栏更新

顶部导航新增：`Dashboard | Skills | Agents | 工作流`

### Dashboard 新增卡片

在统计卡片下方新增"工作流"入口卡片，包含标题、描述和"进入工作流"链接。

### /workflow 页面布局

```
┌──────────┬────────────────────────────────┐
│ 会话列表  │  Chat 主区域                    │
│          │  ┌──────────────────────────┐  │
│ 新建会话  │  │ Agent: Claude Code       │  │
│ 会话1    │  │ Model: claude-sonnet-4... │  │
│ 会话2    │  ├──────────────────────────┤  │
│          │  │ 消息流（流式渲染）          │  │
│          │  │ - 用户消息                │  │
│          │  │ - AI 回复（流式）          │  │
│          │  │ - 工具调用卡片             │  │
│          │  │ - 权限请求卡片（动态选项）   │  │
│          │  ├──────────────────────────┤  │
│          │  │ 输入框 + 发送按钮          │  │
│ ──────── │  └──────────────────────────┘  │
│ Agent选择 │                                │
│ 模型选择  │                                │
└──────────┴────────────────────────────────┘
```

## 前端组件

```
src/components/workflow/
├── chat-layout.tsx        # 左右分栏布局
├── chat-sidebar.tsx       # 会话列表侧边栏（新建/删除/切换会话/Agent选择/模型选择）
├── chat-message.tsx       # 单条消息渲染（用户右侧气泡/AI左侧流式）
├── chat-input.tsx         # 输入框 + 发送，执行中禁用
├── chat-stream.tsx        # 消息流区域，自动滚动
├── permission-card.tsx    # 权限请求卡片，动态渲染 options
├── tool-call-card.tsx     # 工具调用折叠展示
└── engine-info.tsx        # Agent 名称 + 当前模型显示
```

### 权限请求交互

权限选项由 Agent 动态返回，前端不预设。用户点击选项后锁定卡片，回传决策，Agent 继续执行。

```typescript
interface PermissionOption {
  id: string
  label: string           // "允许" / "始终允许" / "拒绝" 等
  style: "primary" | "danger" | "default"
}

interface PermissionRequest {
  id: string
  type: string            // Agent 返回的操作类型
  description: string
  detail: string
  options: PermissionOption[]  // 动态渲染
  timestamp: string
}
```

## 后端 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat/stream` | POST | 发送消息，启动 Agent 执行 |
| `/api/chat/stream` | GET | 建立 SSE 连接，接收流式事件 |
| `/api/chat/stream` | DELETE | 取消当前执行 |
| `/api/chat/permission` | POST | 回传权限决策（requestId + optionId） |
| `/api/chat/sessions` | GET | 获取会话列表 |
| `/api/chat/sessions` | POST | 创建新会话 |
| `/api/chat/sessions/[id]` | DELETE | 删除会话 |
| `/api/engines/availability` | GET | 检测本地可用 Agent 及模型信息 |

### SSE 事件类型

```typescript
type ChatEvent =
  | { type: "message_start"; messageId: string }
  | { type: "message_delta"; messageId: string; content: string }
  | { type: "message_end"; messageId: string }
  | { type: "thought"; messageId: string; content: string }
  | { type: "tool_call"; messageId: string; toolName: string; input: string }
  | { type: "tool_result"; messageId: string; output: string }
  | { type: "permission_request"; messageId: string; request: PermissionRequest }
  | { type: "error"; message: string }
```

## 数据模型

```typescript
interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  toolCalls?: ToolCall[]
  permissionRequest?: PermissionRequest
  permissionDecision?: { optionId: string; label: string }
}

interface ToolCall {
  name: string
  input: string
  output?: string
}

interface ChatSession {
  id: string
  title: string
  engine: string         // "claude-code" | "opencode"
  model: string          // 当前模型 ID
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
}

interface EngineAvailability {
  available: boolean
  name: string           // "Claude Code" | "OpenCode"
  version?: string
  models: ModelInfo[]
  defaultModel?: string
}

interface ModelInfo {
  id: string
  name: string
}
```

## 本地存储

```
data/
├── chat-sessions/
│   ├── session-1.json    # ChatSession JSON
│   └── session-2.json
└── engine-state.json     # { defaultEngine, defaultModel }
```

## Agent 检测

启动时和页面加载时检测：

1. 检查 PATH 中是否存在 `claude` / `opencode` 命令
2. Windows 额外检查 `%APPDATA%\npm\claude.cmd` 等常见路径
3. 执行 `--version` 验证可用
4. 通过 ACP 获取可用模型列表
5. Chat 顶部展示当前 Agent + 默认模型

## Engine 管理

```typescript
class EngineFactory {
  private engines: Map<string, ACPEngine>
  async getEngine(type: "claude-code" | "opencode"): Promise<ACPEngine>
  async releaseEngine(type: string): Promise<void>
  async detectAvailability(): Promise<EngineAvailability[]>
}
```

- 连接池复用，10 分钟空闲自动关闭
- 切换 Agent 时关闭旧实例、创建新实例
