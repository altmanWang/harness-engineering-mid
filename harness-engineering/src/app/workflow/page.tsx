"use client"

import { useState, useEffect, useCallback } from "react"
import { ChatLayout } from "@/components/workflow/chat-layout"
import { useChatStream } from "@/hooks/use-chat-stream"
import type { ChatSession } from "@/types/chat"

export default function WorkflowPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [model, setModel] = useState("")
  const [agentSessionId, setAgentSessionId] = useState<string | undefined>(undefined)

  const { messages, setMessages, isStreaming, sendMessage, resolvePermission, cancelStream } =
    useChatStream({ sessionId: currentSessionId || "", model, agentSessionId, onAgentSessionIdChange: setAgentSessionId })

  const loadSessions = useCallback(async () => {
    const res = await fetch("/api/chat/sessions")
    const data = await res.json()
    setSessions(data.sessions || [])
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  const handleNewSession = async () => {
    const res = await fetch("/api/chat/sessions", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    })
    const data = await res.json()
    if (data.session) {
      setSessions((prev) => [data.session, ...prev])
      setCurrentSessionId(data.session.id)
      setMessages([])
      setAgentSessionId(undefined)
    }
  }

  const handleDeleteSession = async (id: string) => {
    await fetch("/api/chat/sessions", { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id }) })
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (currentSessionId === id) { setCurrentSessionId(null); setMessages([]); setAgentSessionId(undefined) }
  }

  const handleSelectSession = (id: string) => {
    setCurrentSessionId(id)
    const session = sessions.find((s) => s.id === id)
    if (session) {
      setMessages(session.messages)
      setAgentSessionId(session.agentSessionId)
    }
  }

  return (
    <div className="h-[calc(100vh-3.5rem)]">
      <ChatLayout sessions={sessions} currentSessionId={currentSessionId} model={model}
        messages={messages} isStreaming={isStreaming} onSelectSession={handleSelectSession}
        onNewSession={handleNewSession} onDeleteSession={handleDeleteSession}
        onModelChange={setModel} onSendMessage={sendMessage}
        onResolvePermission={resolvePermission} onCancelStream={cancelStream} />
    </div>
  )
}
