"use client"

import { useState, useEffect, useRef } from "react"
import { Brain } from "lucide-react"

interface ThoughtBlockProps {
  content: string
  isStreaming: boolean
}

const COLLAPSE_THRESHOLD = 6
const LINE_HEIGHT = 24 // approximate px per line at text-sm

export function ThoughtBlock({ content, isStreaming }: ThoughtBlockProps) {
  const [expanded, setExpanded] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)
  const [needsCollapse, setNeedsCollapse] = useState(false)

  useEffect(() => {
    if (!contentRef.current) return
    const lineCount = Math.round(contentRef.current.scrollHeight / LINE_HEIGHT)
    setNeedsCollapse(lineCount > COLLAPSE_THRESHOLD)
  }, [content])

  useEffect(() => {
    if (isStreaming) setExpanded(false)
  }, [isStreaming])

  const shouldCollapse = needsCollapse && !expanded && !isStreaming

  return (
    <div className="rounded-lg border bg-muted/30 p-3 my-2 text-sm">
      <div className="flex items-center gap-1.5 text-purple-400 mb-2">
        <Brain className="h-3.5 w-3.5" />
        <span className="text-xs font-medium">思考过程</span>
      </div>
      <div className="relative">
        <div
          ref={contentRef}
          className="whitespace-pre-wrap break-words text-muted-foreground text-sm leading-6"
          style={shouldCollapse ? { maxHeight: COLLAPSE_THRESHOLD * LINE_HEIGHT, overflow: "hidden" } : undefined}
        >
          {content}
        </div>
        {shouldCollapse && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-b from-transparent to-muted/30 pointer-events-none" />
        )}
      </div>
      {needsCollapse && !isStreaming && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs text-purple-400 hover:text-purple-300 w-full text-center"
        >
          {expanded ? "收起 ▲" : "展开全部 ▼"}
        </button>
      )}
    </div>
  )
}
