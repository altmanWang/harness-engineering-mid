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
