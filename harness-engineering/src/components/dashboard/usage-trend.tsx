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
