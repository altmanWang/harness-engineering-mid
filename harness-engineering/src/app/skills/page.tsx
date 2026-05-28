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
