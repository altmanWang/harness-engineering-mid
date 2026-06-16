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
