"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import type { ChatMessage, PermissionRequest } from "@/types/chat"

interface UseChatStreamOptions {
  sessionId: string
  model: string
  agentSessionId?: string
  onAgentSessionIdChange?: (id: string) => void
}

export function useChatStream({ sessionId, model, agentSessionId, onAgentSessionIdChange }: UseChatStreamOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [pendingPermission, setPendingPermission] = useState<PermissionRequest | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)

    const assistantMsgId = `msg-assistant-${Date.now()}`
    setMessages((prev) => [...prev, {
      id: assistantMsgId, role: "assistant", content: "", timestamp: new Date().toISOString(), isStreaming: true,
    }])

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, model, sessionId, agentSessionId: agentSessionId || undefined }),
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

      const es = new EventSource(`/api/chat/stream?id=${chatId}`)
      eventSourceRef.current = es

      es.addEventListener("delta", (e) => {
        const data = JSON.parse(e.data)
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId ? { ...m, content: m.content + data.content } : m
        ))
      })

      es.addEventListener("thinking", (e) => {
        const data = JSON.parse(e.data)
        setMessages((prev) => prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, thoughtContent: (m.thoughtContent || "") + data.content }
            : m
        ))
      })

      es.addEventListener("permission_request", (e) => {
        const data = JSON.parse(e.data)
        setPendingPermission(data.request)
        setMessages((prev) => [...prev, {
          id: `perm-msg-${data.request.id}`, role: "assistant", content: "",
          timestamp: new Date().toISOString(), permissionRequest: data.request,
        }])
      })

      es.addEventListener("done", (e) => {
        const data = JSON.parse(e.data)
        if (data.sessionId && onAgentSessionIdChange) {
          onAgentSessionIdChange(data.sessionId)
        }
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
        setMessages((prev) => prev.map((m) => m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
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
  }, [sessionId, model, isStreaming, agentSessionId, onAgentSessionIdChange])

  const resolvePermission = useCallback(async (requestId: string, optionId: string) => {
    setPendingPermission(null)
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
    if (currentChatId) await fetch(`/api/chat/stream?id=${currentChatId}`, { method: "DELETE" })
    if (eventSourceRef.current) { eventSourceRef.current.close(); eventSourceRef.current = null }
    setIsStreaming(false)
  }, [currentChatId])

  useEffect(() => { return () => { if (eventSourceRef.current) eventSourceRef.current.close() } }, [])

  return { messages, setMessages, isStreaming, pendingPermission, sendMessage, resolvePermission, cancelStream }
}
