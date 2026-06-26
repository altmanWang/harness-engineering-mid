# 前端 — 类型定义 (Types)

## 文件

- `frontend/src/types/chat.ts` — 聊天相关类型
- `frontend/src/types/index.ts` — 市场/技能通用类型

## Chat 类型 (`types/chat.ts`)

```ts
interface PermissionOption {
  id: string
  label: string
  style: "primary" | "danger" | "default"
}

interface PermissionRequest {
  id: string
  type: string
  description: string
  detail: string
  options: PermissionOption[]
  timestamp: string
}

interface ToolCall {
  name: string
  input: string
  output?: string
}

interface ChatMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  thoughtContent?: string
  timestamp: string
  toolCalls?: ToolCall[]
  permissionRequest?: PermissionRequest
  permissionDecision?: { optionId: string; label: string }
  isStreaming?: boolean
}

interface ChatSession {
  id: string
  title: string
  engine: string
  model: string
  agentSessionId?: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
}

interface EngineAvailability {
  available: boolean
  name: string
  version?: string
  models: ModelInfo[]
  defaultModel?: string
}

interface ModelInfo {
  id: string
  name: string
}
```

## 通用类型 (`types/index.ts`)

```ts
interface MarketItem {
  id: string
  name: string
  description: string
  tags: string[]
  icon: string
  usageCount: number
  lastUsedAt: string
}

interface Skill {
  id: string
  name: string
  description: string
  tags: string[]
  fileName: string
  fileSize: number
  createdAt: string
}

type Agent = MarketItem  // Agent 复用 MarketItem 结构
```

## 关键说明

- `Agent` 是 `MarketItem` 的类型别名，复用相同结构
- `ChatMessage.role` 限定为 `"user" | "assistant" | "system"`
- `PermissionOption.style` 限定为三种预定义样式
- 所有时间戳使用 ISO 8601 字符串格式
