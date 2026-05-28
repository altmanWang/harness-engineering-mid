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

export interface PermissionDecision {
  requestId: string
  optionId: string
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
  timestamp: string
  toolCalls?: ToolCall[]
  permissionRequest?: PermissionRequest
  permissionDecision?: { optionId: string; label: string }
  isStreaming?: boolean
}

export interface ChatSession {
  id: string
  title: string
  engine: string
  model: string
  agentSessionId?: string
  messages: ChatMessage[]
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

export type SSEEvent =
  | { type: "message_start"; messageId: string }
  | { type: "message_delta"; messageId: string; content: string }
  | { type: "message_end"; messageId: string }
  | { type: "thought"; messageId: string; content: string }
  | { type: "tool_call"; messageId: string; toolName: string; input: string }
  | { type: "tool_result"; messageId: string; output: string }
  | { type: "permission_request"; messageId: string; request: PermissionRequest }
  | { type: "error"; message: string }

export interface EngineOptions {
  prompt: string
  systemPrompt?: string
  model?: string
  workingDirectory: string
  sessionId?: string
  agent?: string
}

export interface EngineResult {
  success: boolean
  output: string
  error?: string
  sessionId?: string
  stopReason?: string
}
