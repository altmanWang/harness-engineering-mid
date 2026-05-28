# 工作流 Chat 对话框 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a workflow chat page that connects to local Claude Code and OpenCode via ACP/SDK, with interactive permission handling and multi-session support.

**Architecture:** Claude Code uses `@anthropic-ai/claude-agent-sdk` directly; OpenCode uses `@agentclientprotocol/sdk` via ACP stdio protocol. Both engines emit stream events through a unified Engine interface. Permission requests are held as pending promises until the user responds via the UI, then resolved back to the agent. SSE streams events to the frontend. Sessions persist as JSON files.

**Tech Stack:** `@anthropic-ai/claude-agent-sdk`, `@agentclientprotocol/sdk`, SSE (Server-Sent Events), React hooks, Tailwind CSS

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/types/chat.ts` | Chat-specific types: ChatMessage, ChatSession, PermissionRequest, etc. |
| `src/lib/engines/engine-interface.ts` | Abstract Engine interface all wrappers implement |
| `src/lib/engines/acp-engine.ts` | ACP protocol engine for OpenCode (stdio JSON-RPC) |
| `src/lib/engines/opencode-wrapper.ts` | OpenCode engine wrapper using ACP |
| `src/lib/engines/claude-code-wrapper.ts` | Claude Code engine wrapper using SDK |
| `src/lib/engines/engine-factory.ts` | Engine creation, pooling, and agent detection |
| `src/lib/chat/session-store.ts` | File-based chat session CRUD |
| `src/lib/chat/permission-queue.ts` | Pending permission request resolver map |
| `src/lib/chat/stream-state.ts` | Active stream state tracking |
| `src/app/api/chat/stream/route.ts` | POST send message, GET SSE stream, DELETE cancel |
| `src/app/api/chat/permission/route.ts` | POST resolve permission decision |
| `src/app/api/chat/sessions/route.ts` | GET list, POST create, DELETE remove sessions |
| `src/app/api/engines/availability/route.ts` | GET detect available agents + models |
| `src/hooks/use-chat-stream.ts` | React hook for SSE connection and message state |
| `src/components/workflow/chat-layout.tsx` | Left-right split layout |
| `src/components/workflow/chat-sidebar.tsx` | Session list + engine/model selection |
| `src/components/workflow/chat-message.tsx` | Single message rendering (user/assistant/tool/permission) |
| `src/components/workflow/chat-input.tsx` | Text input + send button |
| `src/components/workflow/chat-stream.tsx` | Message scroll area |
| `src/components/workflow/permission-card.tsx` | Dynamic permission options |
| `src/components/workflow/tool-call-card.tsx` | Tool call display |
| `src/components/workflow/engine-info.tsx` | Current agent + model display |
| `src/app/workflow/page.tsx` | Workflow page composing all components |
| `src/components/layout/navbar.tsx` | Updated: add workflow nav item |
| `src/components/dashboard/workflow-card.tsx` | Dashboard entry card for workflow |
| `src/app/dashboard/page.tsx` | Updated: include workflow card |

---

### Task 1: Install Dependencies and Update Types

**Files:**
- Modify: `package.json`
- Create: `src/types/chat.ts`

- [ ] **Step 1: Install new dependencies**

```bash
cd D:/codes/harness/harness-engineering
npm install @agentclientprotocol/sdk @anthropic-ai/claude-agent-sdk
```

- [ ] **Step 2: Create src/types/chat.ts**

```typescript
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
```

- [ ] **Step 3: Commit**

```bash
git add package.json package-lock.json src/types/chat.ts
git commit -m "feat: add ACP/SDK dependencies and chat type definitions"
```

---

### Task 2: Engine Interface and ACP Engine

**Files:**
- Create: `src/lib/engines/engine-interface.ts`
- Create: `src/lib/engines/acp-engine.ts`

- [ ] **Step 1: Create src/lib/engines/engine-interface.ts**

```typescript
import type { EngineOptions, EngineResult } from "@/types/chat"
import type { EventEmitter } from "events"

export interface Engine {
  getName(): string
  execute(options: EngineOptions): Promise<EngineResult>
  cancel(): void
  isAvailable(): Promise<boolean>
  on(event: "stream", listener: (evt: EngineStreamEvent) => void): this
  on(event: string, listener: (...args: any[]) => void): this
}

export interface EngineStreamEvent {
  type: "text" | "thought" | "tool" | "permission_request" | "error"
  content: string
  metadata?: any
}
```

- [ ] **Step 2: Create src/lib/engines/acp-engine.ts**

```typescript
import { spawn, ChildProcess } from "child_process"
import { Writable, Readable } from "node:stream"
import { EventEmitter } from "events"
import {
  ClientSideConnection,
  ndJsonStream,
  PROTOCOL_VERSION,
} from "@agentclientprotocol/sdk"
import type {
  RequestPermissionRequest,
  RequestPermissionResponse,
  SessionNotification,
  StopReason,
  SessionUpdate,
  Client,
  Agent,
} from "@agentclientprotocol/sdk"
import type { PermissionOption } from "@/types/chat"

export interface ACPEngineConfig {
  engineType: string
  command: string
  workingDirectory: string
  agentName?: string
  model?: string
  args?: string[]
  env?: Record<string, string>
}

export class ACPEngine extends EventEmitter {
  private process: ChildProcess | null = null
  private connection: ClientSideConnection | null = null
  private sessionId: string | null = null
  private initialized = false
  private availableModels: Array<{ modelId: string; name: string }> = []

  // Pending permission resolver — set by wrapper when permission is requested
  private permissionResolver: ((response: RequestPermissionResponse) => void) | null = null

  constructor(private config: ACPEngineConfig) {
    super()
  }

  async start(): Promise<void> {
    const args = this.buildCommandArgs()
    console.log(`[${this.config.engineType}] spawning: ${this.config.command} ${args.join(" ")}`)

    this.process = spawn(this.config.command, args, {
      cwd: this.config.workingDirectory,
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        PATH: `${process.env.PATH}:/root/.local/bin:/usr/local/bin`,
        ...this.config.env,
      },
    })

    if (!this.process.stdin || !this.process.stdout || !this.process.stderr) {
      throw new Error(`Failed to create ${this.config.engineType} process streams`)
    }

    this.process.stderr.on("data", (data: Buffer) => {
      console.error(`[${this.config.engineType} stderr] ${data.toString().trim()}`)
    })

    this.process.on("exit", (code, signal) => {
      this.cleanup(`${this.config.engineType} process exited (code=${code}, signal=${signal})`)
    })

    this.process.on("error", (error) => {
      this.cleanup(`${this.config.engineType} process error: ${error.message}`)
    })

    const output = Writable.toWeb(this.process.stdin) as WritableStream<Uint8Array>
    const input = Readable.toWeb(this.process.stdout) as ReadableStream<Uint8Array>
    const stream = ndJsonStream(output, input)

    const engine = this
    this.connection = new ClientSideConnection((_agent: Agent): Client => ({
      async requestPermission(params: RequestPermissionRequest): Promise<RequestPermissionResponse> {
        // Emit permission event for UI — do NOT auto-approve
        engine.emit("permission", params)

        // Wait for user decision from the UI
        const decision = await new Promise<RequestPermissionResponse>((resolve) => {
          engine.permissionResolver = resolve
        })
        engine.permissionResolver = null
        return decision
      },

      async sessionUpdate(params: SessionNotification): Promise<void> {
        engine.handleSessionUpdate(params.update)
      },

      async extMethod(): Promise<Record<string, unknown>> {
        return {}
      },

      async extNotification(): Promise<void> {},
    }), stream)

