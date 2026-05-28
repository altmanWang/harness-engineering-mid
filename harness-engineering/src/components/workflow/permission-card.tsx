"use client"

import type { PermissionRequest } from "@/types/chat"
import { Shield, Check, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface PermissionCardProps {
  request: PermissionRequest
  decision?: { optionId: string; label: string }
  onResolve?: (requestId: string, optionId: string) => void
}

export function PermissionCard({ request, decision, onResolve }: PermissionCardProps) {
  const resolved = !!decision
  return (
    <div className={cn(
      "rounded-lg border p-4 my-2",
      resolved ? "bg-muted/50" : "bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800"
    )}>
      <div className="flex items-center gap-2 mb-2">
        <Shield className="h-4 w-4 text-amber-600" />
        <span className="font-medium text-sm">Agent 请求权限</span>
        {resolved && <span className="text-xs text-muted-foreground ml-auto">已决策</span>}
      </div>
      <div className="text-sm mb-1"><span className="font-medium">操作：</span><span className="text-muted-foreground">{request.description}</span></div>
      <div className="text-sm mb-3"><span className="font-medium">内容：</span><code className="text-xs bg-muted px-1 py-0.5 rounded">{request.detail.slice(0, 200)}</code></div>
      <div className="flex gap-2">
        {request.options.map((option) => (
          <button key={option.id} disabled={resolved} onClick={() => onResolve?.(request.id, option.id)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              resolved && decision?.optionId === option.id && "ring-2 ring-offset-1",
              option.style === "danger"
                ? "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400"
                : option.style === "primary"
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
              resolved && "opacity-60 cursor-not-allowed"
            )}>
            {option.style === "danger" ? <X className="h-3 w-3 inline mr-1" /> : <Check className="h-3 w-3 inline mr-1" />}
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
