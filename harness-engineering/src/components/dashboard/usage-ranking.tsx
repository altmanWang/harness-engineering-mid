import type { RankingItem } from "@/types"
import { Trophy } from "lucide-react"

function RankingList({ title, items }: { title: string; items: RankingItem[] }) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Trophy className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      <ol className="space-y-3">
        {items.map((item, index) => (
          <li key={item.id} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold">
                {index + 1}
              </span>
              <span className="text-sm font-medium">{item.name}</span>
            </div>
            <span className="text-sm text-muted-foreground">{item.callCount.toLocaleString()} 次</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

export function UsageRanking({
  skillRanking,
  agentRanking,
}: {
  skillRanking: RankingItem[]
  agentRanking: RankingItem[]
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <RankingList title="Skills 排行 Top 5" items={skillRanking} />
      <RankingList title="Agents 排行 Top 5" items={agentRanking} />
    </div>
  )
}
