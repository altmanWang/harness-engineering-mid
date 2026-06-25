import type { StockDiagnosis } from './stock'

export interface PermissionOption {
  id: string
  label: string
  style: "primary" | "danger" | "default"
}

export interface PermissionRequest {
  id: string
  type: string
  description: string
  detail: string
  options: PermissionOption[]
  timestamp: string
}

export interface ToolCall {
  name: string
  input: string
  output?: string
}

export interface ChatMessage {
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

export interface ChatSession {
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

export interface EngineAvailability {
  available: boolean
  name: string
  version?: string
  models: ModelInfo[]
  defaultModel?: string
}

export interface ModelInfo {
  id: string
  name: string
}
