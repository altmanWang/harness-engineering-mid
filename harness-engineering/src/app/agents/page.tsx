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
