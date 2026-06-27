# 后端 — 会话存储

## 文件

`backend/app/services/session_store.py`

## 存储方式

- **格式**: 文件 JSON (aiofiles 异步 I/O)
- **路径**: `data/chat-sessions/{session_id}.json`
- **编码**: UTF-8

## 核心函数

| 函数 | 说明 |
|------|------|
| `list_sessions()` | 遍历目录 → 解析 JSON → 按 updatedAt 降序排序 |
| `get_session(session_id)` | 读取单个 JSON 文件 → 反序列化为 ChatSession |
| `save_session(session)` | 序列化 → 写入文件, auto-update updatedAt |
| `delete_session(session_id)` | `path.unlink()` 删除文件 |
| `append_message(session_id, message)` | 加载 → push message → auto-set title (首条 user 消息前50字) → save |
| `update_message(session_id, message_id, updates)` | 加载 → 查找 message → merge updates → save |
| `update_session_agent_id(session_id, agent_session_id)` | 加载 → 设置 agentSessionId → save |

## 会话 ID 格式

```
session-{unix_ms}-{6位随机字符}
例: session-1782307250728-p0gc9u
```

## 消息 ID 格式

```
msg-{unix_ms}
例: msg-1782307250728
```

## 目录自动创建

首次写入时通过 `_ensure_dir()` 自动创建 `data/chat-sessions/` 目录。

## Session JSON 示例

```json
{
  "id": "session-1782307250728-p0gc9u",
  "type": "chat",
  "title": "帮我分析一下贵州茅台",
  "engine": "opencode",
  "model": "claude-sonnet-4-6",
  "agentSessionId": "agent-session-uuid",
  "messages": [
    {
      "id": "msg-1782307250728",
      "role": "user",
      "content": "帮我分析一下贵州茅台",
      "timestamp": "2025-06-24T10:00:00+00:00"
    },
    {
      "id": "msg-assistant-chat-1782307251000",
      "role": "assistant",
      "content": "贵州茅台(600519)是...",
      "timestamp": "2025-06-24T10:00:15+00:00"
    }
  ],
  "diagnosis": null,
  "createdAt": "2025-06-24T10:00:00+00:00",
  "updatedAt": "2025-06-24T10:00:15+00:00"
}
```
