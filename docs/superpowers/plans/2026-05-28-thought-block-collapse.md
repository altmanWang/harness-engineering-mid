# Thought Block Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add collapsible thought-block rendering in the Workflow Chat so that AI thinking content over 6 lines is truncated with a gradient mask and expand/collapse toggle.

**Architecture:** Extend the `ChatMessage` type with `thoughtContent`, wire the existing SSE `thinking` event into the hook, and create a `ThoughtBlock` component that manages collapse state based on line count and streaming status.

**Tech Stack:** React 19, TypeScript, Tailwind CSS 3, lucide-react

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/types/chat.ts` | Modify | Add `thoughtContent` field to `ChatMessage` |
| `src/components/workflow/thought-block.tsx` | Create | New component: renders thought content with collapse/expand |
| `src/hooks/use-chat-stream.ts` | Modify | Handle `thinking` SSE event, accumulate `thoughtContent` |
| `src/components/workflow/chat-message.tsx` | Modify | Render `ThoughtBlock` in assistant messages |

---

### Task 1: Add `thoughtContent` to ChatMessage type

**Files:**
- Modify: `src/types/chat.ts:27-36`

- [ ] **Step 1: Add `thoughtContent` field to `ChatMessage` interface**

In `src/types/chat.ts`, add `thoughtContent` after the `content` field in the `ChatMessage` interface:

```typescript
export interface ChatMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  thoughtContent?: string
  timestamp: string
  toolCalls?: ToolCall[]
  permissionRequest?: PermissionRequest
  permissionDecision?: { optionId: string; label: string }
  isStreaming?: boolean
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors (field is optional).

- [ ] **Step 3: Commit**

```bash
git add src/types/chat.ts
git commit -m "feat: add thoughtContent field to ChatMessage type"
```

---

### Task 2: Handle `thinking` SSE event in use-chat-stream hook

**Files:**
- Modify: `src/hooks/use-chat-stream.ts:63`

- [ ] **Step 1: Replace the empty `thinking` event listener with content accumulation**

In `src/hooks/use-chat-stream.ts`, replace line 63:

```typescript
es.addEventListener("thinking", () => {})
```

with:

```typescript
es.addEventListener("thinking", (e) => {
  const data = JSON.parse(e.data)
  setMessages((prev) => prev.map((m) =>
    m.id === assistantMsgId
      ? { ...m, thoughtContent: (m.thoughtContent || "") + data.content }
      : m
  ))
})
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add src/hooks/use-chat-stream.ts
git commit -m "feat: accumulate thoughtContent from thinking SSE events"
```

---

### Task 3: Create ThoughtBlock component

**Files:**
- Create: `src/components/workflow/thought-block.tsx`

- [ ] **Step 1: Create the component**

Create `src/components/workflow/thought-block.tsx` with the following content:

```tsx
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
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/workflow/thought-block.tsx
git commit -m "feat: create ThoughtBlock component with collapse/expand"
```

---

### Task 4: Integrate ThoughtBlock into ChatMessage

**Files:**
- Modify: `src/components/workflow/chat-message.tsx`

- [ ] **Step 1: Add import and render ThoughtBlock in assistant messages**

In `src/components/workflow/chat-message.tsx`, add the import at the top:

```typescript
import { ThoughtBlock } from "./thought-block"
```

Then, inside the assistant message rendering block (after the opening `<div className={cn("rounded-lg px-3 py-2...">` and before the content `<div className="whitespace-pre-wrap...">`), add:

```tsx
{message.thoughtContent && (
  <ThoughtBlock content={message.thoughtContent} isStreaming={!!message.isStreaming} />
)}
```

The full assistant message section should look like:

```tsx
<div className={cn("rounded-lg px-3 py-2 max-w-[80%] text-sm", isUser ? "bg-primary text-primary-foreground" : "bg-card border")}>
  {message.thoughtContent && (
    <ThoughtBlock content={message.thoughtContent} isStreaming={!!message.isStreaming} />
  )}
  <div className="whitespace-pre-wrap break-words">{message.content || (message.isStreaming ? "..." : "")}</div>
  {message.isStreaming && <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5" />}
</div>
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/workflow/chat-message.tsx
git commit -m "feat: render ThoughtBlock in assistant chat messages"
```

---

### Task 5: Manual verification

**Files:** None (testing only)

- [ ] **Step 1: Start dev server**

Run: `cd harness-engineering && npm run dev`

- [ ] **Step 2: Open the Workflow page and send a message**

Open `http://localhost:3000/workflow`, send a message to the AI. Verify:

1. When thinking content arrives (streaming), it shows fully without collapse
2. After streaming ends and content exceeds 6 lines, it auto-collapses with gradient mask
3. Clicking "展开全部 ▼" expands to show all content
4. Clicking "收起 ▲" collapses back to 6 lines
5. Short thinking content (under 6 lines) shows fully with no toggle button

- [ ] **Step 3: Verify no regressions**

Check that normal text messages, permission cards, and tool call cards still render correctly.

- [ ] **Step 4: Commit (no code changes expected, skip if clean)**

---

## Self-Review

**Spec coverage:**
- Type extension (thoughtContent): Task 1 ✓
- Hook wiring (thinking event): Task 2 ✓
- ThoughtBlock component: Task 3 ✓
- ChatMessage integration: Task 4 ✓
- Collapse threshold 6 lines: Task 3 (COLLAPSE_THRESHOLD = 6) ✓
- Gradient mask: Task 3 ✓
- Stream-then-collapse: Task 3 (isStreaming guard) ✓
- Expand/collapse buttons: Task 3 ✓

**Placeholder scan:** No TBD, TODO, or vague steps found.

**Type consistency:** `thoughtContent?: string` defined in Task 1, used consistently in Task 2 (hook) and Task 4 (component). `ThoughtBlockProps` with `content: string` and `isStreaming: boolean` defined in Task 3, used in Task 4 with matching types.
