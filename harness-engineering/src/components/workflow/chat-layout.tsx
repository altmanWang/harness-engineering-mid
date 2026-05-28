"use client"

import { ChatSidebar } from "./chat-sidebar"
import { ChatStream } from "./chat-stream"
import { ChatInput } from "./chat-input"
import { EngineInfo } from "./engine-info"
import type { ChatSession, ChatMessage } from "@/types/chat"

interface ChatLayoutProps {
  sessions: ChatSession[]; currentSessionId: string | null; model: string
  messages: ChatMessage[]; isStreaming: boolean
  onSelectSession: (id: string) => void; onNewSession: () => void; onDeleteSession: (id: string) => void
  onModelChange: (model: string) => void
  onSendMessage: (content: string) => void; onResolvePermission: (requestId: string, optionId: string) => void; onCancelStream: () => void
}

export function ChatLayout({ sessions, currentSessionId, model, messages, isStreaming,
  onSelectSession, onNewSession, onDeleteSession, onModelChange, onSendMessage, onResolvePermission, onCancelStream }: ChatLayoutProps) {
  return (
    <div className="flex h-full">
      <ChatSidebar sessions={sessions} currentSessionId={currentSessionId} model={model}
        onSelectSession={onSelectSession} onNewSession={onNewSession} onDeleteSession={onDeleteSession}
        onModelChange={onModelChange} />
      <div className="flex-1 flex flex-col min-w-0">
        <EngineInfo engineName="OpenCode" modelName={model} />
        <ChatStream messages={messages} onResolvePermission={onResolvePermission} />
        <ChatInput onSend={onSendMessage} isStreaming={isStreaming} onCancel={onCancelStream} />
      </div>
    </div>
  )
}
