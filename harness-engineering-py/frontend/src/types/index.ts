export interface MarketItem {
  id: string
  name: string
  description: string
  tags: string[]
  icon: string
  usageCount: number
  lastUsedAt: string
}

export interface Skill {
  id: string
  name: string
  description: string
  tags: string[]
  fileName: string
  fileSize: number
  createdAt: string
}

export type Agent = MarketItem
