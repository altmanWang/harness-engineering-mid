import { NextRequest, NextResponse } from "next/server"
import { getOrCreateEngine } from "@/lib/engines/engine-factory"
import type { EngineStreamEvent } from "@/lib/engines/engine-interface"
import { registerStream, appendStreamContent, setStreamStatus, removeStream, getStream } from "@/lib/chat/stream-state"
import { appendMessage, updateSessionAgentId } from "@/lib/chat/session-store"
import { registerPendingPermission } from "@/lib/chat/permission-queue"
import type { PermissionRequest } from "@/types/chat"
import { EventEmitter } from "events"

export const dynamic = "force-dynamic"

const activeChats = new Map<string, { promise: Promise<any>; settled: boolean; chatId: string; cancel: () => void }>()
const engineStreamEvents = new EventEmitter()
engineStreamEvents.setMaxListeners(200)

export async function POST(request: NextRequest) {
  try {
    const { message, model, sessionId: frontendSessionId, agentSessionId } = await request.json()
    if (!message?.trim()) return NextResponse.json({ error: "消息不能为空" }, { status: 400 })

    const chatId = `chat-${Date.now()}`
    const engine = await getOrCreateEngine(frontendSessionId)

    if (!engine) return NextResponse.json({ error: "引擎不可用，请检查是否已安装 OpenCode" }, { status: 500 })

    registerStream(chatId, frontendSessionId || "", "opencode")

    if (frontendSessionId) {
      await appendMessage(frontendSessionId, {
        id: `msg-${Date.now()}`, role: "user", content: message, timestamp: new Date().toISOString(),
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
        registerPendingPermission(request.id, engine)
        engineStreamEvents.emit(chatId, { type: "permission_request", request })
      } else if (evt.type === "error" && evt.content) {
        engineStreamEvents.emit(chatId, { type: "engine_error", content: evt.content })
      }
    }

    engine.on("stream", onEngineStream)

    const execPromise = engine.execute({
      prompt: message, model: model || "", workingDirectory: process.cwd(), sessionId: agentSessionId || undefined,
    }).then(async (result) => {
      if (frontendSessionId) {
        await appendMessage(frontendSessionId, {
          id: `msg-assistant-${chatId}`, role: "assistant", content: result.output || "", timestamp: new Date().toISOString(),
        })
        if (result.sessionId) {
          await updateSessionAgentId(frontendSessionId, result.sessionId)
        }
      }
      return { result: result.output, session_id: result.sessionId, is_error: !result.success, error: result.error }
    }).finally(() => { engine.off("stream", onEngineStream) })

    const entry = { promise: execPromise, settled: false, chatId, cancel: () => { setStreamStatus(chatId, "killed"); engine.cancel() } }
    activeChats.set(chatId, entry)
    execPromise
      .then(() => { entry.settled = true; setStreamStatus(chatId, "completed") })
      .catch(() => { entry.settled = true; setStreamStatus(chatId, "failed") })
      .finally(() => { setTimeout(() => { activeChats.delete(chatId); removeStream(chatId) }, 30000) })

    return NextResponse.json({ chatId })
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "启动失败" }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  const chatId = request.nextUrl.searchParams.get("id")
  if (!chatId) return NextResponse.json({ error: "Missing id" }, { status: 400 })
  const entry = activeChats.get(chatId)
  if (!entry) return NextResponse.json({ error: "Chat not found" }, { status: 404 })

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      let closed = false
      const send = (event: string, data: any) => {
        if (closed) return
        try { controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)) } catch { closed = true }
      }
      const cleanup = () => { closed = true; engineStreamEvents.off(chatId, onEngineStream); try { controller.close() } catch {} }
      const onEngineStream = (evt: any) => {
        if (!evt) return
        if (evt.type === "delta") send("delta", { content: evt.content })
        else if (evt.type === "thinking") send("thinking", { content: evt.content })
        else if (evt.type === "permission_request") send("permission_request", { request: evt.request })
        else if (evt.type === "engine_error") send("engine_error", { message: evt.content })
      }
      const state = getStream(chatId)
      if (state?.streamContent) send("delta", { content: state.streamContent })
      engineStreamEvents.on(chatId, onEngineStream)
      send("connected", { chatId })
      entry.promise
        .then((result: any) => { send("done", { result: result.result, sessionId: result.session_id, isError: result.is_error }) })
        .catch((err: any) => { send("failed", { message: err.message || "执行失败" }) })
        .finally(cleanup)
      request.signal.addEventListener("abort", cleanup)
    },
  })

  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive" },
  })
}

export async function DELETE(request: NextRequest) {
  const chatId = request.nextUrl.searchParams.get("id")
  if (!chatId) return NextResponse.json({ error: "Missing id" }, { status: 400 })
  const entry = activeChats.get(chatId)
  if (entry?.cancel) entry.cancel()
  activeChats.delete(chatId)
  removeStream(chatId)
  return NextResponse.json({ killed: true })
}
