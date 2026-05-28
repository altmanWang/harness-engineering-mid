# Harness Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Next.js web platform with Skills/Agents marketplace and usage dashboard, using stub data.

**Architecture:** Next.js App Router with three independent route pages sharing a top navbar. All data is stubbed in a single mock-data module. UI built with shadcn/ui + Tailwind, charts with Recharts.

**Tech Stack:** Next.js 16, React 18, TypeScript 5, Tailwind CSS, shadcn/ui, Recharts, Lucide React

---

## File Map

| File | Responsibility |
|------|---------------|
| `package.json` | Project dependencies and scripts |
| `next.config.js` | Next.js configuration |
| `tailwind.config.ts` | Tailwind + shadcn/ui theme config |
| `tsconfig.json` | TypeScript config |
| `postcss.config.js` | PostCSS config for Tailwind |
| `src/types/index.ts` | All shared type definitions |
| `src/lib/mock-data.ts` | Stub data: skills, agents, stats, trend, ranking |
| `src/app/layout.tsx` | Root layout with navbar |
| `src/app/page.tsx` | Redirect to /dashboard |
| `src/components/layout/navbar.tsx` | Top navigation bar |
| `src/app/dashboard/page.tsx` | Dashboard page composing stats, trend, ranking |
| `src/components/dashboard/stats-cards.tsx` | 4 stat cards row |
| `src/components/dashboard/usage-trend.tsx` | 30-day dual-line chart |
| `src/components/dashboard/usage-ranking.tsx` | Skills/Agents top 5 ranking |
| `src/app/skills/page.tsx` | Skills marketplace page |
| `src/components/skills/skill-card.tsx` | Single skill card |
| `src/components/skills/skill-filter.tsx` | Search + tag filter |
| `src/app/agents/page.tsx` | Agents marketplace page |
| `src/components/agents/agent-card.tsx` | Single agent card |
| `src/components/agents/agent-filter.tsx` | Search + tag filter |
| `src/lib/utils.ts` | cn() utility for className merging |

---

### Task 1: Initialize Project

**Files:**
- Create: `package.json`
- Create: `next.config.js`
- Create: `tsconfig.json`
- Create: `tailwind.config.ts`
- Create: `postcss.config.js`
- Create: `src/app/globals.css`

- [ ] **Step 1: Create project directory and initialize package.json**

```bash
cd D:/codes/harness/harness-engineering
npm init -y
```

- [ ] **Step 2: Install dependencies**

```bash
npm install next@latest react@latest react-dom@latest
npm install recharts lucide-react clsx tailwind-merge
npm install -D typescript @types/react @types/react-dom @types/node tailwindcss postcss autoprefixer
```

- [ ] **Step 3: Create next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {}

module.exports = nextConfig
```

- [ ] **Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 5: Create tailwind.config.ts**

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

- [ ] **Step 6: Install tailwindcss-animate**

```bash
npm install -D tailwindcss-animate
```

- [ ] **Step 7: Create postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 8: Create src/app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * { @apply border-border; }
  body { @apply bg-background text-foreground; }
}
```

- [ ] **Step 9: Add scripts to package.json**

Update the `scripts` section of `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: initialize project with Next.js, Tailwind, and base config"
```

---

### Task 2: Types and Utility

**Files:**
- Create: `src/types/index.ts`
- Create: `src/lib/utils.ts`

- [ ] **Step 1: Create src/types/index.ts**

```typescript
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
```

- [ ] **Step 2: Create src/lib/utils.ts**

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 3: Commit**

```bash
git add src/types/index.ts src/lib/utils.ts
git commit -m "feat: add type definitions and utility function"
```

---

### Task 3: Mock Data

**Files:**
- Create: `src/lib/mock-data.ts`

- [ ] **Step 1: Create src/lib/mock-data.ts**

