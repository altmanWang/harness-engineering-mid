import { cn } from "@/lib/utils"
import type { Skill } from "@/types"
import * as LucideIcons from "lucide-react"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function DynamicIcon({ name, ...props }: { name: string } & any) {
  const icons = LucideIcons as unknown as Record<string, React.ComponentType<any>>
  const Icon = icons[name]
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
