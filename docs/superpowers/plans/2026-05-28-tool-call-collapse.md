# Tool Call Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire tool-call and tool-result SSE events from engine through to the UI, rendering them as collapsible ToolCallCard components in the chat.

**Architecture:** The engine already emits `tool-call` and `tool-call-update` events (via `opencode-wrapper.ts`), but currently they are emitted as `type: "text"` events. We need to emit proper `tool_call` / `tool_result` stream events from the engine wrapper, forward them through the SSE route, handle them in the hook, and render via the existing ToolCallCard component.

**Tech Stack:** React 19, TypeScript, Tailwind CSS 3, lucide-react, Server-Sent Events

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/lib/engines/engine-interface.ts` | Modify | Add `tool_call` and `tool_result` to `EngineStreamEvent.type` union |
| `src/lib/engines/opencode-wrapper.ts` | Modify | Emit `tool_call` / `tool_result` events instead of `text` for tool calls |
| `src/app/api/chat/stream/route.ts` | Modify | Forward `tool_call` / `tool_result` events as SSE |
| `src/types/chat.ts` | Modify | Add `id` to `ToolCall` interface |
| `src/hooks/use-chat-stream.ts` | Modify | Listen for `tool_call` / `tool_result` SSE events |
| `src/components/workflow/chat-message.tsx` | Modify | Render ToolCallCard list in assistant messages |

---

### Task 1: Extend EngineStreamEvent type and update opencode-wrapper

**Files:**
- Modify: `src/lib/engines/engine-interface.ts:3-4`
- Modify: `src/lib/engines/opencode-wrapper.ts:93-113`

- [ ] **Step 1: Update EngineStreamEvent type union**

In `src/lib/engines/engine-interface.ts`, change line 4 from:

```typescript
type: "text" | "thought" | "tool" | "permission_request" | "error"
```

to:

```typescript
type: "text" | "thought" | "tool_call" | "tool_result" | "permission_request" | "error"
```

- [ ] **Step 2: Update opencode-wrapper to emit proper tool events**

In `src/lib/engines/opencode-wrapper.ts`, replace the `tool-call` event handler (lines 93-101):

```typescript
this.engine.on("tool-call", (tc: any) => {
  if (!this.streaming) return
  const toolId = tc.id || ""
  if (toolId && !this.seenToolIds.has(toolId)) {
    this.seenToolIds.add(toolId)
    const formatted = `\n\n**🔧 ${tc.title || "Tool"}**\n`
    this.collectedOutput += formatted
    this.emit("stream", { type: "text", content: formatted, metadata: tc } as EngineStreamEvent)
  }
})
```

with:

```typescript
this.engine.on("tool-call", (tc: any) => {
  if (!this.streaming) return
  const toolId = tc.id || ""
  if (toolId && !this.seenToolIds.has(toolId)) {
    this.seenToolIds.add(toolId)
    this.emit("stream", { type: "tool_call", content: "", metadata: { id: toolId, name: tc.title || tc.name || "Tool", input: tc.input || "" } } as EngineStreamEvent)
  }
})
```

Then replace the `tool-call-update` event handler (lines 103-112):

```typescript
this.engine.on("tool-call-update", (tu: any) => {
  if (!this.streaming) return
  if (tu.status === "completed" || tu.status === "failed") {
    const output = typeof tu.rawOutput === "string" ? tu.rawOutput : tu.rawOutput?.output || ""
    if (output) {
      const formatted = `\n\`\`\`\n${output}\n\`\`\`\n`
      this.collectedOutput += formatted
      this.emit("stream", { type: "text", content: formatted, metadata: tu } as EngineStreamEvent)
    }
  }
})
```

with:

```typescript
this.engine.on("tool-call-update", (tu: any) => {
  if (!this.streaming) return
  if (tu.status === "completed" || tu.status === "failed") {
    const output = typeof tu.rawOutput === "string" ? tu.rawOutput : tu.rawOutput?.output || ""
    this.emit("stream", { type: "tool_result", content: "", metadata: { id: tu.id, output, status: tu.status } } as EngineStreamEvent)
  }
})
```

Key changes: tool events no longer append to `collectedOutput` or emit as `type: "text"`. They emit as proper `tool_call` / `tool_result` types.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
git add src/lib/engines/engine-interface.ts src/lib/engines/opencode-wrapper.ts
git commit -m "feat: emit tool_call and tool_result engine stream events"
```

---

### Task 2: Forward tool_call / tool_result events in SSE route

**Files:**
- Modify: `src/app/api/chat/stream/route.ts:34-46` (POST handler onEngineStream)
- Modify: `src/app/api/chat/stream/route.ts:93-98` (GET handler onEngineStream)

- [ ] **Step 1: Add tool event forwarding in POST handler**

In `src/app/api/chat/stream/route.ts`, in the `onEngineStream` callback inside POST (around line 34), add after the `thought` handling block and before the `permission_request` block:

```typescript
} else if (evt.type === "tool_call" && evt.metadata) {
  const tc = evt.metadata
  engineStreamEvents.emit(chatId, { type: "tool_call", toolCallId: tc.id, toolName: tc.name, input: tc.input })
} else if (evt.type === "tool_result" && evt.metadata) {
  const tu = evt.metadata
  engineStreamEvents.emit(chatId, { type: "tool_result", toolCallId: tu.id, output: tu.output, status: tu.status })
}
```

- [ ] **Step 2: Add tool event forwarding in GET handler**

In the same file, in the `onEngineStream` callback inside GET (around line 93), add after the `thinking` handling and before the `permission_request` block:

