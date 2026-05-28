import { Wrench } from "lucide-react"
import { useState } from "react"

interface ToolCallCardProps { name: string; input?: string; output?: string }

export function ToolCallCard({ name, input, output }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="rounded-lg border bg-muted/30 p-3 my-2 text-sm">
      <button onClick={() => setExpanded(!expanded)} className="flex items-center gap-2 w-full text-left">
        <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="font-medium">{name}</span>
        <span className="text-xs text-muted-foreground ml-auto">{expanded ? "收起" : "展开"}</span>
      </button>
      {expanded && (input || output) && (
        <div className="mt-2 space-y-2">
          {input && <div><div className="text-xs text-muted-foreground mb-1">输入</div><pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-40">{input}</pre></div>}
          {output && <div><div className="text-xs text-muted-foreground mb-1">输出</div><pre className="text-xs bg-muted p-2 rounded overflow-x-auto max-h-40">{output}</pre></div>}
        </div>
      )}
    </div>
  )
}
