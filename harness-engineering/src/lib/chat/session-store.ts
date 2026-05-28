import { readFile, writeFile, mkdir, unlink } from "fs/promises"
import { existsSync } from "fs"
import { resolve } from "path"
import type { ChatSession, ChatMessage } from "@/types/chat"

const SESSIONS_DIR = resolve(process.cwd(), "data", "chat-sessions")

async function ensureDir(): Promise<void> {
  if (!existsSync(SESSIONS_DIR)) await mkdir(SESSIONS_DIR, { recursive: true })
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
  } catch { return null }
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

export async function updateSessionAgentId(sessionId: string, agentSessionId: string): Promise<void> {
  const session = await getSession(sessionId)
  if (!session) return
  session.agentSessionId = agentSessionId
  await saveSession(session)
}
