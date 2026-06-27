# 前端 — 类型定义 (Types)

## 文件

- `frontend/src/types/chat.ts` — 聊天相关类型
- `frontend/src/types/index.ts` — 市场/技能通用类型
- `frontend/src/types/stock.ts` — 诊股相关类型

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
  type: "chat" | "stock_diagnosis"
  title: string
  engine: string
  model: string
  agentSessionId?: string
  messages: ChatMessage[]
  diagnosis?: StockDiagnosis
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
- `ChatSession.type` 限定为 `"chat" | "stock_diagnosis"`，`diagnosis` 字段仅在 stock_diagnosis 类型时有值
- 所有时间戳使用 ISO 8601 字符串格式

## Stock 类型 (`types/stock.ts`)

```ts
interface DiagnosisResult {
  code: string
  name: string
  conclusion: "看多" | "看空" | "观望" | null
  reason: string
  close?: number
  open?: number
  pct_chg?: number
  ema20?: number
  error?: string
  source?: string
  klinePath?: string
  klineDate?: string
}

interface StockDiagnosis {
  codes: string[]
  sector?: string
  days: number
  skills: string[]
  skillNames: string[]
  initialPrompt: string
  results: DiagnosisResult[]
  successCount: number
  failedCount: number
}

interface StockSearchResult {
  code: string
  name: string
  type: string
}
```