```typescript
import type { Skill, Agent, DashboardStats, TrendPoint, RankingItem } from "@/types"

export const skills: Skill[] = [
  { id: "s1", name: "代码生成", description: "根据需求描述自动生成代码片段和函数实现", tags: ["代码生成"], icon: "Code", usageCount: 2340, lastUsedAt: "2026-05-27T10:30:00Z" },
  { id: "s2", name: "单元测试", description: "自动为指定函数生成单元测试用例", tags: ["测试"], icon: "TestTube", usageCount: 1890, lastUsedAt: "2026-05-27T09:15:00Z" },
  { id: "s3", name: "代码审查", description: "AI 驱动的代码审查，发现潜在问题和优化建议", tags: ["代码生成"], icon: "Search", usageCount: 1560, lastUsedAt: "2026-05-26T16:45:00Z" },
  { id: "s4", name: "文档生成", description: "自动生成 API 文档和代码注释", tags: ["文档"], icon: "FileText", usageCount: 1200, lastUsedAt: "2026-05-26T14:20:00Z" },
  { id: "s5", name: "自动部署", description: "一键部署应用到指定环境", tags: ["部署"], icon: "Rocket", usageCount: 980, lastUsedAt: "2026-05-25T11:00:00Z" },
  { id: "s6", name: "数据迁移", description: "数据库 schema 迁移和数据转换工具", tags: ["数据", "部署"], icon: "Database", usageCount: 760, lastUsedAt: "2026-05-24T15:30:00Z" },
  { id: "s7", name: "性能分析", description: "分析代码性能瓶颈并提供优化建议", tags: ["代码生成"], icon: "Gauge", usageCount: 650, lastUsedAt: "2026-05-23T10:00:00Z" },
  { id: "s8", name: "接口测试", description: "自动生成 API 接口测试脚本", tags: ["测试"], icon: "Webhook", usageCount: 580, lastUsedAt: "2026-05-22T09:30:00Z" },
  { id: "s9", name: "安全扫描", description: "扫描代码中的安全漏洞和敏感信息泄露", tags: ["安全"], icon: "Shield", usageCount: 520, lastUsedAt: "2026-05-21T14:00:00Z" },
  { id: "s10", name: "日志分析", description: "智能分析应用日志，定位异常和错误", tags: ["数据"], icon: "ScrollText", usageCount: 450, lastUsedAt: "2026-05-20T16:30:00Z" },
  { id: "s11", name: "依赖管理", description: "检测项目依赖更新和版本冲突", tags: ["部署"], icon: "Package", usageCount: 380, lastUsedAt: "2026-05-19T11:15:00Z" },
  { id: "s12", name: "配置生成", description: "根据项目类型生成配置文件模板", tags: ["文档"], icon: "Settings", usageCount: 310, lastUsedAt: "2026-05-18T08:45:00Z" },
]

export const agents: Agent[] = [
  { id: "a1", name: "编码助手", description: "全栈编码助手，支持代码生成、重构和调试", tags: ["编码"], icon: "Bot", usageCount: 3210, lastUsedAt: "2026-05-27T11:00:00Z" },
  { id: "a2", name: "测试助手", description: "自动化测试编排，覆盖单元、集成和 E2E 测试", tags: ["测试"], icon: "FlaskConical", usageCount: 2100, lastUsedAt: "2026-05-27T10:00:00Z" },
  { id: "a3", name: "运维助手", description: "监控、告警和自动化运维操作", tags: ["运维"], icon: "Server", usageCount: 1680, lastUsedAt: "2026-05-26T15:30:00Z" },
  { id: "a4", name: "文档助手", description: "自动生成和维护项目文档", tags: ["文档"], icon: "BookOpen", usageCount: 1200, lastUsedAt: "2026-05-25T09:00:00Z" },
  { id: "a5", name: "安全助手", description: "安全审计、合规检查和漏洞修复建议", tags: ["安全"], icon: "ShieldCheck", usageCount: 890, lastUsedAt: "2026-05-24T14:00:00Z" },
  { id: "a6", name: "数据助手", description: "数据分析、可视化和报告生成", tags: ["数据"], icon: "BarChart3", usageCount: 750, lastUsedAt: "2026-05-23T10:30:00Z" },
  { id: "a7", name: "架构助手", description: "系统架构设计和代码结构优化", tags: ["编码"], icon: "Blocks", usageCount: 620, lastUsedAt: "2026-05-22T16:00:00Z" },
  { id: "a8", name: "DevOps 助手", description: "CI/CD 流水线编排和部署管理", tags: ["运维"], icon: "GitBranch", usageCount: 540, lastUsedAt: "2026-05-21T11:30:00Z" },
]

export const dashboardStats: DashboardStats = {
  totalCalls: 27890,
  dailyAvg: 930,
  skillCount: 12,
  agentCount: 8,
}

function generateTrendData(): TrendPoint[] {
  const data: TrendPoint[] = []
  const today = new Date(2026, 4, 27) // 2026-05-27
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().slice(0, 10)
    data.push({
      date: dateStr,
      skills: Math.floor(200 + Math.random() * 300),
      agents: Math.floor(150 + Math.random() * 250),
    })
  }
  return data
}

export const trendData: TrendPoint[] = generateTrendData()

export const skillRanking: RankingItem[] = skills
  .sort((a, b) => b.usageCount - a.usageCount)
  .slice(0, 5)
  .map(s => ({ id: s.id, name: s.name, type: "skill" as const, callCount: s.usageCount }))

export const agentRanking: RankingItem[] = agents
  .sort((a, b) => b.usageCount - a.usageCount)
  .slice(0, 5)
  .map(a => ({ id: a.id, name: a.name, type: "agent" as const, callCount: a.usageCount }))

export const skillTags: string[] = [...new Set(skills.flatMap(s => s.tags))]
export const agentTags: string[] = [...new Set(agents.flatMap(a => a.tags))]
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/mock-data.ts
git commit -m "feat: add mock data for skills, agents, stats, trend, and ranking"
```

