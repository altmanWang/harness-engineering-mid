# Harness Engineering - Design Spec

## 概述

基于 ACEHarness 技术栈，新建 `harness-engineering` 项目，实现一个 Web 平台，包含 Skills/Agents 市场和使用情况看板。数据全部打桩。

## 技术栈

- Next.js 16 + React 18 + TypeScript 5
- Tailwind CSS + shadcn/ui（组件库）
- Recharts（图表）
- Lucide React（图标）

## 项目结构

```
harness-engineering/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 根布局：Providers + 顶部导航栏
│   │   ├── page.tsx            # 首页重定向到 /dashboard
│   │   ├── dashboard/
│   │   │   └── page.tsx        # 看板页面
│   │   ├── skills/
│   │   │   └── page.tsx        # Skills 市场页面
│   │   └── agents/
│   │       └── page.tsx        # Agents 市场页面
│   ├── components/
│   │   ├── layout/
│   │   │   └── navbar.tsx      # 顶部导航栏（Dashboard/Skills/Agents）
│   │   ├── dashboard/
│   │   │   ├── stats-cards.tsx      # 调用量统计卡片
│   │   │   ├── usage-trend.tsx      # 30天趋势图
│   │   │   └── usage-ranking.tsx    # 使用排行榜
│   │   ├── skills/
│   │   │   ├── skill-card.tsx       # Skill 卡片
│   │   │   └── skill-filter.tsx     # 分类筛选 + 搜索
│   │   └── agents/
│   │       ├── agent-card.tsx       # Agent 卡片
│   │       └── agent-filter.tsx     # 分类筛选 + 搜索
│   ├── lib/
│   │   └── mock-data.ts       # 打桩数据
│   └── types/
│       └── index.ts            # 类型定义
├── package.json
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## 数据模型

```typescript
// Skill 和 Agent 共用基础类型
interface MarketItem {
  id: string
  name: string
  description: string
  tags: string[]          // 分类标签，如 ["代码生成", "测试"]
  icon: string            // Lucide 图标名称
  usageCount: number      // 总使用次数
  lastUsedAt: string      // 最近使用时间 ISO
}

type Skill = MarketItem
type Agent = MarketItem

// 看板统计
interface DashboardStats {
  totalCalls: number      // 近30天总调用次数
  dailyAvg: number        // 日均调用次数
  skillCount: number      // Skills 总数
  agentCount: number      // Agents 总数
}

// 趋势数据（近30天每日）
interface TrendPoint {
  date: string            // "2026-05-27"
  skills: number          // 当日 Skills 调用量
  agents: number          // 当日 Agents 调用量
}

// 排行榜条目
interface RankingItem {
  id: string
  name: string
  type: "skill" | "agent"
  callCount: number
}
```

打桩数据：约 12 个 Skills、8 个 Agents，标签涵盖代码生成、测试、部署、文档、数据分析等。30天趋势数据随机生成合理调用量。

## 页面设计

### 布局方案

独立路由页面，顶部导航栏切换，与 ACEHarness 一致。

- `/dashboard` — 看板
- `/skills` — Skills 市场
- `/agents` — Agents 市场

### Dashboard 看板

- **4 个统计卡片**：总调用量、日均调用、Skills 数、Agents 数，一行排列
- **30 天调用趋势图**：双折线图（Skills/Agents），占满宽度
- **排行榜**：左右两列，Skills Top 5 和 Agents Top 5

### Skills 市场

- **搜索框 + 标签筛选**（多选）
- **卡片网格**：3-4 列响应式布局
- **卡片内容**：图标、名称、描述、标签

### Agents 市场

结构与 Skills 市场相同，展示 Agent 卡片，标签按 Agent 类别划分（编码助手、运维助手、测试助手等）。

## 导航栏

所有页面共享顶部导航栏，包含：
- 左侧：Dashboard / Skills / Agents 链接，当前页面高亮
- 右侧：主题切换、用户菜单

## 无后端

所有数据为打桩数据，定义在 `src/lib/mock-data.ts`，无 API 调用、无数据库。
