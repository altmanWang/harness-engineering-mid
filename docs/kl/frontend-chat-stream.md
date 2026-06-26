# 前端 — 聊天流 (Chat Stream)

## 文件

`frontend/src/composables/useChatStream.ts`

## 两步 SSE 模式

```
Step 1: POST /api/chat/stream
  → 返回 { chatId: "chat-..." }

Step 2: EventSource GET /api/chat/stream?id=<chatId>
  → 接收 SSE 事件流
```

## 接口定义

```ts
interface UseChatStreamOptions {
  sessionId: string
  model: string
  agentSessionId?: string
  onAgentSessionIdChange?: (id: string) => void
  onDone?: () => void | Promise<void>
}
```

## 返回值

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `messages` | `Ref<ChatMessage[]>` | 消息列表 |
| `isStreaming` | `Ref<boolean>` | 是否正在流式传输 |
| `pendingPermission` | `Ref<PermissionRequest \| null>` | 待处理的权限请求 |
| `sendMessage(content)` | `async` | 发送消息并开始流 |
| `resolvePermission(reqId, optId)` | `async` | 解决权限请求 |
| `cancelStream()` | `async` | 取消当前流 |

## sendMessage 流程

1. 创建 user 消息 → push 到 messages
2. 创建 assistant 占位消息 (isStreaming: true)
3. `POST /api/chat/stream` → 获取 chatId
4. 打开 `EventSource('/api/chat/stream?id=' + chatId)`
5. 监听 SSE 事件:

| SSE Event | 处理 |
|-----------|------|
| `delta` | 追加 content 到 assistant 消息 |
| `thinking` | 追加 thoughtContent 到 assistant 消息 |
| `permission_request` | 设置 pendingPermission + push 权限消息 |
| `done` | 更新 agentSessionId, 结束 streaming, 调用 onDone |
| `failed` | 显示错误信息, 关闭 EventSource |
| `engine_error` | 显示引擎错误, 不关闭流 |
| `onerror` | 关闭流, 结束 streaming |

## 权限处理

```ts
resolvePermission(requestId, optionId)
  → 清除 pendingPermission
  → 更新消息的 permissionDecision
  → POST /api/chat/permission { requestId, optionId }
```

## 在 HomeView 中的使用

```ts
const { messages, isStreaming, sendMessage, resolvePermission, cancelStream }
  = useChatStream({
      get sessionId() { return chatStore.currentSessionId || '' },
      get model() { return chatStore.model },
      get agentSessionId() { return chatStore.agentSessionId },
      onAgentSessionIdChange(id) { chatStore.setAgentSessionId(id) },
      async onDone() { await chatStore.loadSessions() },
    })
```

双向同步: `messages` ↔ `chatStore.messages` 通过 watch 保持同步。
