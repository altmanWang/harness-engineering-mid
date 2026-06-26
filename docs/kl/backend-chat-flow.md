# 后端 — 聊天流 API

## 文件

`backend/app/routers/chat.py`

## 架构

聊天流使用**两步模式**: 先 POST 启动聊天获取 chatId，再 GET 建立 SSE 连接接收事件。

### 模块级状态

```python
_active_chats: dict[str, asyncio.Task]       # chatId → 后台任务
_stream_queues: dict[str, list[asyncio.Queue]] # chatId → SSE 监听队列列表
```

---

## POST /api/chat/stream (start_chat)

### 请求体 (SendMessageRequest)

```json
{
  "message": "用户输入",
  "model": "claude-sonnet-4-6",
  "sessionId": "session-...",
  "agentSessionId": "..."  // 可选, 用于恢复会话
}
```

### 处理流程

```
1. 校验 message 非空
2. 生成 chatId = "chat-{unix_ms}"
3. get_or_create_engine(sessionId) → 从引擎池获取/创建引擎
4. register_stream(chatId, sessionId, "opencode") → 创建 StreamState
5. 如果有 sessionId → append_message (user 消息) 到 session store
6. 注册 on_engine_stream 回调:
   - text → append_stream_content + _stream_event("delta")
   - thought → _stream_event("thinking")
   - permission_request → register_pending_permission + _stream_event("permission_request")
   - error → _stream_event("engine_error")
7. engine.execute({prompt, model, workingDirectory, sessionId}) → 后台 asyncio.Task
8. 任务完成后: append_message (assistant 消息) + update_session_agent_id
9. 注册 30 秒延迟清理: 移除 _active_chats + remove_stream
```

### 响应

```json
{ "chatId": "chat-1750000000000" }
```

---

## GET /api/chat/stream?id=<chatId> (stream_chat)

### 处理流程

```
1. 从 _active_chats 获取后台任务 (404 如果不存在)
2. 创建 asyncio.Queue → 加入 _stream_queues[chatId]
3. 读取 StreamState.stream_content 作为缓冲内容
4. 返回 StreamingResponse (text/event-stream)
```

### SSE 事件序列

```
event: connected
data: {"chatId":"chat-..."}

event: delta                          ← 缓冲内容 (如果有)
data: {"content":"..."}

event: delta / thinking / permission_request / engine_error  ← 实时事件
data: {...}

event: done                           ← 任务完成
data: {"result":"...", "sessionId":"...", "isError":false}
```

或失败时:

```
event: failed
data: {"message":"error description"}
```

### 轮询机制

- 从 queue 获取事件，0.1s 超时
- 超时后检查 task.done()
- 如果 task 完成 → 发送 done/failed 事件 → 退出循环
- 退出后 0.5s 延迟 → 清理队列

---

## DELETE /api/chat/stream?id=<chatId> (cancel_chat)

1. 取消 asyncio.Task (如果未完成)
2. 从 _active_chats 移除
3. remove_stream(id)

---

## POST /api/chat/permission (resolve_permission_route)

### 请求体

```json
{
  "requestId": "perm-...",
  "optionId": "allow"
}
```

### 流程

1. 校验 requestId 和 optionId 非空
2. `resolve_permission(requestId, optionId)` → 从权限队列查找 → 调用 engine.resolve_permission()
3. 返回 `{"resolved": true}`
