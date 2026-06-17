import { OpenCodeEngineWrapper } from "./opencode-wrapper"
import type { Engine } from "./engine-interface"
import type { EngineAvailability, ModelInfo } from "@/types/chat"
import { readFile } from "fs/promises"
import { existsSync } from "fs"
import { resolve } from "path"
import { homedir } from "os"

export type EngineType = "opencode"

const enginePool = new Map<string, { engine: Engine; lastUsed: number }>()

setInterval(() => {
  const now = Date.now()
  for (const [key, entry] of enginePool) {
    if (now - entry.lastUsed > ENGINE_POOL_TTL) {
      if (typeof (entry.engine as any).cancel === "function") (entry.engine as any).cancel()
      enginePool.delete(key)
    }
  }
}, 60_000)

const ENGINE_POOL_TTL = 10 * 60 * 1000

export async function getOrCreateEngine(sessionKey?: string): Promise<Engine | null> {
  if (sessionKey) {
    const cached = enginePool.get(sessionKey)
    if (cached) {
      cached.lastUsed = Date.now()
      return cached.engine
    }
  }
  const engine = await createEngine()
  if (engine && sessionKey) enginePool.set(sessionKey, { engine, lastUsed: Date.now() })
  return engine
}

export async function createEngine(): Promise<Engine | null> {
  const engine = new OpenCodeEngineWrapper()
  if (!(await engine.isAvailable())) return null
  return engine
}

export async function detectEngines(): Promise<EngineAvailability[]> {
  const engine = new OpenCodeEngineWrapper()
  const available = await engine.isAvailable()
  const models = await readOpenCodeModels()
  return [{ available, name: "OpenCode", models, defaultModel: models[0]?.id }]
}

async function readOpenCodeModels(): Promise<ModelInfo[]> {
  const configPath = resolve(homedir(), ".config", "opencode", "opencode.json")
  if (!existsSync(configPath)) return [{ id: "default", name: "Default" }]

  try {
    const content = await readFile(configPath, "utf-8")
    const config = JSON.parse(content)
    const models: ModelInfo[] = []
    const defaultModel = config.model || ""

    if (config.provider && typeof config.provider === "object") {
      for (const [providerKey, providerVal] of Object.entries(config.provider)) {
        const provider = providerVal as { models?: Record<string, any> }
        if (!provider.models || typeof provider.models !== "object") continue
        for (const [modelKey, modelVal] of Object.entries(provider.models)) {
          const model = modelVal as { name?: string }
          const fullId = `${providerKey}/${modelKey}`
          const isDefault = defaultModel === fullId
          models.push({
            id: fullId,
            name: model.name || modelKey + (isDefault ? " (默认)" : ""),
          })
        }
      }
    }

    if (models.length === 0) return [{ id: "default", name: "Default" }]
    models.sort((a, b) => {
      if (a.id === defaultModel) return -1
      if (b.id === defaultModel) return 1
      return a.name.localeCompare(b.name)
    })
    return models
  } catch {
    return [{ id: "default", name: "Default" }]
  }
}

export async function isEngineAvailable(): Promise<boolean> {
  const engine = await createEngine()
  return engine !== null
}
