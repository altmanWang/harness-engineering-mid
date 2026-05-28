# 思考过程折叠展示设计

## 概述

在 Workflow Chat 中，AI 的思考过程（thinking）内容可能很长。需要支持折叠/展开，避免长内容挤占聊天区域。

## 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 折叠样式 | 渐变遮罩 + 行数截断 | 流畅自然，不突兀 |
| 折叠阈值 | 6 行 | 紧凑但能预览 |
| 流式阶段 | 全部展示，流式结束后自动折叠 | 避免思考过程中内容跳动 |
| 展开/收起 | 点击"展开全部 ▼" / "收起 ▲" | 简洁直观 |

## 行为规则

1. 不足 6 行：全部展示，无折叠控件
2. 超过 6 行：显示前 6 行 + 底部渐变遮罩 + "展开全部 ▼" 按钮
3. 流式输出中（`isStreaming=true`）：始终全部展示，不折叠
4. 流式结束（`isStreaming=false`）：自动折叠到 6 行
5. 手动展开后：显示全部内容 + "收起 ▲" 按钮
6. 手动收起后：恢复 6 行截断 + 渐变遮罩

## 数据流改动

### 1. 类型扩展 — `src/types/chat.ts`

`ChatMessage` 新增字段：

```typescript
thoughtContent?: string
```

### 2. Hook 改动 — `src/hooks/use-chat-stream.ts`

当前 `thinking` 事件监听为空（第 63 行）：

```typescript
es.addEventListener("thinking", () => {})
```

改为累加思考内容到当前 assistant 消息：

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

### 3. 新组件 — `src/components/workflow/thought-block.tsx`

职责：渲染思考内容，管理折叠/展开状态。

Props：
- `content: string` — 思考文本
- `isStreaming: boolean` — 是否流式中

核心逻辑：
- 用 `useRef` 测量内容行数（或用行数分割 + max-height 方案）
- `isStreaming` 为 true 时：全部展示，无折叠
- `isStreaming` 为 false 且超过 6 行时：折叠显示
- 渐变遮罩用 CSS `linear-gradient` + `pointer-events-none` 叠加层实现

### 4. 消息组件改动 — `src/components/workflow/chat-message.tsx`

在 assistant 消息中，正文之前渲染 `ThoughtBlock`：

```tsx
{message.thoughtContent && (
  <ThoughtBlock content={message.thoughtContent} isStreaming={!!message.isStreaming} />
)}
```

## 视觉规格

- 容器：`rounded-lg border bg-muted/30 p-3`，与 ToolCallCard 一致
- 图标：💭 或用 lucide 的 `Brain` 图标，紫色 `text-purple-400`
- 标题：`💭 思考过程`
- 内容：`text-sm whitespace-pre-wrap break-words text-muted-foreground`
- 渐变遮罩：`bg-gradient-to-b from-transparent to-muted/30`，高度 48px
- 折叠时 max-height 通过 CSS clamp 实现 6 行截断
- 展开按钮：居中，`text-xs text-purple-400 hover:text-purple-300`

## 不做的事

- 不持久化思考内容到 session store（与现有行为一致）
- 不支持部分折叠（只做全部展开/收起）
- 不添加复制思考内容的功能
