# 后端 — 引擎抽象层

## 三层架构

```
Engine (ABC)                          ← 抽象接口层
  └── OpenCodeEngineWrapper           ← 实现适配层
        └── ACPEngine                  ← 传输协议层
              └── subprocess: opencode acp
```

---

## 第一层: Engine 接口 (`engine_interface.py`)

```python
@dataclass
class EngineStreamEvent:
    type: str      # "text" | "thought" | "tool" | "permission_request" | "error"
    content: str
    metadata: Any = None

class Engine(ABC):
    @abstractmethod
    def get_name(self) -> str: ...
    @abstractmethod
    async def execute(self, options: dict) -> dict: ...
    @abstractmethod
    def cancel(self) -> None: ...
    @abstractmethod
    async def is_available(self) -> bool: ...
    @abstractmethod
    def resolve_permission(self, option_id: str) -> None: ...
    @abstractmethod
    def on(self, event: str, listener: Callable) -> None: ...
    @abstractmethod
    def off(self, event: str, listener: Callable) -> None: ...
```

---

## 第二层: OpenCodeEngineWrapper (`opencode_wrapper.py`)

实现 `Engine` 接口，包装 `ACPEngine`。

### execute(options) 流程

1. 清除 tool ID 去重集合和输出缓冲
2. 如果 prompt 以 `/` 开头 → 去掉 (防止被 opencode 当作 slash command)
3. 判断是否可复用: sessionId 相同 + engine 存活
4. 不可复用时: 停止旧 engine → 创建新 ACPEngine → start → create_session 或 resume_session
5. 设置 model (如果指定)
6. `engine.send_prompt(prompt)` → 流式收集输出
7. 返回 `{success, output, sessionId, stopReason}` 或 `{success: false, output, error}`

### 事件处理 (_setup_engine_events)

| ACP 事件 | 处理逻辑 |
|----------|---------|
| `agent-message` | 提取 text/content → 追加到 _collected_output → emit text event |
| `agent-thought` | 提取 text/content → emit thought event |
| `tool-call` | 去重 (by id) → 格式化 `**🔧 {title}**` → emit text event |
| `tool-call-update` | completed/failed 时 → 格式化 rawOutput 为 markdown code block |
| `permission` | 构建 PermissionRequest 对象 (含 style 推断) → emit permission_request |
| `error` | emit error event |

### 权限选项 style 推断

```python
if any(kw in opt_id.lower() for kw in ("deny", "reject", "block")):
    style = "danger"
elif any(kw in opt_id.lower() for kw in ("allow", "accept", "always")):
    style = "primary"
else:
    style = "default"
```

### is_available()

- Windows: `where opencode`
- Unix: `command -v opencode`

---

## 第三层: ACPEngine (`acp_engine.py`)

通过 **ACP 协议 (Agent Communication Protocol)** 与 `opencode` CLI 通信。

### 通信方式

- 子进程: `opencode acp --cwd <workingDirectory>`
- 传输: JSON-RPC 2.0 over stdin/stdout (newline-delimited JSON)
- Windows: `shell=True`

### 生命周期

| 方法 | JSON-RPC 调用 | 说明 |
|------|-------------|------|
| `start()` | — | spawn 子进程, 启动 read_loop |
| `_initialize()` | `initialize` | 握手: protocolVersion=1, capabilities |
| `create_session()` | `session/new` | 创建新会话 → 返回 sessionId + models |
| `resume_session(id)` | `session/load` | 恢复已有会话 |
| `send_prompt(prompt)` | `session/prompt` | 发送提示 → 返回 stopReason |
| `set_model(model)` | `session/set_model` | 切换模型 |
| `cancel_session()` | `session/cancel` | 取消当前会话 |
| `stop()` | — | kill 子进程 |

### 消息处理 (_read_loop)

- 从 stdout 逐行读取 JSON
- 有 `id` → 匹配 pending request → resolve Future
- 有 `method` (通知):
  - `session/update` / `sessionUpdate` → `_handle_session_update`
  - `session/request_permission` / `requestPermission` → `_handle_permission`

### 会话更新分发

| 通知类型 | 发出事件 |
|----------|---------|
| `agent_message_chunk` | `"agent-message"` |
| `agent_thought_chunk` | `"agent-thought"` |
| `tool_call` | `"tool-call"` |
| `tool_call_update` | `"tool-call-update"` |

### 权限处理

- 收到权限通知 → emit `"permission"` 事件 + 存储 `_permission_resolver` 闭包
- `resolve_permission(optionId)` → 调用闭包 → 发送 JSON-RPC 响应

---

## 引擎工厂 (`engine_factory.py`)

### 引擎池

```python
_engine_pool: dict[str, dict]  # sessionKey → {engine, lastUsed}
ENGINE_POOL_TTL = 600  # 10 分钟
```

### 关键函数

| 函数 | 说明 |
|------|------|
| `get_or_create_engine(sessionKey)` | 池命中 → 更新 lastUsed; 池未命中 → create_engine → 入池 |
| `create_engine()` | 创建 OpenCodeEngineWrapper, 检查 is_available() |
| `detect_engines()` | 读取 `~/.config/opencode/opencode.json` 获取模型列表 |
| `_cleanup_loop()` | 后台每 60s 清理过期引擎 (10 分钟未用) |
