export interface MarketItem {
  id: string
  name: string
  description: string
  tags: string[]
  icon: string
  usageCount: number
  lastUsedAt: string
}

export type Skill = MarketItem
export type Agent = MarketItem

export interface DashboardStats {
  totalCalls: number
  dailyAvg: number
  skillCount: number
  agentCount: number
}

export interface TrendPoint {
  date: string
  skills: number
  agents: number
}

export interface RankingItem {
  id: string
  name: string
  type: "skill" | "agent"
  callCount: number
}
