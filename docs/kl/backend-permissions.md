# 后端 — 权限队列

## 文件

`backend/app/services/permission_queue.py`

## 概述

简单的内存权限请求注册与解决机制，作为 SSE 流式聊天中权限请求的桥梁。

## 数据结构

```python
_pending_permissions: dict[str, Any]  # request_id → engine 实例
```

## 核心函数

| 函数 | 说明 |
|------|------|
| `register_pending_permission(request_id, engine)` | 注册 request_id → engine 映射 |
| `resolve_permission(request_id, option_id) -> bool` | 查找 engine → 调用 engine.resolve_permission(option_id) → 从 dict 移除 → 返回是否找到 |

## 完整流程

```
1. opencode 发出权限请求
   ↓
2. ACPEngine._handle_permission()
   → 存储 _permission_resolver 闭包
   → emit "permission" 事件
   ↓
3. OpenCodeEngineWrapper.on_permission()
   → emit EngineStreamEvent(type="permission_request")
   ↓
4. chat.py on_engine_stream 回调
   → register_pending_permission(request["id"], engine)
   → _stream_event("permission_request", {request})
   ↓
5. 前端 EventSource 收到 permission_request 事件
   → 显示权限卡片 UI
   ↓
6. 用户点击选项 → 前端 POST /api/chat/permission
   ↓
7. chat.py resolve_permission_route()
   → resolve_permission(requestId, optionId)
   ↓
8. permission_queue.resolve_permission()
   → engine.resolve_permission(optionId)
   ↓
9. OpenCodeEngineWrapper.resolve_permission()
   → ACPEngine.resolve_permission()
   ↓
10. ACPEngine 调用 _permission_resolver 闭包
    → 发送 JSON-RPC 响应回 opencode
```

## 特点

- 纯内存, 服务重启后丢失
- 简单 dict 映射, 无 TTL/超时机制
- resolve 后自动清理
