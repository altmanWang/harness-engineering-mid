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
      shell: process.platform === "win32",
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

    this.process.on("exit", () => {
      this.cleanup()
    })

    this.process.on("error", () => {
      this.cleanup()
    })

    const output = Writable.toWeb(this.process.stdin) as WritableStream<Uint8Array>
    const input = Readable.toWeb(this.process.stdout) as ReadableStream<Uint8Array>
    const stream = ndJsonStream(output, input)

    const engine = this
    this.connection = new ClientSideConnection((_agent: Agent): Client => ({
      async requestPermission(params: RequestPermissionRequest): Promise<RequestPermissionResponse> {
        engine.emit("permission", params)
        const decision = await new Promise<RequestPermissionResponse>((resolve) => {
          engine.permissionResolver = resolve
        })
        engine.permissionResolver = null
        return decision
      },

      async sessionUpdate(params: SessionNotification): Promise<void> {
        engine.handleSessionUpdate(params.update)
      },

      async extMethod(): Promise<Record<string, unknown>> { return {} },
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
    const result = await this.connection.newSession({ cwd: this.config.workingDirectory, mcpServers: [] })
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

  getAvailableModels(): Array<{ modelId: string; name: string }> { return this.availableModels }

  cancelSession(): void {
    if (this.sessionId && this.connection) {
      this.connection.cancel({ sessionId: this.sessionId }).catch(() => {})
    }
  }

  stop(): void {
    if (this.process) { this.process.kill(); this.cleanup() }
  }

  private handleSessionUpdate(update: SessionUpdate): void {
    switch (update.sessionUpdate) {
      case "agent_message_chunk": this.emit("agent-message", (update as any).content); break
      case "agent_thought_chunk": this.emit("agent-thought", (update as any).content); break
      case "tool_call": this.emit("tool-call", { id: (update as any).toolCallId, title: (update as any).title, status: (update as any).status, rawInput: (update as any).rawInput }); break
      case "tool_call_update": this.emit("tool-call-update", { id: (update as any).toolCallId, title: (update as any).title, status: (update as any).status, rawInput: (update as any).rawInput, rawOutput: (update as any).rawOutput }); break
    }
  }

  private cleanup(): void {
    this.process = null; this.connection = null; this.sessionId = null; this.initialized = false
  }
}
