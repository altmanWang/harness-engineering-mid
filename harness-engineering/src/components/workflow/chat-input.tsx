"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Square } from "lucide-react"

interface ChatInputProps { onSend: (message: string) => void; isStreaming: boolean; onCancel: () => void }

export function ChatInput({ onSend, isStreaming, onCancel }: ChatInputProps) {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  const handleSubmit = () => { if (!input.trim() || isStreaming) return; onSend(input.trim()); setInput("") }
  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit() } }

  return (
    <div className="border-t bg-card p-4">
      <div className="flex items-end gap-2">
        <textarea ref={textareaRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)" disabled={isStreaming} rows={1}
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-50" />
        {isStreaming ? (
          <button onClick={onCancel} className="p-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90"><Square className="h-4 w-4" /></button>
        ) : (
          <button onClick={handleSubmit} disabled={!input.trim()} className="p-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"><Send className="h-4 w-4" /></button>
        )}
      </div>
    </div>
  )
}
