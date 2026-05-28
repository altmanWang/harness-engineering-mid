import type { ChatMessage as ChatMessageType } from "@/types/chat"
import { PermissionCard } from "./permission-card"
import { cn } from "@/lib/utils"
import { User, Bot } from "lucide-react"

interface ChatMessageProps { message: ChatMessageType; onResolvePermission?: (requestId: string, optionId: string) => void }

export function ChatMessage({ message, onResolvePermission }: ChatMessageProps) {
  const isUser = message.role === "user"

  if (message.permissionRequest) {
    return (
      <div className="flex justify-start px-4 py-1">
        <div className="max-w-[80%]">
          <PermissionCard request={message.permissionRequest} decision={message.permissionDecision} onResolve={onResolvePermission} />
        </div>
      </div>
    )
  }

  return (
    <div className={cn("flex gap-3 px-4 py-2", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-primary shrink-0 mt-1">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={cn("rounded-lg px-3 py-2 max-w-[80%] text-sm", isUser ? "bg-primary text-primary-foreground" : "bg-card border")}>
        <div className="whitespace-pre-wrap break-words">{message.content || (message.isStreaming ? "..." : "")}</div>
        {message.isStreaming && <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5" />}
      </div>
      {isUser && (
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-secondary text-secondary-foreground shrink-0 mt-1">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}
