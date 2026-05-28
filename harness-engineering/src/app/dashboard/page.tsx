import { StatsCards } from "@/components/dashboard/stats-cards"
import { UsageTrend } from "@/components/dashboard/usage-trend"
import { UsageRanking } from "@/components/dashboard/usage-ranking"
import { WorkflowCard } from "@/components/dashboard/workflow-card"
import { dashboardStats, trendData, skillRanking, agentRanking } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatsCards stats={dashboardStats} />
      <UsageTrend data={trendData} />
      <UsageRanking skillRanking={skillRanking} agentRanking={agentRanking} />
      <WorkflowCard />
    </div>
  )
}
