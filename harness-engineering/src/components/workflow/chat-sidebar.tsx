"use client"

import { useState, useEffect } from "react"
import type { ChatSession, EngineAvailability, ModelInfo } from "@/types/chat"
import { Plus, Trash2, Cpu } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatSidebarProps {
  sessions: ChatSession[]; currentSessionId: string | null; model: string
  onSelectSession: (id: string) => void; onNewSession: () => void; onDeleteSession: (id: string) => void
  onModelChange: (model: string) => void
}

export function ChatSidebar({ sessions, currentSessionId, model, onSelectSession, onNewSession, onDeleteSession, onModelChange }: ChatSidebarProps) {
  const [engineInfo, setEngineInfo] = useState<EngineAvailability | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/engines/availability").then((r) => r.json()).then((data) => {
      const engines: EngineAvailability[] = data.engines || []
      setEngineInfo(engines[0] || null)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (engineInfo?.defaultModel && !model) {
      onModelChange(engineInfo.defaultModel)
    }
  }, [engineInfo, model, onModelChange])

  return (
    <div className="w-64 border-r bg-card flex flex-col h-full">
      <div className="p-3 border-b">
        <button onClick={onNewSession} className="flex items-center gap-2 w-full px-3 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90">
          <Plus className="h-4 w-4" />新建会话
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map((session) => (
          <div key={session.id} onClick={() => onSelectSession(session.id)}
            className={cn("flex items-center justify-between px-3 py-2 rounded-md text-sm cursor-pointer",
              session.id === currentSessionId ? "bg-accent text-accent-foreground" : "hover:bg-accent/50")}>
            <span className="truncate flex-1">{session.title || "新会话"}</span>
            <button onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id) }}
              className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive">
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
      <div className="border-t p-3 space-y-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground"><Cpu className="h-3.5 w-3.5" /><span>模型</span></div>
        <select value={model} onChange={(e) => onModelChange(e.target.value)} className="w-full rounded-md border bg-background px-2 py-1.5 text-sm">
          {(engineInfo?.models || []).map((m: ModelInfo) => <option key={m.id} value={m.id}>{m.name}</option>)}
          {(!engineInfo || engineInfo.models.length === 0) && !loading && <option value="" disabled>未检测到模型</option>}
        </select>
      </div>
    </div>
  )
}
