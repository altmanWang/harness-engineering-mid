import type { EngineOptions, EngineResult } from "@/types/chat"

export interface EngineStreamEvent {
  type: "text" | "thought" | "tool" | "permission_request" | "error"
  content: string
  metadata?: any
}

export interface Engine {
  getName(): string
  execute(options: EngineOptions): Promise<EngineResult>
  cancel(): void
  isAvailable(): Promise<boolean>
  resolvePermission(optionId: string): void
  on(event: "stream", listener: (evt: EngineStreamEvent) => void): this
  on(event: string, listener: (...args: any[]) => void): this
  off(event: string, listener: (...args: any[]) => void): this
}
