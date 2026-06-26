# 前端 — 状态管理 (Stores)

## chatStore (`stores/chat.ts`)

Pinia store, id: `'chat'`

### State

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sessions` | `ChatSession[]` | `[]` | 所有会话 |
| `currentSessionId` | `string \| null` | `null` | 当前活跃会话 ID |
| `messages` | `ChatMessage[]` | `[]` | 当前会话的消息列表 |
| `isStreaming` | `boolean` | `false` | 是否正在流式传输 |
| `pendingPermission` | `PermissionRequest \| null` | `null` | 待处理权限 |
| `model` | `string` | `'claude-sonnet-4-6'` | 当前模型 |
| `agentSessionId` | `string \| undefined` | `undefined` | OpenCode agent 会话 ID |

### Actions

| 方法 | 说明 |
|------|------|
| `setSessions(list)` | 直接设置会话列表 |
| `loadSessions()` | GET /api/chat/sessions → setSessions |
| `selectSession(id)` | 选中会话, 加载其 messages/agentSessionId/model |
| `createSession()` | POST /api/chat/sessions → 加入列表 → selectSession |
| `deleteSession(id)` | DELETE /api/chat/sessions → 从列表移除 → 如当前则 clearSession |
| `clearSession()` | 重置 currentSessionId, messages, agentSessionId |
| `setModel(model)` | 设置当前模型 |
| `setAgentSessionId(id)` | 设置 agentSessionId, 更新 sessions 中对应项 |

---

## engineStore (`stores/engine.ts`)

Pinia store, id: `'engine'`

### State

| 字段 | 类型 | 默认值 |
|------|------|--------|
| `engineInfo` | `EngineAvailability \| null` | `null` |
| `loading` | `boolean` | `false` |

### Actions

| 方法 | 说明 |
|------|------|
| `fetchAvailability()` | GET /api/engines/availability → 取第一个 engine 作为 engineInfo |