---

### Task 4: Layout and Navbar

**Files:**
- Create: `src/components/layout/navbar.tsx`
- Create: `src/app/layout.tsx`
- Create: `src/app/page.tsx`

- [ ] **Step 1: Create src/components/layout/navbar.tsx**

```tsx
"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Sparkles, Bot, Moon, Sun } from "lucide-react"
import { useState } from "react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/skills", label: "Skills", icon: Sparkles },
  { href: "/agents", label: "Agents", icon: Bot },
]

export function Navbar() {
  const pathname = usePathname()
  const [dark, setDark] = useState(false)

  const toggleTheme = () => {
    setDark(!dark)
    document.documentElement.classList.toggle("dark")
  }

  return (
    <header className="h-14 border-b bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-1">
        <span className="font-semibold text-lg mr-4">Harness</span>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
      <button
        onClick={toggleTheme}
        className="p-2 rounded-md hover:bg-accent text-muted-foreground"
      >
        {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>
    </header>
  )
}
```

- [ ] **Step 2: Create src/app/layout.tsx**

```tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Navbar } from "@/components/layout/navbar"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Harness Engineering",
  description: "Skills and Agents marketplace with usage dashboard",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <body className={inter.className}>
        <div className="min-h-screen bg-background flex flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Create src/app/page.tsx**

```tsx
import { redirect } from "next/navigation"

export default function Home() {
  redirect("/dashboard")
}
```

- [ ] **Step 4: Verify dev server starts**

```bash
npm run dev
```

Open http://localhost:3000, should redirect to /dashboard (which will 404 — that's expected until Task 5).

- [ ] **Step 5: Commit**

```bash
git add src/components/layout/navbar.tsx src/app/layout.tsx src/app/page.tsx
git commit -m "feat: add root layout, navbar with navigation, and home redirect"
```

---

### Task 5: Dashboard Stats Cards

**Files:**
- Create: `src/components/dashboard/stats-cards.tsx`
- Create: `src/app/dashboard/page.tsx`

- [ ] **Step 1: Create src/components/dashboard/stats-cards.tsx**

```tsx
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
```

- [ ] **Step 2: Create src/app/dashboard/page.tsx (skeleton — will add trend and ranking in later tasks)**

```tsx
import { StatsCards } from "@/components/dashboard/stats-cards"
import { dashboardStats } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatsCards stats={dashboardStats} />
    </div>
  )
}
```

- [ ] **Step 3: Verify stats cards render**

```bash
npm run dev
```

Open http://localhost:3000/dashboard, should see 4 stat cards.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/stats-cards.tsx src/app/dashboard/page.tsx
git commit -m "feat: add dashboard stats cards"
```

---

### Task 6: Dashboard Usage Trend Chart

**Files:**
- Create: `src/components/dashboard/usage-trend.tsx`
- Modify: `src/app/dashboard/page.tsx`

- [ ] **Step 1: Create src/components/dashboard/usage-trend.tsx**