```typescript
else if (evt.type === "tool_call") send("tool_call", { toolCallId: evt.toolCallId, toolName: evt.toolName, input: evt.input })
else if (evt.type === "tool_result") send("tool_result", { toolCallId: evt.toolCallId, output: evt.output, status: evt.status })
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
git add src/app/api/chat/stream/route.ts
git commit -m "feat: forward tool_call and tool_result SSE events"
```

---

### Task 3: Add id field to ToolCall type and handle tool events in hook

**Files:**
- Modify: `src/types/chat.ts:21-25`
- Modify: `src/hooks/use-chat-stream.ts` (after line 70, before line 72)

- [ ] **Step 1: Add `id` field to `ToolCall` interface**

In `src/types/chat.ts`, change the `ToolCall` interface from:

```typescript
export interface ToolCall {
  name: string
  input: string
  output?: string
}
```

to:

```typescript
export interface ToolCall {
  id?: string
  name: string
  input: string
  output?: string
}
```

- [ ] **Step 2: Add tool_call and tool_result event listeners in hook**

In `src/hooks/use-chat-stream.ts`, after the `thinking` event listener (ending at line 70) and before the `permission_request` listener (line 72), add:

```typescript
es.addEventListener("tool_call", (e) => {
  const data = JSON.parse(e.data)
  setMessages((prev) => prev.map((m) =>
    m.id === assistantMsgId
      ? { ...m, toolCalls: [...(m.toolCalls || []), { id: data.toolCallId, name: data.toolName, input: data.input }] }
      : m
  ))
})

es.addEventListener("tool_result", (e) => {
  const data = JSON.parse(e.data)
  setMessages((prev) => prev.map((m) =>
    m.id === assistantMsgId
      ? { ...m, toolCalls: (m.toolCalls || []).map((tc) => tc.id === data.toolCallId ? { ...tc, output: data.output } : tc) }
      : m
  ))
})
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
git add src/types/chat.ts src/hooks/use-chat-stream.ts
git commit -m "feat: add ToolCall id field and handle tool SSE events in hook"
```

---

### Task 4: Render ToolCallCard in ChatMessage

**Files:**
- Modify: `src/components/workflow/chat-message.tsx`

- [ ] **Step 1: Add ToolCallCard import**

In `src/components/workflow/chat-message.tsx`, add after the existing imports:

```typescript
import { ToolCallCard } from "./tool-call-card"
```

- [ ] **Step 2: Render ToolCallCard list in assistant messages**

In the same file, after the `ThoughtBlock` rendering block and before the content `<div className="whitespace-pre-wrap...">`, add:

```tsx
{message.toolCalls && message.toolCalls.length > 0 && (
  <div className="space-y-2 mb-2">
    {message.toolCalls.map((tc, i) => (
      <ToolCallCard key={tc.id || i} name={tc.name} input={tc.input} output={tc.output} />
    ))}
  </div>
)}
```

The full assistant message bubble should now look like:

```tsx
<div className={cn("rounded-lg px-3 py-2 max-w-[80%] text-sm", isUser ? "bg-primary text-primary-foreground" : "bg-card border")}>
  {message.thoughtContent && (
    <ThoughtBlock content={message.thoughtContent} isStreaming={!!message.isStreaming} />
  )}
  {message.toolCalls && message.toolCalls.length > 0 && (
    <div className="space-y-2 mb-2">
      {message.toolCalls.map((tc, i) => (
        <ToolCallCard key={tc.id || i} name={tc.name} input={tc.input} output={tc.output} />
      ))}
    </div>
  )}
  <div className="whitespace-pre-wrap break-words">{message.content || (message.isStreaming ? "..." : "")}</div>
  {message.isStreaming && <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5" />}
</div>
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd harness-engineering && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
git add src/components/workflow/chat-message.tsx
git commit -m "feat: render ToolCallCard list in assistant chat messages"
```

---

### Task 5: Manual verification

**Files:** None (testing only)

- [ ] **Step 1: Start dev server**

Run: `cd harness-engineering && npm run dev`

- [ ] **Step 2: Open the Workflow page and test**

Open `http://localhost:3000/workflow`, send a message that triggers tool use. Verify:

1. Tool calls appear as collapsed cards (only title bar visible with tool name + "展开")
2. Clicking the title bar expands to show input and output
3. Clicking again collapses
4. Multiple tool calls each have their own card
5. Thought blocks (if present) appear above tool call cards
6. Final response text appears below tool call cards

- [ ] **Step 3: Verify no regressions**

Normal text messages, permission cards, and thought blocks still render correctly.

---

## Self-Review

**Spec coverage:**
- SSE event forwarding (route.ts): Task 2 ✓
- SSE event types: Not needed as separate task — the events are forwarded as plain JSON objects, not using the `SSEEvent` type ✓
- ToolCall id field: Task 3 ✓
- Hook handling: Task 3 ✓
- ChatMessage rendering: Task 4 ✓
- ToolCallCard changes: Not needed (spec says "无需修改") ✓
- Rendering order (Thought → ToolCalls → Content): Task 4 ✓
- Default collapsed: Existing ToolCallCard already does this ✓

**Placeholder scan:** No TBD, TODO, or vague steps found.

**Type consistency:**
- `ToolCall.id?: string` defined in Task 3, used in Task 3 (hook: `data.toolCallId`) and Task 4 (key: `tc.id || i`)
- Engine stream event types `tool_call` / `tool_result` defined in Task 1 (engine-interface), used in Task 1 (opencode-wrapper), forwarded in Task 2 (route.ts)
- `toolCallId`, `toolName`, `input` property names consistent across Task 2 (emit) and Task 3 (parse)
