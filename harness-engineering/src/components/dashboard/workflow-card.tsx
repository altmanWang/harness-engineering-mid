import Link from "next/link"
import { Rocket } from "lucide-react"

export function WorkflowCard() {
  return (
    <div className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
          <Rocket className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold">工作流</h3>
          <p className="text-sm text-muted-foreground mt-1">启动 AI Agent 对话，支持 Claude Code / OpenCode</p>
        </div>
      </div>
      <div className="mt-4">
        <Link href="/workflow" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
          进入工作流 →
        </Link>
      </div>
    </div>
  )
}