```tsx
"use client"

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts"
import type { TrendPoint } from "@/types"

export function UsageTrend({ data }: { data: TrendPoint[] }) {
  const chartData = data.map((d) => ({
    ...d,
    date: d.date.slice(5), // "05-27"
  }))

  return (
    <div className="rounded-lg border bg-card p-6">
      <h2 className="text-lg font-semibold mb-4">近30天调用趋势</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="date" className="text-xs" tick={{ fontSize: 12 }} />
          <YAxis className="text-xs" tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="skills" name="Skills" stroke="hsl(221, 83%, 53%)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="agents" name="Agents" stroke="hsl(142, 71%, 45%)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 2: Update src/app/dashboard/page.tsx to include trend chart**

Replace the full content of `src/app/dashboard/page.tsx`:

```tsx
import { StatsCards } from "@/components/dashboard/stats-cards"
import { UsageTrend } from "@/components/dashboard/usage-trend"
import { dashboardStats, trendData } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatsCards stats={dashboardStats} />
      <UsageTrend data={trendData} />
    </div>
  )
}
```

- [ ] **Step 3: Verify trend chart renders**

```bash
npm run dev
```

Open http://localhost:3000/dashboard, should see dual-line chart.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/usage-trend.tsx src/app/dashboard/page.tsx
git commit -m "feat: add 30-day usage trend chart to dashboard"
```

---

### Task 7: Dashboard Ranking

**Files:**
- Create: `src/components/dashboard/usage-ranking.tsx`
- Modify: `src/app/dashboard/page.tsx`

- [ ] **Step 1: Create src/components/dashboard/usage-ranking.tsx**

```tsx
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
```

- [ ] **Step 2: Update src/app/dashboard/page.tsx to include ranking**

Replace the full content of `src/app/dashboard/page.tsx`:

```tsx
import { StatsCards } from "@/components/dashboard/stats-cards"
import { UsageTrend } from "@/components/dashboard/usage-trend"
import { UsageRanking } from "@/components/dashboard/usage-ranking"
import { dashboardStats, trendData, skillRanking, agentRanking } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <StatsCards stats={dashboardStats} />
      <UsageTrend data={trendData} />
      <UsageRanking skillRanking={skillRanking} agentRanking={agentRanking} />
    </div>
  )
}
```

- [ ] **Step 3: Verify dashboard is complete**

```bash
npm run dev
```

Open http://localhost:3000/dashboard, should see stats cards + trend chart + ranking.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/usage-ranking.tsx src/app/dashboard/page.tsx
git commit -m "feat: add usage ranking to dashboard, dashboard page complete"
```

---

### Task 8: Skills Marketplace Page

**Files:**
- Create: `src/components/skills/skill-card.tsx`
- Create: `src/components/skills/skill-filter.tsx`
- Create: `src/app/skills/page.tsx`

- [ ] **Step 1: Create src/components/skills/skill-card.tsx**

```tsx
import { cn } from "@/lib/utils"
import type { Skill } from "@/types"
import * as LucideIcons from "lucide-react"

function DynamicIcon({ name, ...props }: { name: string } & React.SVGProps<SVGSVGElement>) {
  const Icon = (LucideIcons as Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>>)[name]
  if (!Icon) return <LucideIcons.Sparkles {...props} />
  return <Icon {...props} />
}

