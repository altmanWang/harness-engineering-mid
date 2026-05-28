# 工具调用折叠展示设计

## 概述

在 Workflow Chat 中，AI 的工具调用（tool call）和结果需要以折叠卡片形式展示，避免长内容挤占聊天区域。当前 `ToolCallCard` 组件已有折叠功能但未被使用，需要接通数据流并集成渲染。

## 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 折叠样式 | 标题栏展开/收起 | 业界常见模式，与现有 ToolCallCard 一致 |
| 默认状态 | 折叠 | 工具调用细节通常不需要立即查看 |
| 流式阶段 | 立即显示（折叠状态） | 用户能看到工具正在执行 |

## 行为规则

1. 工具调用默认折叠，只显示标题栏（🔧 工具名称 + 展开/收起）
2. 点击标题栏展开，显示输入和输出内容
3. 再次点击收起
4. 流式阶段工具调用到达时立即显示（折叠状态）
5. 工具结果到达时更新对应卡片的输出内容

## 数据流改动

### 1. SSE 事件转发 — `src/app/api/chat/stream/route.ts`

后端引擎已发出 `tool-call` 和 `tool-call-update` 事件（见 `opencode-wrapper.ts:93-113`），但 `route.ts` 的 `onEngineStream` 没有转发。

在 `onEngineStream` 中增加：

```typescript
} else if (evt.type === "tool-call" && evt.metadata) {
  const tc = evt.metadata
  engineStreamEvents.emit(chatId, { type: "tool_call", toolCallId: tc.id, toolName: tc.title || tc.name || "Tool", input: tc.input || "" })
} else if (evt.type === "tool-call-update" && evt.metadata) {
  const tu = evt.metadata
  const output = typeof tu.rawOutput === "string" ? tu.rawOutput : tu.rawOutput?.output || ""
  engineStreamEvents.emit(chatId, { type: "tool_result", toolCallId: tu.id, output, status: tu.status })
}
```

在 GET handler 的 `onEngineStream` 中增加对应的 SSE 发送：

```typescript
else if (evt.type === "tool_call") send("tool_call", { toolCallId: evt.toolCallId, toolName: evt.toolName, input: evt.input })
else if (evt.type === "tool_result") send("tool_result", { toolCallId: evt.toolCallId, output: evt.output, status: evt.status })
```

### 2. SSE 事件类型 — `src/types/chat.ts`

`SSEEvent` 联合类型新增：

```typescript
| { type: "tool_call"; messageId: string; toolName: string; input: string }
| { type: "tool_result"; messageId: string; output: string }
```

### 3. Hook 改动 — `src/hooks/use-chat-stream.ts`

监听 `tool_call` 和 `tool_result` 事件：

- `tool_call` 事件：在当前 assistant 消息的 `toolCalls` 数组中追加一条记录
- `tool_result` 事件：更新对应 `toolCallId` 的输出

```typescript
es.addEventListener("tool_call", (e) => {
  const data = JSON.parse(e.data)
  setMessages((prev) => prev.map((m) =>
    m.id === assistantMsgId
      ? { ...m, toolCalls: [...(m.toolCalls || []), { name: data.toolName, input: data.input }] }
      : m
  ))
})

es.addEventListener("tool_result", (e) => {
  const data = JSON.parse(e.data)
  setMessages((prev) => prev.map((m) =>
    m.id === assistantMsgId
      ? { ...m, toolCalls: (m.toolCalls || []).map((tc, i) => i === (m.toolCalls || []).length - 1 ? { ...tc, output: data.output } : tc) }
      : m
  ))
})
```

注意：由于 `ToolCall` 类型没有 `id` 字段，匹配方式需要改进。在 `ToolCall` 类型中增加可选的 `id` 字段用于匹配。

### 4. 类型扩展 — `src/types/chat.ts`

`ToolCall` 接口增加 `id` 字段：

```typescript
export interface ToolCall {
  id?: string
  name: string
  input: string
  output?: string
}
```

### 5. 消息组件改动 — `src/components/workflow/chat-message.tsx`

在 assistant 消息中，`ThoughtBlock` 之后、正文之前渲染工具调用卡片：

```tsx
{message.toolCalls && message.toolCalls.length > 0 && (
  <div className="space-y-2 mb-2">
    {message.toolCalls.map((tc, i) => (
      <ToolCallCard key={tc.id || i} name={tc.name} input={tc.input} output={tc.output} />
    ))}
  </div>
)}
```

需要新增 `import { ToolCallCard } from "./tool-call-card"`。

### 6. ToolCallCard 微调 — `src/components/workflow/tool-call-card.tsx`

现有组件功能基本满足需求，只需确保：
- 默认折叠（当前已经是 `useState(false)` 即折叠状态）
- 样式与 ThoughtBlock 一致（已是 `rounded-lg border bg-muted/30 p-3`）

无需修改，现有实现已满足。

## 渲染顺序

assistant 消息气泡内的渲染顺序：
1. ThoughtBlock（思考过程）
2. ToolCallCard 列表（工具调用）
3. 正文内容（最终回复）

## 不做的事

- 不修改 ToolCallCard 的折叠交互方式
- 不添加工具调用的状态指示器（loading/success/error 图标）
- 不支持工具调用的流式输入显示
