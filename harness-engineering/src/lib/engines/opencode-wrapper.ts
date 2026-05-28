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

  getName(): string { return "opencode" }

  async isAvailable(): Promise<boolean> {
    try {
      const { execSync } = require("child_process")
      if (process.platform === "win32") {
        execSync("where opencode", { stdio: "ignore" })
      } else {
        execSync("command -v opencode", { stdio: "ignore", shell: "/bin/bash" })
      }
      return true
    } catch { return false }
  }

  async execute(options: EngineOptions): Promise<EngineResult> {
    this.seenToolIds.clear()
    this.collectedOutput = ""
    const canReuse = options.sessionId && this.engine && this.currentSessionId === options.sessionId
    if (!canReuse) {
      if (this.engine) { try { this.engine.stop() } catch {} }
      const config: ACPEngineConfig = {
        engineType: "opencode", command: "opencode",
        workingDirectory: options.workingDirectory || process.cwd(),
        agentName: options.agent, model: options.model,
      }
      this.engine = new ACPEngine(config)
      this.setupEngineEvents()
      await this.engine.start()
      this.currentSessionId = options.sessionId
        ? await this.engine.resumeSession(options.sessionId)
        : await this.engine.createSession()
    }
    const engine = this.engine!
    if (options.model) {
      try { await engine.setModel(options.model) }
      catch (err: any) {
        this.emit("stream", { type: "error", content: `Model unavailable: ${err.message}` } as EngineStreamEvent)
        return { success: false, output: "", error: err.message }
      }
    }
    this.streaming = true
    try {
      const stopReason = await engine.sendPrompt(options.prompt)
      this.streaming = false
      return {
        success: !stopReason || stopReason === "end_turn",
        output: this.collectedOutput.trim(),
        sessionId: this.currentSessionId ?? undefined,
        stopReason: stopReason ?? undefined,
      }
    } catch (error) {
      this.streaming = false
      return { success: false, output: this.collectedOutput.trim(), error: error instanceof Error ? error.message : String(error) }
    }
  }

  resolvePermission(optionId: string): void {
    this.engine?.resolvePermission(optionId)
  }

  cancel(): void {
    if (this.engine) { this.engine.cancelSession(); this.engine.stop(); this.engine = null }
  }

  getAvailableModels(): Array<{ modelId: string; name: string }> {
    return this.engine?.getAvailableModels() || []
  }

  private setupEngineEvents(): void {
    if (!this.engine) return
    this.engine.on("agent-message", (content: any) => {
      if (!this.streaming) return
      const text = typeof content === "string" ? content : content?.text || content?.content || ""
      if (text) { this.collectedOutput += text; this.emit("stream", { type: "text", content: text } as EngineStreamEvent) }
    })
    this.engine.on("agent-thought", (content: any) => {
      if (!this.streaming) return
      const text = typeof content === "string" ? content : content?.text || content?.content || ""
      if (text) this.emit("stream", { type: "thought", content: text } as EngineStreamEvent)
    })
    this.engine.on("tool-call", (tc: any) => {
      if (!this.streaming) return
      const toolId = tc.id || ""
      if (toolId && !this.seenToolIds.has(toolId)) {
        this.seenToolIds.add(toolId)
        const formatted = `\n\n**🔧 ${tc.title || "Tool"}**\n`
        this.collectedOutput += formatted
        this.emit("stream", { type: "text", content: formatted, metadata: tc } as EngineStreamEvent)
      }
    })
    this.engine.on("tool-call-update", (tu: any) => {
      if (!this.streaming) return
      if (tu.status === "completed" || tu.status === "failed") {
        const output = typeof tu.rawOutput === "string" ? tu.rawOutput : tu.rawOutput?.output || ""
        if (output) {
          const formatted = `\n\`\`\`\n${output}\n\`\`\`\n`
          this.collectedOutput += formatted
          this.emit("stream", { type: "text", content: formatted, metadata: tu } as EngineStreamEvent)
        }
      }
    })
    this.engine.on("permission", (params: any) => {
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
        options, timestamp: new Date().toISOString(),
      }
      this.emit("stream", { type: "permission_request", content: JSON.stringify(request), metadata: request } as EngineStreamEvent)
    })
    this.engine.on("error", (error: any) => {
      this.emit("stream", { type: "error", content: error instanceof Error ? error.message : String(error) } as EngineStreamEvent)
    })
  }

  private inferOptionStyle(id: string): "primary" | "danger" | "default" {
    const lower = id.toLowerCase()
    if (lower.includes("deny") || lower.includes("reject") || lower.includes("block")) return "danger"
    if (lower.includes("allow") || lower.includes("accept") || lower.includes("always")) return "primary"
    return "default"
  }
}
