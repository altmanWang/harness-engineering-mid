import { Bot, Cpu } from "lucide-react"

interface EngineInfoProps { engineName: string; modelName: string }

export function EngineInfo({ engineName, modelName }: EngineInfoProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 border-b bg-card text-sm">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        <Bot className="h-3.5 w-3.5" /><span>{engineName}</span>
      </div>
      <div className="flex items-center gap-1.5 text-muted-foreground">
        <Cpu className="h-3.5 w-3.5" /><span>{modelName}</span>
      </div>
    </div>
  )
}