    await this.initialize()
  }

  resolvePermission(optionId: string): void {
    if (this.permissionResolver) {
      this.permissionResolver({ outcome: { outcome: "selected", optionId } })
    }
  }

  private buildCommandArgs(): string[] {
    const args: string[] = []
    switch (this.config.engineType) {
      case "opencode":
        args.push("acp", "--cwd", this.config.workingDirectory)
        break
      default:
        throw new Error(`Unknown engine type: ${this.config.engineType}`)
    }
    if (this.config.args) args.push(...this.config.args)
    return args
  }

  private async initialize(): Promise<void> {
    if (!this.connection) throw new Error("No connection")
    await this.connection.initialize({
      protocolVersion: PROTOCOL_VERSION,
      clientInfo: { name: "harness-engineering", version: "1.0.0" },
      clientCapabilities: {
        fs: { readTextFile: true, writeTextFile: true },
        terminal: true,
      },
    })
    this.initialized = true
  }

  async createSession(): Promise<string> {
    if (!this.initialized || !this.connection) throw new Error("Not initialized")
    const result = await this.connection.newSession({
      cwd: this.config.workingDirectory,
      mcpServers: [],
    })
    this.sessionId = result.sessionId
    this.availableModels = (result.models?.availableModels as any[]) || []
    return this.sessionId!
  }

  async resumeSession(sessionId: string): Promise<string> {
    if (!this.initialized || !this.connection) throw new Error("Not initialized")
    const result = await this.connection.loadSession({ sessionId, cwd: this.config.workingDirectory, mcpServers: [] })
    this.sessionId = sessionId
    this.availableModels = (result.models?.availableModels as any[]) || this.availableModels
    return this.sessionId
  }

  async sendPrompt(prompt: string): Promise<StopReason> {
    if (!this.sessionId || !this.connection) throw new Error("No active session")
    const result = await this.connection.prompt({
      sessionId: this.sessionId,
      prompt: [{ type: "text", text: prompt }],
    })
    return result.stopReason
  }

  async setModel(modelId: string): Promise<void> {
    if (!this.sessionId || !this.connection) throw new Error("No active session")
    await this.connection.unstable_setSessionModel({ sessionId: this.sessionId, modelId })
  }

  getAvailableModels(): Array<{ modelId: string; name: string }> {
    return this.availableModels
  }

  cancelSession(): void {
    if (this.sessionId && this.connection) {
      this.connection.cancel({ sessionId: this.sessionId }).catch(() => {})
    }
  }

  stop(): void {
    if (this.process) {
      this.process.kill()
      this.cleanup()
    }
  }

  private handleSessionUpdate(update: SessionUpdate): void {
    switch (update.sessionUpdate) {
      case "agent_message_chunk":
        this.emit("agent-message", (update as any).content)
        break
      case "agent_thought_chunk":
        this.emit("agent-thought", (update as any).content)
        break
      case "tool_call":
        this.emit("tool-call", {
          id: (update as any).toolCallId,
          title: (update as any).title,
          status: (update as any).status,
          kind: (update as any).kind,
          content: (update as any).content,
          rawInput: (update as any).rawInput,
        })
        break
      case "tool_call_update":
        this.emit("tool-call-update", {
          id: (update as any).toolCallId,
          title: (update as any).title,
          status: (update as any).status,
          content: (update as any).content,
          rawInput: (update as any).rawInput,
          rawOutput: (update as any).rawOutput,
        })
        break
    }
  }

  private cleanup(reason?: string): void {
    this.process = null
    this.connection = null
    this.sessionId = null
    this.initialized = false
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/engines/engine-interface.ts src/lib/engines/acp-engine.ts
git commit -m "feat: add engine interface and ACP engine with interactive permission handling"
```

---

### Task 3: Engine Wrappers (Claude Code + OpenCode)

**Files:**
- Create: `src/lib/engines/opencode-wrapper.ts`
- Create: `src/lib/engines/claude-code-wrapper.ts`

- [ ] **Step 1: Create src/lib/engines/opencode-wrapper.ts**

```typescript
import { EventEmitter } from "events"
import { ACPEngine, ACPEngineConfig } from "./acp-engine"
import type { Engine, EngineStreamEvent } from "./engine-interface"
import type { EngineOptions, EngineResult, PermissionOption } from "@/types/chat"

export class OpenCodeEngineWrapper extends EventEmitter implements Engine {
  private engine: ACPEngine | null = null
  private currentSessionId: string | null = null
  private streaming = false
  private collectedOutput = ""
  private seenToolIds = new Set<string>()

  getName(): string {
    return "opencode"
  }

  async isAvailable(): Promise<boolean> {
    try {
      const { execSync } = require("child_process")
      if (process.platform === "win32") {
        execSync("where opencode", { stdio: "ignore" })
      } else {
        execSync("command -v opencode", { stdio: "ignore", shell: "/bin/bash" })
      }
      return true
    } catch {
      return false
    }
  }

  async execute(options: EngineOptions): Promise<EngineResult> {
    this.seenToolIds.clear()
    this.collectedOutput = ""

    const canReuse = options.sessionId && this.engine && this.currentSessionId === options.sessionId
    if (!canReuse) {
      if (this.engine) {
        try { this.engine.stop() } catch {}
      }
      const config: ACPEngineConfig = {
        engineType: "opencode",
        command: "opencode",
        workingDirectory: options.workingDirectory || process.cwd(),
        agentName: options.agent,
        model: options.model,
      }
      this.engine = new ACPEngine(config)
      this.setupEngineEvents()
      await this.engine.start()

      if (options.sessionId) {
        this.currentSessionId = await this.engine.resumeSession(options.sessionId)
      } else {
        this.currentSessionId = await this.engine.createSession()
      }
    }

    const engine = this.engine!
    if (options.model) {
      try {
        await engine.setModel(options.model)
      } catch (err: any) {
        this.emit("stream", { type: "error", content: `模型不可用: ${err.message}` } as EngineStreamEvent)
        return { success: false, output: "", error: err.message }
      }
    }

    this.streaming = true
    try {
      const stopReason = await engine.sendPrompt(options.prompt)
      this.streaming = false
      const isSuccess = !stopReason || stopReason === "end_turn"
      return {
        success: isSuccess,
        output: this.collectedOutput.trim(),
        sessionId: this.currentSessionId ?? undefined,
        stopReason: stopReason ?? undefined,
      }
    } catch (error) {
      this.streaming = false
      return {
        success: false,
        output: this.collectedOutput.trim(),
        error: error instanceof Error ? error.message : String(error),
      }
    }
  }

  // Resolve a pending permission request from the UI
  resolvePermission(optionId: string): void {
    if (this.engine) {
      this.engine.resolvePermission(optionId)
    }
  }

  cancel(): void {
    if (this.engine) {
      this.engine.cancelSession()
      this.engine.stop()
      this.engine = null
    }
  }

  getAvailableModels(): Array<{ modelId: string; name: string }> {
    return this.engine?.getAvailableModels() || []
  }

  private setupEngineEvents(): void {
    if (!this.engine) return

    this.engine.on("agent-message", (content) => {
      if (!this.streaming) return
      const text = this.extractText(content)
      if (text) {
        this.collectedOutput += text
        this.emit("stream", { type: "text", content: text } as EngineStreamEvent)
      }
    })

    this.engine.on("agent-thought", (content) => {
      if (!this.streaming) return
      const text = this.extractText(content)
      if (text) {
        this.emit("stream", { type: "thought", content: text } as EngineStreamEvent)
      }
    })

    this.engine.on("tool-call", (toolCall) => {
      if (!this.streaming) return
      const toolId = toolCall.id || ""
      if (toolId && !this.seenToolIds.has(toolId)) {
        this.seenToolIds.add(toolId)
        const formatted = this.formatToolCall(toolCall)
        this.collectedOutput += formatted
        this.emit("stream", { type: "text", content: formatted, metadata: toolCall } as EngineStreamEvent)
      }
    })

    this.engine.on("tool-call-update", (toolUpdate) => {
      if (!this.streaming) return
      if (toolUpdate.status === "completed" || toolUpdate.status === "failed") {
        const output = this.extractToolOutput(toolUpdate.rawOutput)
        if (output) {
          const formatted = `\n\`\`\`\n${output}\n\`\`\`\n`
          this.collectedOutput += formatted
          this.emit("stream", { type: "text", content: formatted, metadata: toolUpdate } as EngineStreamEvent)
        }
      }
    })

    this.engine.on("permission", (params) => {
      // Forward permission request to the UI via stream event
      const options: PermissionOption[] = (params.options || []).map((o: any) => ({
        id: o.optionId || o.id,
        label: o.label || o.optionId || o.id,
        style: this.inferOptionStyle(o.optionId || o.id),
      }))
      const request = {
        id: params.id || `perm-${Date.now()}`,
        type: params.type || "unknown",
        description: params.description || params.title || "",
        detail: params.detail || params.message || JSON.stringify(params, null, 2),
        options,
        timestamp: new Date().toISOString(),
      }
      this.emit("stream", {
        type: "permission_request",
        content: JSON.stringify(request),
        metadata: request,
      } as EngineStreamEvent)
    })

    this.engine.on("error", (error) => {
      this.emit("stream", {
        type: "error",
        content: error instanceof Error ? error.message : String(error),
      } as EngineStreamEvent)
    })
  }

  private extractText(content: any): string {
    if (typeof content === "string") return content
    if (content && typeof content === "object") {
      if (content.type === "text" && content.text) return content.text
      if (content.text) return content.text
      if (content.content) return content.content
    }
    return ""
  }

  private extractToolOutput(raw: any): string {
    if (typeof raw === "string") return raw
    if (!raw || typeof raw !== "object") return ""
    if ("output" in raw && typeof raw.output === "string") return raw.output
    return JSON.stringify(raw)
  }

  private formatToolCall(toolCall: any): string {
    const title = toolCall.title || "Tool"
    return `\n\n**🔧 ${title}**\n`
  }

  private inferOptionStyle(id: string): "primary" | "danger" | "default" {
    const lower = id.toLowerCase()
    if (lower.includes("deny") || lower.includes("reject") || lower.includes("block")) return "danger"
    if (lower.includes("allow") || lower.includes("accept") || lower.includes("always")) return "primary"
    return "default"
  }
}
```

- [ ] **Step 2: Create src/lib/engines/claude-code-wrapper.ts**

```typescript
import { EventEmitter } from "events"
import type { Engine, EngineStreamEvent } from "./engine-interface"
import type { EngineOptions, EngineResult, PermissionOption } from "@/types/chat"

export class ClaudeCodeEngineWrapper extends EventEmitter implements Engine {
  private abortController: AbortController | null = null

  getName(): string {
    return "claude-code"
  }

  async isAvailable(): Promise<boolean> {
    try {
      await import("@anthropic-ai/claude-agent-sdk")
      return true
    } catch {
      return false
    }
  }

  cancel(): void {
    try { this.abortController?.abort() } catch {}
  }

  async execute(options: EngineOptions): Promise<EngineResult> {
    this.abortController = new AbortController()
    let accumulated = ""

    try {
      const { query } = await import("@anthropic-ai/claude-agent-sdk")

      const userPrompt = options.systemPrompt?.trim()
        ? `# System Instructions\n${options.systemPrompt}\n\n---\n\n# Task\n${options.prompt}`
        : options.prompt

      const sdkOptions: Record<string, unknown> = {
        cwd: options.workingDirectory || process.cwd(),
        model: options.model || undefined,
        permissionMode: "default",
        abortController: this.abortController,
        maxTurns: 200,
      }

      if (options.sessionId) {
        (sdkOptions as any).resume = options.sessionId
      }

      // Hook tool usage for permission interception
      sdkOptions.canUseTool = async (toolName: string, input: unknown) => {
        const request = {
          id: `perm-${Date.now()}`,
          type: toolName,
          description: `Tool: ${toolName}`,
          detail: JSON.stringify(input, null, 2),
          options: [
            { id: "allow", label: "允许", style: "primary" as const },
            { id: "allow-always", label: "始终允许", style: "primary" as const },
            { id: "deny", label: "拒绝", style: "danger" as const },
          ],
          timestamp: new Date().toISOString(),
        }

        // Emit permission request to UI
        this.emit("stream", {
          type: "permission_request",
          content: JSON.stringify(request),
          metadata: request,
        } as EngineStreamEvent)

        // Wait for user decision
        const decision = await new Promise<string>((resolve) => {
          pendingPermissionResolvers.set(request.id, resolve)
        })

        if (decision === "deny") {
          return { behavior: "deny" as const }
        }
        return { behavior: "allow" as const, updatedInput: input }
      }

      const iter = query({ prompt: userPrompt, options: sdkOptions as any })
      let lastBlockWasTool = false

      for await (const msg of iter) {
        if (msg.type === "assistant") {
          const snapshot = this.extractText(msg as any)
          if (snapshot) {
            let piece = snapshot.startsWith(accumulated) ? snapshot.slice(accumulated.length) : snapshot
            if (lastBlockWasTool && !piece.startsWith("\n")) piece = `\n\n${piece}`
            accumulated += piece
            lastBlockWasTool = false
            this.emit("stream", { type: "text", content: piece } as EngineStreamEvent)
          }
        } else if (msg.type === "stream_event") {
          const ev = (msg as any).event
          if (ev?.delta?.type === "text_delta" && typeof ev.delta.text === "string") {
            const piece = ev.delta.text
            accumulated += piece
            lastBlockWasTool = false
            this.emit("stream", { type: "text", content: piece } as EngineStreamEvent)
          }
          if (ev?.delta?.type === "thinking_delta" && typeof ev.delta.thinking === "string") {
            this.emit("stream", { type: "thought", content: ev.delta.thinking } as EngineStreamEvent)
          }
          if (ev?.content_block?.type === "tool_use") {
            const toolName = ev.content_block.name || "tool"
            const formatted = `\n\n**🔧 ${toolName}**\n`
            accumulated += formatted
            lastBlockWasTool = true
            this.emit("stream", { type: "text", content: formatted } as EngineStreamEvent)
          }
        } else if (msg.type === "result") {
          if ((msg as any).session_id) {
            return {
              success: msg.subtype === "success",
              output: accumulated || (msg as any).result || "",
              sessionId: (msg as any).session_id,
            }
          }
          return {
            success: msg.subtype === "success",
            output: accumulated,
            error: msg.subtype !== "success" ? "Execution failed" : undefined,
          }
        }
      }

      return { success: true, output: accumulated }
    } catch (error) {
      return {
        success: false,
        output: accumulated,
        error: error instanceof Error ? error.message : String(error),
      }
    }
  }

  // Resolve a pending permission request
  static resolvePermission(requestId: string, optionId: string): void {
    const resolver = pendingPermissionResolvers.get(requestId)
    if (resolver) {
      resolver(optionId)
      pendingPermissionResolvers.delete(requestId)
    }
  }

  private extractText(msg: any): string {
    if (typeof msg === "string") return msg
    if (msg?.message?.content) {
      const blocks = Array.isArray(msg.message.content) ? msg.message.content : [msg.message.content]
      return blocks
        .filter((b: any) => b.type === "text" && typeof b.text === "string")
        .map((b: any) => b.text)
        .join("")
    }
    return ""
  }
}

// Module-level map for pending permission resolvers
const pendingPermissionResolvers = new Map<string, (optionId: string) => void>()

export { pendingPermissionResolvers }
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/engines/opencode-wrapper.ts src/lib/engines/claude-code-wrapper.ts
git commit -m "feat: add OpenCode and Claude Code engine wrappers with interactive permissions"
```

---

### Task 4: Engine Factory and Agent Detection

**Files:**
- Create: `src/lib/engines/engine-factory.ts`

- [ ] **Step 1: Create src/lib/engines/engine-factory.ts**

```typescript
import { OpenCodeEngineWrapper } from "./opencode-wrapper"
import { ClaudeCodeEngineWrapper } from "./claude-code-wrapper"
import type { Engine } from "./engine-interface"
import type { EngineAvailability, ModelInfo } from "@/types/chat"

export type EngineType = "claude-code" | "opencode"

const enginePool = new Map<string, { engine: Engine; engineType: EngineType; lastUsed: number }>()
const ENGINE_POOL_TTL = 10 * 60 * 1000

setInterval(() => {
  const now = Date.now()
  for (const [key, entry] of enginePool) {
    if (now - entry.lastUsed > ENGINE_POOL_TTL) {
      if (typeof (entry.engine as any).cancel === "function") {
        (entry.engine as any).cancel()
      }
      enginePool.delete(key)
    }
  }
}, 60_000)

export async function getOrCreateEngine(type: EngineType, sessionKey?: string): Promise<Engine | null> {
  if (sessionKey) {
    const cached = enginePool.get(sessionKey)
    if (cached) {
      if (cached.engineType !== type) {
        if (typeof (cached.engine as any).cancel === "function") {
          (cached.engine as any).cancel()
        }
        enginePool.delete(sessionKey)
      } else {
        cached.lastUsed = Date.now()
        return cached.engine
      }
    }
  }

  const engine = await createEngine(type)
  if (engine && sessionKey) {
    enginePool.set(sessionKey, { engine, engineType: type, lastUsed: Date.now() })
  }
  return engine
}

export async function createEngine(type: EngineType): Promise<Engine | null> {
  switch (type) {
    case "claude-code": {
      const engine = new ClaudeCodeEngineWrapper()
      if (!(await engine.isAvailable())) return null
      return engine
    }
    case "opencode": {
      const engine = new OpenCodeEngineWrapper()
      if (!(await engine.isAvailable())) return null
      return engine
    }
    default:
      return null
  }
}

export async function detectEngines(): Promise<EngineAvailability[]> {
  const results: EngineAvailability[] = []

  // Check Claude Code
  const ccEngine = new ClaudeCodeEngineWrapper()
  const ccAvailable = await ccEngine.isAvailable()
  results.push({
    available: ccAvailable,
    name: "Claude Code",
    models: ccAvailable ? [
      { id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6" },
      { id: "claude-haiku-4-5", name: "Claude Haiku 4.5" },
    ] : [],
    defaultModel: "claude-sonnet-4-6",
  })

  // Check OpenCode
  const ocEngine = new OpenCodeEngineWrapper()
  const ocAvailable = await ocEngine.isAvailable()
  results.push({
    available: ocAvailable,
    name: "OpenCode",
    models: ocAvailable ? [
      { id: "default", name: "Default Model" },
    ] : [],
    defaultModel: "default",
  })

  return results
}

export async function isEngineAvailable(type: EngineType): Promise<boolean> {
  const engine = await createEngine(type)
  return engine !== null
}
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/engines/engine-factory.ts
git commit -m "feat: add engine factory with pooling and agent detection"
```

---

### Task 5: Chat Backend - Session Store, Permission Queue, Stream State

**Files:**
- Create: `src/lib/chat/session-store.ts`
- Create: `src/lib/chat/permission-queue.ts`
- Create: `src/lib/chat/stream-state.ts`

- [ ] **Step 1: Create src/lib/chat/session-store.ts**

```typescript
import { readFile, writeFile, mkdir, unlink } from "fs/promises"
import { existsSync } from "fs"
import { resolve } from "path"
import type { ChatSession, ChatMessage } from "@/types/chat"

const SESSIONS_DIR = resolve(process.cwd(), "data", "chat-sessions")

async function ensureDir(): Promise<void> {
  if (!existsSync(SESSIONS_DIR)) {
    await mkdir(SESSIONS_DIR, { recursive: true })
  }
}

function sessionPath(id: string): string {
  return resolve(SESSIONS_DIR, `${id}.json`)
}

export async function listSessions(): Promise<ChatSession[]> {
  await ensureDir()
  const { readdir } = await import("fs/promises")
  const files = await readdir(SESSIONS_DIR)
  const sessions: ChatSession[] = []
  for (const file of files) {
    if (!file.endsWith(".json")) continue
    try {
      const content = await readFile(resolve(SESSIONS_DIR, file), "utf-8")
      sessions.push(JSON.parse(content))
    } catch {}
  }
  return sessions.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
}

export async function getSession(id: string): Promise<ChatSession | null> {
  try {
    const content = await readFile(sessionPath(id), "utf-8")
    return JSON.parse(content)
  } catch {
    return null
  }
}

export async function saveSession(session: ChatSession): Promise<void> {
  await ensureDir()
  session.updatedAt = new Date().toISOString()
  await writeFile(sessionPath(session.id), JSON.stringify(session, null, 2), "utf-8")
}

export async function deleteSession(id: string): Promise<void> {
  try { await unlink(sessionPath(id)) } catch {}
}

export async function appendMessage(sessionId: string, message: ChatMessage): Promise<void> {
  const session = await getSession(sessionId)
  if (!session) return
  session.messages.push(message)
  // Auto-title from first user message
  if (!session.title && message.role === "user" && message.content) {
    session.title = message.content.slice(0, 50) + (message.content.length > 50 ? "..." : "")
  }
  await saveSession(session)
}

export async function updateMessage(sessionId: string, messageId: string, updates: Partial<ChatMessage>): Promise<void> {
  const session = await getSession(sessionId)
  if (!session) return
  const idx = session.messages.findIndex((m) => m.id === messageId)
  if (idx >= 0) {
    session.messages[idx] = { ...session.messages[idx], ...updates }
    await saveSession(session)
  }
}
```

- [ ] **Step 2: Create src/lib/chat/permission-queue.ts**

```typescript
import type { OpenCodeEngineWrapper } from "@/lib/engines/opencode-wrapper"
import { ClaudeCodeEngineWrapper, pendingPermissionResolvers } from "@/lib/engines/claude-code-wrapper"

// Map of pending permission requests: requestId -> { engine, engineType, sessionId }
const pendingPermissions = new Map<string, {
  engineType: "claude-code" | "opencode"
  engine: any
}>()

export function registerPendingPermission(
  requestId: string,
  engineType: "claude-code" | "opencode",
  engine: any,
): void {
  pendingPermissions.set(requestId, { engineType, engine })
}

export function resolvePermission(requestId: string, optionId: string): boolean {
  const entry = pendingPermissions.get(requestId)
  if (!entry) return false

  if (entry.engineType === "opencode") {
    // OpenCode: resolve via ACP engine
    const ocEngine = entry.engine as OpenCodeEngineWrapper
    ocEngine.resolvePermission(optionId)
  } else {
    // Claude Code: resolve via static method
    ClaudeCodeEngineWrapper.resolvePermission(requestId, optionId)
  }

  pendingPermissions.delete(requestId)
  return true
}
```

- [ ] **Step 3: Create src/lib/chat/stream-state.ts**

```typescript
interface StreamState {
  chatId: string
  frontendSessionId: string
  engine: string
  streamContent: string
  status: "running" | "completed" | "failed" | "killed"
}

const streams = new Map<string, StreamState>()

export function registerStream(chatId: string, frontendSessionId: string, engine: string): void {
  streams.set(chatId, { chatId, frontendSessionId, engine, streamContent: "", status: "running" })
}

export function appendStreamContent(chatId: string, content: string): void {
  const state = streams.get(chatId)
  if (state) state.streamContent += content
}

export function setStreamStatus(chatId: string, status: StreamState["status"]): void {
  const state = streams.get(chatId)
  if (state) state.status = status
}

export function getStream(chatId: string): StreamState | undefined {
  return streams.get(chatId)
}

export function getStreamBySessionId(frontendSessionId: string): StreamState | undefined {
  for (const state of streams.values()) {
    if (state.frontendSessionId === frontendSessionId) return state
  }
  return undefined
}

export function removeStream(chatId: string): void {
  streams.delete(chatId)
}
```

- [ ] **Step 4: Commit**

```bash
git add src/lib/chat/session-store.ts src/lib/chat/permission-queue.ts src/lib/chat/stream-state.ts
git commit -m "feat: add session store, permission queue, and stream state management"
```

---

### Task 6: Chat API Routes

**Files:**
- Create: `src/app/api/chat/stream/route.ts`
- Create: `src/app/api/chat/permission/route.ts`
- Create: `src/app/api/chat/sessions/route.ts`
- Create: `src/app/api/engines/availability/route.ts`

- [ ] **Step 1: Create src/app/api/chat/stream/route.ts**

```typescript
import { NextRequest, NextResponse } from "next/server"
import { getOrCreateEngine } from "@/lib/engines/engine-factory"
import type { EngineType } from "@/lib/engines/engine-factory"
import type { Engine } from "@/lib/engines/engine-interface"
import type { EngineStreamEvent } from "@/lib/engines/engine-interface"
import {
  registerStream,
  appendStreamContent,
  setStreamStatus,
  removeStream,
  getStream,
} from "@/lib/chat/stream-state"
import { appendMessage, updateMessage, getSession } from "@/lib/chat/session-store"
import { registerPendingPermission } from "@/lib/chat/permission-queue"
import type { PermissionRequest } from "@/types/chat"
import { EventEmitter } from "events"

export const dynamic = "force-dynamic"

const activeChats = new Map<string, {
  promise: Promise<any>
  settled: boolean
  chatId: string
  cancel: () => void
}>()
const engineStreamEvents = new EventEmitter()
engineStreamEvents.setMaxListeners(200)

export async function POST(request: NextRequest) {
  try {
    const { message, model, engine: perChatEngine, sessionId, frontendSessionId } = await request.json()
    if (!message?.trim()) {
      return NextResponse.json({ error: "消息不能为空" }, { status: 400 })
    }

    const chatId = `chat-${Date.now()}`
    const configuredEngine = (perChatEngine || "claude-code") as EngineType
    const engine = await getOrCreateEngine(configuredEngine, frontendSessionId)

    if (!engine) {
      return NextResponse.json({ error: "引擎不可用，请检查是否已安装 Claude Code 或 OpenCode" }, { status: 500 })
    }

    registerStream(chatId, frontendSessionId || "", configuredEngine)

    // Save user message
    if (frontendSessionId) {
      await appendMessage(frontendSessionId, {
        id: `msg-${Date.now()}`,
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      })
    }

    const onEngineStream = (evt: EngineStreamEvent) => {
      if (evt.type === "text" && evt.content) {
        appendStreamContent(chatId, evt.content)
        engineStreamEvents.emit(chatId, { type: "delta", content: evt.content })
      } else if (evt.type === "thought" && evt.content) {
        engineStreamEvents.emit(chatId, { type: "thinking", content: evt.content })
      } else if (evt.type === "permission_request" && evt.metadata) {
        const request = evt.metadata as PermissionRequest
        registerPendingPermission(request.id, configuredEngine, engine)
        engineStreamEvents.emit(chatId, { type: "permission_request", request })
      } else if (evt.type === "error" && evt.content) {
        engineStreamEvents.emit(chatId, { type: "engine_error", content: evt.content })
      }
    }

    engine.on("stream", onEngineStream)

    const execPromise = engine.execute({
      prompt: message,
      model: model || "",
      workingDirectory: process.cwd(),
      sessionId: sessionId || undefined,
    }).then(async (result) => {
      // Save assistant message
      if (frontendSessionId) {
        const msgId = `msg-assistant-${chatId}`
        await appendMessage(frontendSessionId, {
          id: msgId,
          role: "assistant",
          content: result.output || "",
          timestamp: new Date().toISOString(),
        })
      }
      return {
        result: result.output,
        session_id: result.sessionId,
        duration_ms: 0,
        is_error: !result.success,
        error: result.error,
      }
    }).finally(() => {
      engine.off("stream", onEngineStream)
    })

    const entry = {
      promise: execPromise,
      settled: false,
      chatId,
      cancel: () => {
        setStreamStatus(chatId, "killed")
        engine.cancel()
      },
    }
    activeChats.set(chatId, entry)
    execPromise
      .then(() => { entry.settled = true; setStreamStatus(chatId, "completed") })
      .catch(() => { entry.settled = true; setStreamStatus(chatId, "failed") })
      .finally(() => {
        setTimeout(() => {
          activeChats.delete(chatId)
          removeStream(chatId)
        }, 30000)
      })

    return NextResponse.json({ chatId })
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "启动失败" }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  const chatId = request.nextUrl.searchParams.get("id")
  if (!chatId) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 })
  }

  const entry = activeChats.get(chatId)
  if (!entry) {
    return NextResponse.json({ error: "Chat not found" }, { status: 404 })
  }

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      let closed = false

      const send = (event: string, data: any) => {
        if (closed) return
        try {
          controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`))
        } catch { closed = true }
      }

      const cleanup = () => {
        closed = true
        engineStreamEvents.off(chatId, onEngineStream)
        try { controller.close() } catch {}
      }

      const onEngineStream = (evt: any) => {
        if (!evt) return
        if (evt.type === "delta") send("delta", { content: evt.content })
        else if (evt.type === "thinking") send("thinking", { content: evt.content })
        else if (evt.type === "permission_request") send("permission_request", { request: evt.request })
        else if (evt.type === "engine_error") send("engine_error", { message: evt.content })
      }

      const state = getStream(chatId)
      if (state?.streamContent) {
        send("delta", { content: state.streamContent })
      }
      engineStreamEvents.on(chatId, onEngineStream)
      send("connected", { chatId })

      entry.promise
        .then((result: any) => {
          send("done", {
            result: result.result,
            sessionId: result.session_id,
            isError: result.is_error,
          })
        })
        .catch((err: any) => {
          send("failed", { message: err.message || "执行失败" })
        })
        .finally(cleanup)

      request.signal.addEventListener("abort", cleanup)
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  })
}

export async function DELETE(request: NextRequest) {
  const chatId = request.nextUrl.searchParams.get("id")
  if (!chatId) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 })
  }
  const entry = activeChats.get(chatId)
  if (entry?.cancel) entry.cancel()
  activeChats.delete(chatId)
  removeStream(chatId)
  return NextResponse.json({ killed: true })
}
```

- [ ] **Step 2: Create src/app/api/chat/permission/route.ts**

```typescript
import { NextRequest, NextResponse } from "next/server"
import { resolvePermission } from "@/lib/chat/permission-queue"

export async function POST(request: NextRequest) {
  try {
    const { requestId, optionId } = await request.json()
    if (!requestId || !optionId) {
      return NextResponse.json({ error: "Missing requestId or optionId" }, { status: 400 })
    }
    const resolved = resolvePermission(requestId, optionId)
    if (!resolved) {
      return NextResponse.json({ error: "Permission request not found or already resolved" }, { status: 404 })
    }
    return NextResponse.json({ resolved: true })
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Failed" }, { status: 500 })
  }
}
```

- [ ] **Step 3: Create src/app/api/chat/sessions/route.ts**

```typescript
import { NextRequest, NextResponse } from "next/server"
import { listSessions, getSession, saveSession, deleteSession } from "@/lib/chat/session-store"
import type { ChatSession } from "@/types/chat"

export async function GET() {
  const sessions = await listSessions()
  return NextResponse.json({ sessions })
}

export async function POST(request: NextRequest) {
  try {
    const { engine, model } = await request.json()
    const session: ChatSession = {
      id: `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title: "",
      engine: engine || "claude-code",
      model: model || "claude-sonnet-4-6",
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    await saveSession(session)
    return NextResponse.json({ session })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { id } = await request.json()
    if (!id) return NextResponse.json({ error: "Missing id" }, { status: 400 })
    await deleteSession(id)
    return NextResponse.json({ deleted: true })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
```

- [ ] **Step 4: Create src/app/api/engines/availability/route.ts**

```typescript
import { NextResponse } from "next/server"
import { detectEngines } from "@/lib/engines/engine-factory"

export const dynamic = "force-dynamic"

export async function GET() {
  const engines = await detectEngines()
  return NextResponse.json({ engines })
}
```

- [ ] **Step 5: Commit**

```bash
git add src/app/api/chat/ src/app/api/engines/
git commit -m "feat: add chat API routes (stream, permission, sessions, engine availability)"
```

---

### Task 7: Frontend - Chat Hook

**Files:**
- Create: `src/hooks/use-chat-stream.ts`

- [ ] **Step 1: Create src/hooks/use-chat-stream.ts**

```typescript
"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import type { ChatMessage, PermissionRequest, SSEEvent } from "@/types/chat"

interface UseChatStreamOptions {
  sessionId: string
  engine: string
  model: string
}

export function useChatStream({ sessionId, engine, model }: UseChatStreamOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [pendingPermission, setPendingPermission] = useState<PermissionRequest | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)

    // Add streaming assistant message placeholder
    const assistantMsgId = `msg-assistant-${Date.now()}`
    setMessages((prev) => [...prev, {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    }])

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          engine,
          model,
          frontendSessionId: sessionId,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: `错误: ${err.error}`, isStreaming: false } : m
        ))
        setIsStreaming(false)
        return
      }

      const { chatId } = await res.json()
      setCurrentChatId(chatId)

      // Open SSE connection
      const es = new EventSource(`/api/chat/stream?id=${chatId}`)
      eventSourceRef.current = es

      es.addEventListener("delta", (e) => {
        const data = JSON.parse(e.data)
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: m.content + data.content } : m
        ))
      })

      es.addEventListener("thinking", () => {
        // Could display thinking indicator
      })

      es.addEventListener("permission_request", (e) => {
        const data = JSON.parse(e.data)
        setPendingPermission(data.request)
        // Also add to messages
        setMessages((prev) => [...prev, {
          id: `perm-msg-${data.request.id}`,
          role: "assistant",
          content: "",
          timestamp: new Date().toISOString(),
          permissionRequest: data.request,
        }])
      })

      es.addEventListener("done", () => {
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, isStreaming: false } : m
        ))
        setIsStreaming(false)
        es.close()
        eventSourceRef.current = null
      })

      es.addEventListener("failed", (e) => {
        const data = JSON.parse(e.data)
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false } : m
        ))
        setIsStreaming(false)
        es.close()
        eventSourceRef.current = null
      })

      es.addEventListener("engine_error", (e) => {
        const data = JSON.parse(e.data)
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false } : m
        ))
      })

      es.onerror = () => {
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, isStreaming: false } : m
        ))
        setIsStreaming(false)
        es.close()
        eventSourceRef.current = null
      }
    } catch (error) {
      setMessages((prev) => prev.map((m) =>
        m.id === assistantMsgId ? { ...m, content: `连接失败: ${error}`, isStreaming: false } : m
      ))
      setIsStreaming(false)
    }
  }, [sessionId, engine, model, isStreaming])

  const resolvePermission = useCallback(async (requestId: string, optionId: string) => {
    setPendingPermission(null)
    // Update the permission message in place
    setMessages((prev) => prev.map((m) =>
      m.permissionRequest?.id === requestId
        ? { ...m, permissionDecision: { optionId, label: optionId } }
        : m
    ))
    await fetch("/api/chat/permission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requestId, optionId }),
    })
  }, [])

  const cancelStream = useCallback(async () => {
    if (currentChatId) {
      await fetch(`/api/chat/stream?id=${currentChatId}`, { method: "DELETE" })
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsStreaming(false)
  }, [currentChatId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return {
    messages,
    setMessages,
    isStreaming,
    pendingPermission,
    sendMessage,
    resolvePermission,
    cancelStream,
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/hooks/use-chat-stream.ts
git commit -m "feat: add useChatStream hook for SSE chat communication"
```

---

### Task 8: Frontend - Chat Components

**Files:**
- Create: `src/components/workflow/engine-info.tsx`
- Create: `src/components/workflow/permission-card.tsx`
- Create: `src/components/workflow/tool-call-card.tsx`
- Create: `src/components/workflow/chat-message.tsx`
- Create: `src/components/workflow/chat-input.tsx`
- Create: `src/components/workflow/chat-stream.tsx`
- Create: `src/components/workflow/chat-sidebar.tsx`
- Create: `src/components/workflow/chat-layout.tsx`

- [ ] **Step 1: Create src/components/workflow/engine-info.tsx**

```tsx
import { Bot, Cpu } from "lucide-react"

interface EngineInfoProps {
  engineName: string
  modelName: string
}

export function EngineInfo({ engineName, modelName }: EngineInfoProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 border-b bg-card text-sm">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        <Bot className="h-3.5 w-3.5" />
        <span>{engineName}</span>
      </div>
      <div className="flex items-center gap-1.5 text-muted-foreground">
        <Cpu className="h-3.5 w-3.5" />
        <span>{modelName}</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create src/components/workflow/permission-card.tsx**

```tsx
"use client"

import type { PermissionRequest, PermissionOption } from "@/types/chat"
import { Shield, Check, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface PermissionCardProps {
  request: PermissionRequest
  decision?: { optionId: string; label: string }
  onResolve?: (requestId: string, optionId: string) => void
}

export function PermissionCard({ request, decision, onResolve }: PermissionCardProps) {
  const resolved = !!decision

  return (
    <div className={cn(
      "rounded-lg border p-4 my-2",
      resolved ? "bg-muted/50" : "bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800"
    )}>
      <div className="flex items-center gap-2 mb-2">
        <Shield className="h-4 w-4 text-amber-600" />
        <span className="font-medium text-sm">Agent 请求权限</span>
        {resolved && <span className="text-xs text-muted-foreground ml-auto">已决策</span>}
      </div>
      <div className="text-sm mb-1">
        <span className="font-medium">操作：</span>
        <span className="text-muted-foreground">{request.description}</span>
      </div>
      <div className="text-sm mb-3">
        <span className="font-medium">内容：</span>
        <code className="text-xs bg-muted px-1 py-0.5 rounded">{request.detail.slice(0, 200)}</code>
      </div>
      <div className="flex gap-2">
        {request.options.map((option) => (
          <button
            key={option.id}
            disabled={resolved}
            onClick={() => onResolve?.(request.id, option.id)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              resolved && decision?.optionId === option.id && "ring-2 ring-offset-1",
              option.style === "danger"
                ? "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400"
                : option.style === "primary"
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
              resolved && "opacity-60 cursor-not-allowed"
            )}
          >
            {option.style === "danger" ? <X className="h-3 w-3 inline mr-1" /> : <Check className="h-3 w-3 inline mr-1" />}
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create src/components/workflow/tool-call-card.tsx**

```tsx
import { Wrench } from "lucide-react"
import { useState } from "react"

interface ToolCallCardProps {
  name: string
  input?: string
  output?: string
}

export function ToolCallCard({ name, input, output }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-lg border bg-muted/30 p-3 my-2 text-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="font-medium">{name}</span>
        <span className="text-xs text-muted-foreground ml-auto">
          {expanded ? "收起" : "展开"}
        </span>
      </button>
      {expanded && (input || output) && (
        <div className="mt-2 space-y-2">
          {input && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">输入</div>
              <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-40">{input}</pre>
            </div>
          )}
          {output && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">输出</div>
              <pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-40">{output}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create src/components/workflow/chat-message.tsx**

```tsx
import type { ChatMessage as ChatMessageType } from "@/types/chat"
import { PermissionCard } from "./permission-card"
import { cn } from "@/lib/utils"
import { User, Bot } from "lucide-react"

interface ChatMessageProps {
  message: ChatMessageType
  onResolvePermission?: (requestId: string, optionId: string) => void
}

export function ChatMessage({ message, onResolvePermission }: ChatMessageProps) {
  const isUser = message.role === "user"

  // Permission request message
  if (message.permissionRequest) {
    return (
      <div className="flex justify-start px-4 py-1">
        <div className="max-w-[80%]">
          <PermissionCard
            request={message.permissionRequest}
            decision={message.permissionDecision}
            onResolve={onResolvePermission}
          />
        </div>
      </div>
    )
  }

  return (
    <div className={cn("flex gap-3 px-4 py-2", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-primary shrink-0 mt-1">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={cn(
        "rounded-lg px-3 py-2 max-w-[80%] text-sm",
        isUser
          ? "bg-primary text-primary-foreground"
          : "bg-card border"
      )}>
        <div className="whitespace-pre-wrap break-words">
          {message.content || (message.isStreaming ? "..." : "")}
        </div>
        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5" />
        )}
      </div>
      {isUser && (
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-secondary text-secondary-foreground shrink-0 mt-1">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Create src/components/workflow/chat-input.tsx**

```tsx
"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Square } from "lucide-react"

interface ChatInputProps {
  onSend: (message: string) => void
  isStreaming: boolean
  onCancel: () => void
}

export function ChatInput({ onSend, isStreaming, onCancel }: ChatInputProps) {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return
    onSend(input.trim())
    setInput("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t bg-card p-4">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          disabled={isStreaming}
          rows={1}
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-50"
        />
        {isStreaming ? (
          <button
            onClick={onCancel}
            className="p-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            <Square className="h-4 w-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!input.trim()}
            className="p-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create src/components/workflow/chat-stream.tsx**

```tsx
"use client"

import { useRef, useEffect } from "react"
import type { ChatMessage as ChatMessageType } from "@/types/chat"
import { ChatMessage } from "./chat-message"

interface ChatStreamProps {
  messages: ChatMessageType[]
  onResolvePermission?: (requestId: string, optionId: string) => void
}

export function ChatStream({ messages, onResolvePermission }: ChatStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto py-4">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          开始对话吧...
        </div>
      )}
      {messages.map((msg) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          onResolvePermission={onResolvePermission}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 7: Create src/components/workflow/chat-sidebar.tsx**

```tsx
"use client"

import { useState, useEffect } from "react"
import type { ChatSession, EngineAvailability, ModelInfo } from "@/types/chat"
import { Plus, Trash2, Bot, Cpu } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatSidebarProps {
  sessions: ChatSession[]
  currentSessionId: string | null
  engine: string
  model: string
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onDeleteSession: (id: string) => void
  onEngineChange: (engine: string) => void
  onModelChange: (model: string) => void
}

export function ChatSidebar({
  sessions,
  currentSessionId,
  engine,
  model,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onEngineChange,
  onModelChange,
}: ChatSidebarProps) {
  const [engines, setEngines] = useState<EngineAvailability[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/engines/availability")
      .then((r) => r.json())
      .then((data) => {
        setEngines(data.engines || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const currentEngineInfo = engines.find((e) => {
    const engineKey = e.name.toLowerCase().replace(" ", "-")
    return engineKey === engine || e.name === engine
  })

  return (
    <div className="w-64 border-r bg-card flex flex-col h-full">
      <div className="p-3 border-b">
        <button
          onClick={onNewSession}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          新建会话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={cn(
              "flex items-center justify-between px-3 py-2 rounded-md text-sm cursor-pointer",
              session.id === currentSessionId
                ? "bg-accent text-accent-foreground"
                : "hover:bg-accent/50"
            )}
          >
            <span className="truncate flex-1">
              {session.title || "新会话"}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
              className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>

      <div className="border-t p-3 space-y-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Bot className="h-3.5 w-3.5" />
          <span>Agent</span>
        </div>
        <select
          value={engine}
          onChange={(e) => onEngineChange(e.target.value)}
          className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
        >
          {engines.map((e) => (
            <option key={e.name} value={e.name.toLowerCase().replace(" ", "-")} disabled={!e.available}>
              {e.name} {!e.available && "(未安装)"}
            </option>
          ))}
          {engines.length === 0 && !loading && (
            <option value="" disabled>未检测到 Agent</option>
          )}
        </select>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Cpu className="h-3.5 w-3.5" />
          <span>模型</span>
        </div>
        <select
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
        >
          {(currentEngineInfo?.models || []).map((m: ModelInfo) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Create src/components/workflow/chat-layout.tsx**

```tsx
"use client"

import { ChatSidebar } from "./chat-sidebar"
import { ChatStream } from "./chat-stream"
import { ChatInput } from "./chat-input"
import { EngineInfo } from "./engine-info"
import type { ChatSession, ChatMessage } from "@/types/chat"

interface ChatLayoutProps {
  sessions: ChatSession[]
  currentSessionId: string | null
  engine: string
  model: string
  messages: ChatMessage[]
  isStreaming: boolean
  onSelectSession: (id: string) => void
  onNewSession: () => void
  onDeleteSession: (id: string) => void
  onEngineChange: (engine: string) => void
  onModelChange: (model: string) => void
  onSendMessage: (content: string) => void
  onResolvePermission: (requestId: string, optionId: string) => void
  onCancelStream: () => void
}

export function ChatLayout({
  sessions,
  currentSessionId,
  engine,
  model,
  messages,
  isStreaming,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onEngineChange,
  onModelChange,
  onSendMessage,
  onResolvePermission,
  onCancelStream,
}: ChatLayoutProps) {
  const engineDisplayName = engine === "claude-code" ? "Claude Code" : engine === "opencode" ? "OpenCode" : engine

  return (
    <div className="flex h-full">
      <ChatSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        engine={engine}
        model={model}
        onSelectSession={onSelectSession}
        onNewSession={onNewSession}
        onDeleteSession={onDeleteSession}
        onEngineChange={onEngineChange}
        onModelChange={onModelChange}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <EngineInfo engineName={engineDisplayName} modelName={model} />
        <ChatStream messages={messages} onResolvePermission={onResolvePermission} />
        <ChatInput onSend={onSendMessage} isStreaming={isStreaming} onCancel={onCancelStream} />
      </div>
    </div>
  )
}
```

- [ ] **Step 9: Commit**

```bash
git add src/components/workflow/
git commit -m "feat: add all workflow chat components"
```

---

### Task 9: Workflow Page and Navigation Updates

**Files:**
- Create: `src/app/workflow/page.tsx`
- Modify: `src/components/layout/navbar.tsx`
- Create: `src/components/dashboard/workflow-card.tsx`
- Modify: `src/app/dashboard/page.tsx`

- [ ] **Step 1: Create src/app/workflow/page.tsx**

```tsx
"use client"

import { useState, useEffect, useCallback } from "react"
import { ChatLayout } from "@/components/workflow/chat-layout"
import { useChatStream } from "@/hooks/use-chat-stream"
import type { ChatSession } from "@/types/chat"

export default function WorkflowPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [engine, setEngine] = useState("claude-code")
  const [model, setModel] = useState("claude-sonnet-4-6")

  const currentSession = sessions.find((s) => s.id === currentSessionId)
  const { messages, setMessages, isStreaming, sendMessage, resolvePermission, cancelStream } =
    useChatStream({
      sessionId: currentSessionId || "",
      engine,
      model,
    })

  const loadSessions = useCallback(async () => {
    const res = await fetch("/api/chat/sessions")
    const data = await res.json()
    setSessions(data.sessions || [])
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  const handleNewSession = async () => {
    const res = await fetch("/api/chat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engine, model }),
    })
    const data = await res.json()
    if (data.session) {
      setSessions((prev) => [data.session, ...prev])
      setCurrentSessionId(data.session.id)
      setMessages([])
    }
  }

  const handleDeleteSession = async (id: string) => {
    await fetch("/api/chat/sessions", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    })
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (currentSessionId === id) {
      setCurrentSessionId(null)
      setMessages([])
    }
  }

  const handleSelectSession = (id: string) => {
    setCurrentSessionId(id)
    const session = sessions.find((s) => s.id === id)
    if (session) {
      setMessages(session.messages)
    }
  }

  const handleEngineChange = (newEngine: string) => {
    setEngine(newEngine)
  }

  const handleModelChange = (newModel: string) => {
    setModel(newModel)
  }

  return (
    <div className="h-[calc(100vh-3.5rem)]">
      <ChatLayout
        sessions={sessions}
        currentSessionId={currentSessionId}
        engine={engine}
        model={model}
        messages={messages}
        isStreaming={isStreaming}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onEngineChange={handleEngineChange}
        onModelChange={handleModelChange}
        onSendMessage={sendMessage}
        onResolvePermission={resolvePermission}
        onCancelStream={cancelStream}
      />
    </div>
  )
}
```

- [ ] **Step 2: Update src/components/layout/navbar.tsx — add Workflow nav item**

In the `navItems` array, add a new entry:

```typescript
const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/skills", label: "Skills", icon: Sparkles },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/workflow", label: "工作流", icon: Workflow },
]
```

And add the import:

```typescript
import { LayoutDashboard, Sparkles, Bot, Moon, Sun, Workflow } from "lucide-react"
```

- [ ] **Step 3: Create src/components/dashboard/workflow-card.tsx**

```tsx
import Link from "next/link"
import { Rocket } from "lucide-react"

export function WorkflowCard() {
  return (
    <div className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
          <Rocket className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold">工作流</h3>
          <p className="text-sm text-muted-foreground mt-1">
            启动 AI Agent 对话，支持 Claude Code / OpenCode
          </p>
        </div>
      </div>
      <div className="mt-4">
        <Link
          href="/workflow"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          进入工作流 →
        </Link>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Update src/app/dashboard/page.tsx — add WorkflowCard**

Add the import and place the card after the ranking section:

```tsx
import { WorkflowCard } from "@/components/dashboard/workflow-card"

// In the JSX, add after </UsageRanking>:
<WorkflowCard />
```

The final dashboard page:

```tsx
import { StatsCards } from "@/components/dashboard/stats-cards"
import { UsageTrend } from "@/components/dashboard/usage-trend"
import { UsageRanking } from "@/components/dashboard/usage-ranking"
import { WorkflowCard } from "@/components/dashboard/workflow-card"
import { dashboardStats, trendData, skillRanking, agentRanking } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatsCards stats={dashboardStats} />
      <UsageTrend data={trendData} />
      <UsageRanking skillRanking={skillRanking} agentRanking={agentRanking} />
      <WorkflowCard />
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add src/app/workflow/ src/components/layout/navbar.tsx src/components/dashboard/workflow-card.tsx src/app/dashboard/page.tsx
git commit -m "feat: add workflow page, update navbar and dashboard with workflow entry"
```

---

### Task 10: Build Verification

- [ ] **Step 1: Run production build**

```bash
npm run build
```

Expected: Build succeeds. Some TypeScript strict warnings are acceptable.

- [ ] **Step 2: Fix any build errors if found**

Common issues:
- Missing `Workflow` icon import in navbar — verify it exists in lucide-react
- Server component importing client code — add "use client" directives

- [ ] **Step 3: Start dev server and verify pages**

```bash
npm run dev
```

- http://localhost:3000/dashboard — should show WorkflowCard
- http://localhost:3000/workflow — should show chat layout with sidebar
- Navigation between pages should work

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve build issues for workflow feature"
```
