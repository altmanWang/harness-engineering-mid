"use client"

import { useRef, useEffect } from "react"
import type { ChatMessage as ChatMessageType } from "@/types/chat"
import { ChatMessage } from "./chat-message"

interface ChatStreamProps { messages: ChatMessageType[]; onResolvePermission?: (requestId: string, optionId: string) => void }

export function ChatStream({ messages, onResolvePermission }: ChatStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages])

  return (
    <div className="flex-1 overflow-y-auto py-4">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">开始对话吧...</div>
      )}
      {messages.map((msg) => <ChatMessage key={msg.id} message={msg} onResolvePermission={onResolvePermission} />)}
      <div ref={bottomRef} />
    </div>
  )
}