export function SkillCard({ skill }: { skill: Skill }) {
  return (
    <div className="rounded-lg border bg-card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
          <DynamicIcon name={skill.icon} className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-sm">{skill.name}</h3>
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{skill.description}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {skill.tags.map((tag) => (
          <span key={tag} className={cn(
            "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
            "bg-secondary text-secondary-foreground"
          )}>
            {tag}
          </span>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create src/components/skills/skill-filter.tsx**

```tsx
"use client"

import { useState } from "react"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

interface SkillFilterProps {
  tags: string[]
  selectedTags: string[]
  onTagChange: (tags: string[]) => void
  searchQuery: string
  onSearchChange: (query: string) => void
}

export function SkillFilter({ tags, selectedTags, onTagChange, searchQuery, onSearchChange }: SkillFilterProps) {
  const [showAll, setShowAll] = useState(false)

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      onTagChange(selectedTags.filter((t) => t !== tag))
    } else {
      onTagChange([...selectedTags, tag])
    }
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="搜索 Skills..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full rounded-md border bg-background pl-9 pr-4 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onTagChange([])}
          className={cn(
            "rounded-md px-3 py-1 text-sm font-medium transition-colors",
            selectedTags.length === 0
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          全部
        </button>
        {tags.map((tag) => (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            className={cn(
              "rounded-md px-3 py-1 text-sm font-medium transition-colors",
              selectedTags.includes(tag)
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create src/app/skills/page.tsx**

```tsx
"use client"

import { useState, useMemo } from "react"
import { SkillCard } from "@/components/skills/skill-card"
import { SkillFilter } from "@/components/skills/skill-filter"
import { skills, skillTags } from "@/lib/mock-data"

export default function SkillsPage() {
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")

  const filtered = useMemo(() => {
    return skills.filter((s) => {
      const matchTags = selectedTags.length === 0 || selectedTags.some((t) => s.tags.includes(t))
      const matchSearch = searchQuery === "" || s.name.toLowerCase().includes(searchQuery.toLowerCase()) || s.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchTags && matchSearch
    })
  }, [selectedTags, searchQuery])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Skills 市场</h1>
      <SkillFilter
        tags={skillTags}
        selectedTags={selectedTags}
        onTagChange={setSelectedTags}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((skill) => (
          <SkillCard key={skill.id} skill={skill} />
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center text-muted-foreground py-12">没有找到匹配的 Skill</div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Verify skills page renders**

```bash
npm run dev
```

Open http://localhost:3000/skills, should see filter bar + card grid.

- [ ] **Step 5: Commit**

```bash
git add src/components/skills/skill-card.tsx src/components/skills/skill-filter.tsx src/app/skills/page.tsx
git commit -m "feat: add skills marketplace page with card grid and filter"
```

---

### Task 9: Agents Marketplace Page

**Files:**
- Create: `src/components/agents/agent-card.tsx`
- Create: `src/components/agents/agent-filter.tsx`
- Create: `src/app/agents/page.tsx`

- [ ] **Step 1: Create src/components/agents/agent-card.tsx**

```tsx
import { cn } from "@/lib/utils"
import type { Agent } from "@/types"
import * as LucideIcons from "lucide-react"

function DynamicIcon({ name, ...props }: { name: string } & React.SVGProps<SVGSVGElement>) {
  const Icon = (LucideIcons as Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>>)[name]
  if (!Icon) return <LucideIcons.Bot {...props} />
  return <Icon {...props} />
}

export function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="rounded-lg border bg-card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
          <DynamicIcon name={agent.icon} className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-sm">{agent.name}</h3>
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{agent.description}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {agent.tags.map((tag) => (
          <span key={tag} className={cn(
            "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
            "bg-secondary text-secondary-foreground"
          )}>
            {tag}
          </span>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create src/components/agents/agent-filter.tsx**

```tsx
"use client"

import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentFilterProps {
  tags: string[]
  selectedTags: string[]
  onTagChange: (tags: string[]) => void
  searchQuery: string
  onSearchChange: (query: string) => void
}

export function AgentFilter({ tags, selectedTags, onTagChange, searchQuery, onSearchChange }: AgentFilterProps) {
  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      onTagChange(selectedTags.filter((t) => t !== tag))
    } else {
      onTagChange([...selectedTags, tag])
    }
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="搜索 Agents..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full rounded-md border bg-background pl-9 pr-4 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onTagChange([])}
          className={cn(
            "rounded-md px-3 py-1 text-sm font-medium transition-colors",
            selectedTags.length === 0
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          全部
        </button>
        {tags.map((tag) => (
          <button
            key={tag}
            onClick={() => toggleTag(tag)}
            className={cn(
              "rounded-md px-3 py-1 text-sm font-medium transition-colors",
              selectedTags.includes(tag)
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create src/app/agents/page.tsx**

```tsx
"use client"

import { useState, useMemo } from "react"
import { AgentCard } from "@/components/agents/agent-card"
import { AgentFilter } from "@/components/agents/agent-filter"
import { agents, agentTags } from "@/lib/mock-data"

export default function AgentsPage() {
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")

  const filtered = useMemo(() => {
    return agents.filter((a) => {
      const matchTags = selectedTags.length === 0 || selectedTags.some((t) => a.tags.includes(t))
      const matchSearch = searchQuery === "" || a.name.toLowerCase().includes(searchQuery.toLowerCase()) || a.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchTags && matchSearch
    })
  }, [selectedTags, searchQuery])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Agents 市场</h1>
      <AgentFilter
        tags={agentTags}
        selectedTags={selectedTags}
        onTagChange={setSelectedTags}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center text-muted-foreground py-12">没有找到匹配的 Agent</div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Verify all pages work**

```bash
npm run dev
```

Navigate between /dashboard, /skills, /agents. All should render correctly.

- [ ] **Step 5: Commit**

```bash
git add src/components/agents/agent-card.tsx src/components/agents/agent-filter.tsx src/app/agents/page.tsx
git commit -m "feat: add agents marketplace page with card grid and filter"
```

---

### Task 10: Build Verification

- [ ] **Step 1: Run production build**

```bash
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 2: Start production server and verify**

```bash
npm run start
```

Open http://localhost:3000, verify all three pages work correctly.

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: resolve build issues"
```
