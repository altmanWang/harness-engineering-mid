import { Activity, BarChart3, Sparkles, Bot } from "lucide-react"
import type { DashboardStats } from "@/types"

const iconMap = {
  totalCalls: Activity,
  dailyAvg: BarChart3,
  skillCount: Sparkles,
  agentCount: Bot,
}

const labelMap: Record<keyof DashboardStats, string> = {
  totalCalls: "总调用量",
  dailyAvg: "日均调用",
  skillCount: "Skills 数",
  agentCount: "Agents 数",
}

export function StatsCards({ stats }: { stats: DashboardStats }) {
  const entries = Object.entries(stats) as [keyof DashboardStats, number][]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {entries.map(([key, value]) => {
        const Icon = iconMap[key]
        return (
          <div key={key} className="rounded-lg border bg-card p-6">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">{labelMap[key]}</span>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="mt-2 text-2xl font-bold">{value.toLocaleString()}</div>
          </div>
        )
      })}
    </div>
  )
}
