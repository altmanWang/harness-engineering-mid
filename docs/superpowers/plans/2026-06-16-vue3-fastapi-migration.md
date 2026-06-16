# Vue 3 + FastAPI 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 Next.js 16 应用迁移为 Vue 3 + FastAPI 前后端分离架构，3 个页面（Skills、Agents、Workflow），功能等价。

**Architecture:** FastAPI 后端通过子进程驱动 OpenCode ACP，SSE 流式推送到 Vue 3 前端。Skills/Agents 页面使用 mock 数据纯前端渲染。Pinia 管理全局状态，composables 封装聊天 SSE 逻辑。

**Tech Stack:** Vue 3 + Vite + Element Plus + Pinia + TypeScript | FastAPI + uvicorn + Pydantic + aiofiles

---

## Part 1: Backend (FastAPI)

### Task 1: Backend 项目脚手架

**Files:**
- Create: `harness-engineering-py/backend/requirements.txt`
- Create: `harness-engineering-py/backend/pyproject.toml`
- Create: `harness-engineering-py/backend/app/__init__.py`
- Create: `harness-engineering-py/backend/app/main.py`
- Create: `harness-engineering-py/backend/app/models/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
aiofiles>=24.0.0
```

- [ ] **Step 2: 创建 pyproject.toml**

```toml
[project]
name = "harness-engineering-backend"
version = "1.0.0"
description = "Harness Engineering FastAPI backend"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0.0",
    "aiofiles>=24.0.0",
]
```

- [ ] **Step 3: 创建 app/__init__.py** (空文件)

- [ ] **Step 4: 创建 app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sessions, chat, engines

app = FastAPI(title="Harness Engineering API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(engines.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建 app/models/__init__.py** (空文件)

- [ ] **Step 6: 验证项目可启动**

```bash
cd harness-engineering-py/backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000 &
sleep 2
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
cd harness-engineering-py
git init
git add backend/
git commit -m "feat: scaffold FastAPI backend project"
```

---

### Task 2: Pydantic 数据模型

**Files:**
- Create: `harness-engineering-py/backend/app/models/schemas.py`

- [ ] **Step 1: 创建 schemas.py**

```python
from pydantic import BaseModel, Field
from typing import Optional, List


class PermissionOption(BaseModel):
    id: str
    label: str
    style: str = "default"  # "primary" | "danger" | "default"


class PermissionRequest(BaseModel):
    id: str
    type: str
    description: str
    detail: str
    options: List[PermissionOption] = []
    timestamp: str


class PermissionDecision(BaseModel):
    requestId: str
    optionId: str


class ToolCall(BaseModel):
    name: str
    input: str
    output: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    thoughtContent: Optional[str] = None
    timestamp: str
    toolCalls: Optional[List[ToolCall]] = None
    permissionRequest: Optional[PermissionRequest] = None
    permissionDecision: Optional[dict] = None
    isStreaming: Optional[bool] = None


class ChatSession(BaseModel):
    id: str
    title: str
    engine: str
    model: str
    agentSessionId: Optional[str] = None
    messages: List[ChatMessage] = []
    createdAt: str
    updatedAt: str


class ModelInfo(BaseModel):
    id: str
    name: str


class EngineAvailability(BaseModel):
    available: bool
    name: str
    version: Optional[str] = None
    models: List[ModelInfo] = []
    defaultModel: Optional[str] = None


# Request/Response models

class SendMessageRequest(BaseModel):
    message: str
    model: str
    sessionId: str
    agentSessionId: Optional[str] = None


class SendMessageResponse(BaseModel):
    chatId: str


class CreateSessionRequest(BaseModel):
    engine: Optional[str] = None
    model: Optional[str] = None


class DeleteSessionRequest(BaseModel):
    id: str


class ResolvePermissionRequest(BaseModel):
    requestId: str
    optionId: str


class StreamState:
    """内存中的流状态（非 Pydantic 模型）"""
    def __init__(self, chat_id: str, frontend_session_id: str, engine: str):
        self.chat_id = chat_id
        self.frontend_session_id = frontend_session_id
        self.engine = engine
        self.stream_content = ""
        self.status = "running"  # "running" | "completed" | "failed" | "killed"
```

- [ ] **Step 2: 验证模型可导入**

```bash
cd harness-engineering-py/backend
python -c "from app.models.schemas import ChatMessage, ChatSession, SendMessageRequest; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add Pydantic schemas for all data models"
```

---

### Task 3: Session Store 服务

**Files:**
- Create: `harness-engineering-py/backend/app/services/__init__.py`
- Create: `harness-engineering-py/backend/app/services/session_store.py`

- [ ] **Step 1: 创建 app/services/__init__.py** (空文件)

- [ ] **Step 2: 创建 session_store.py**

```python
import json
import os
import aiofiles
from pathlib import Path
from typing import Optional, List
from app.models.schemas import ChatSession, ChatMessage


SESSIONS_DIR = Path(os.getcwd()) / "data" / "chat-sessions"


async def _ensure_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


async def list_sessions() -> List[ChatSession]:
    await _ensure_dir()
    sessions: List[ChatSession] = []
    if not SESSIONS_DIR.exists():
        return sessions
    for f in SESSIONS_DIR.iterdir():
        if not f.suffix == ".json":
            continue
        try:
            async with aiofiles.open(f, "r", encoding="utf-8") as fp:
                content = await fp.read()
                sessions.append(ChatSession(**json.loads(content)))
        except Exception:
            pass
    sessions.sort(key=lambda s: s.updatedAt, reverse=True)
    return sessions


async def get_session(session_id: str) -> Optional[ChatSession]:
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as fp:
            content = await fp.read()
            return ChatSession(**json.loads(content))
    except Exception:
        return None


async def save_session(session: ChatSession) -> None:
    await _ensure_dir()
    from datetime import datetime, timezone
    session.updatedAt = datetime.now(timezone.utc).isoformat()
    async with aiofiles.open(_session_path(session.id), "w", encoding="utf-8") as fp:
        await fp.write(json.dumps(session.model_dump(), ensure_ascii=False, indent=2))


async def delete_session(session_id: str) -> None:
    path = _session_path(session_id)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


async def append_message(session_id: str, message: ChatMessage) -> None:
    session = await get_session(session_id)
    if session is None:
        return
    session.messages.append(message)
    if not session.title and message.role == "user" and message.content:
        content = message.content[:50]
        session.title = content + ("..." if len(message.content) > 50 else "")
    await save_session(session)


async def update_message(session_id: str, message_id: str, updates: dict) -> None:
    session = await get_session(session_id)
    if session is None:
        return
    for i, m in enumerate(session.messages):
        if m.id == message_id:
            updated = m.model_dump()
            updated.update(updates)
            session.messages[i] = ChatMessage(**updated)
            await save_session(session)
            return


async def update_session_agent_id(session_id: str, agent_session_id: str) -> None:
    session = await get_session(session_id)
    if session is None:
        return
    session.agentSessionId = agent_session_id
    await save_session(session)
```

- [ ] **Step 3: 验证导入**

```bash
cd harness-engineering-py/backend
python -c "from app.services.session_store import list_sessions, get_session, save_session; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/
git commit -m "feat: add session store service (file-based JSON)"
```

---

### Task 4: Stream State + Permission Queue 服务

**Files:**
- Create: `harness-engineering-py/backend/app/services/stream_state.py`
- Create: `harness-engineering-py/backend/app/services/permission_queue.py`

- [ ] **Step 1: 创建 stream_state.py**

```python
from typing import Dict, Optional
from app.models.schemas import StreamState


_streams: Dict[str, StreamState] = {}


def register_stream(chat_id: str, frontend_session_id: str, engine: str) -> None:
    _streams[chat_id] = StreamState(
        chat_id=chat_id,
        frontend_session_id=frontend_session_id,
        engine=engine,
    )


def append_stream_content(chat_id: str, content: str) -> None:
    state = _streams.get(chat_id)
    if state:
        state.stream_content += content


def set_stream_status(chat_id: str, status: str) -> None:
    state = _streams.get(chat_id)
    if state:
        state.status = status


def get_stream(chat_id: str) -> Optional[StreamState]:
    return _streams.get(chat_id)


def get_stream_by_session_id(frontend_session_id: str) -> Optional[StreamState]:
    for state in _streams.values():
        if state.frontend_session_id == frontend_session_id:
            return state
    return None


def remove_stream(chat_id: str) -> None:
    _streams.pop(chat_id, None)
```

- [ ] **Step 2: 创建 permission_queue.py**

```python
from typing import Any, Dict


_pending_permissions: Dict[str, Any] = {}


def register_pending_permission(request_id: str, engine: Any) -> None:
    _pending_permissions[request_id] = engine


def resolve_permission(request_id: str, option_id: str) -> bool:
    engine = _pending_permissions.pop(request_id, None)
    if engine is None:
        return False
    if hasattr(engine, "resolve_permission"):
        engine.resolve_permission(option_id)
    return True
```

- [ ] **Step 3: 验证导入**

```bash
cd harness-engineering-py/backend
python -c "from app.services.stream_state import register_stream, get_stream; from app.services.permission_queue import register_pending_permission, resolve_permission; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/stream_state.py backend/app/services/permission_queue.py
git commit -m "feat: add stream state and permission queue services"
```

---

### Task 5: Engine 接口 + ACP Engine

**Files:**
- Create: `harness-engineering-py/backend/app/services/engine_interface.py`
- Create: `harness-engineering-py/backend/app/services/acp_engine.py`

- [ ] **Step 1: 创建 engine_interface.py**

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from dataclasses import dataclass


@dataclass
class EngineStreamEvent:
    type: str  # "text" | "thought" | "tool" | "permission_request" | "error"
    content: str
    metadata: Any = None


class Engine(ABC):
    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    async def execute(self, options: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    def resolve_permission(self, option_id: str) -> None: ...

    @abstractmethod
    def on(self, event: str, listener: Callable[..., Any]) -> None: ...

    @abstractmethod
    def off(self, event: str, listener: Callable[..., Any]) -> None: ...
```

- [ ] **Step 2: 创建 acp_engine.py**

```python
import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional


class ACPEngine:
    """通过子进程 stdio 与 opencode acp 通信的 ACP 协议引擎。

    不依赖 @agentclientprotocol/sdk，使用手动 ndjson JSON-RPC 通信。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.session_id: Optional[str] = None
        self.initialized = False
        self.available_models: List[Dict[str, str]] = []
        self._permission_resolver: Optional[Callable] = None
        self._listeners: Dict[str, List[Callable]] = {}
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._stopping = False
        self._model: Optional[str] = None

    def on(self, event: str, listener: Callable) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable) -> None:
        if event in self._listeners:
            self._listeners[event] = [l for l in self._listeners[event] if l is not listener]

    def _emit(self, event: str, *args: Any) -> None:
        for listener in self._listeners.get(event, []):
            try:
                listener(*args)
            except Exception:
                pass

    async def start(self) -> None:
        args = self._build_args()
        print(f"[acp-engine] spawning: opencode {' '.join(args)}")

        self.process = subprocess.Popen(
            ["opencode"] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.config.get("workingDirectory", os.getcwd()),
            shell=(platform.system() == "Windows"),
            env={**os.environ, "PATH": os.environ.get("PATH", "")},
        )

        if self.process.stdout is None or self.process.stdin is None:
            raise RuntimeError("Failed to create process streams")

        self._read_task = asyncio.create_task(self._read_loop())
        asyncio.create_task(self._read_stderr())

        await self._initialize()

    async def _initialize(self) -> None:
        result = await self._send_request("initialize", {
            "protocolVersion": 1,
            "clientInfo": {"name": "harness-engineering", "version": "1.0.0"},
            "clientCapabilities": {
                "fs": {"readTextFile": True, "writeTextFile": True},
                "terminal": True,
            },
        })
        self.initialized = True

    async def create_session(self) -> str:
        if not self.initialized:
            raise RuntimeError("Not initialized")
        result = await self._send_request("newSession", {
            "cwd": self.config.get("workingDirectory", os.getcwd()),
            "mcpServers": [],
        })
        self.session_id = result.get("sessionId", "")
        models_raw = result.get("models", {}).get("availableModels", [])
        self.available_models = [{"modelId": m.get("modelId", m.get("id", "")), "name": m.get("name", m.get("modelId", ""))} for m in models_raw]
        return self.session_id

    async def resume_session(self, session_id: str) -> str:
        if not self.initialized:
            raise RuntimeError("Not initialized")
        result = await self._send_request("loadSession", {
            "sessionId": session_id,
            "cwd": self.config.get("workingDirectory", os.getcwd()),
            "mcpServers": [],
        })
        self.session_id = session_id
        return self.session_id

    async def send_prompt(self, prompt: str) -> str:
        if not self.session_id:
            raise RuntimeError("No active session")
        result = await self._send_request("prompt", {
            "sessionId": self.session_id,
            "prompt": [{"type": "text", "text": prompt}],
        })
        return result.get("stopReason", "end_turn")

    async def set_model(self, model_id: str) -> None:
        if not self.session_id:
            raise RuntimeError("No active session")
        self._model = model_id
        await self._send_request("unstable_setSessionModel", {
            "sessionId": self.session_id,
            "modelId": model_id,
        })

    def get_available_models(self) -> List[Dict[str, str]]:
        return self.available_models

    def resolve_permission(self, option_id: str) -> None:
        if self._permission_resolver:
            resolver = self._permission_resolver
            self._permission_resolver = None
            resolver({"outcome": {"outcome": "selected", "optionId": option_id}})

    def cancel_session(self) -> None:
        if self.session_id:
            asyncio.create_task(self._send_request("cancel", {"sessionId": self.session_id}))

    def stop(self) -> None:
        self._stopping = True
        if self.process:
            self.process.kill()
            self.process = None
        self.session_id = None
        self.initialized = False

    def _build_args(self) -> List[str]:
        engine_type = self.config.get("engineType", "opencode")
        cwd = self.config.get("workingDirectory", os.getcwd())
        if engine_type == "opencode":
            return ["acp", "--cwd", cwd]
        raise ValueError(f"Unknown engine type: {engine_type}")

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._request_id += 1
        req_id = self._request_id
        request = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[req_id] = future

        if self.process and self.process.stdin:
            self.process.stdin.write((request + "\n").encode())
            self.process.stdin.flush()

        try:
            return await asyncio.wait_for(future, timeout=300)
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise RuntimeError(f"Request {method} timed out")

    async def _read_loop(self) -> None:
        if not self.process or not self.process.stdout:
            return
        loop = asyncio.get_event_loop()
        buffer = b""
        while not self._stopping and self.process and self.process.stdout:
            try:
                chunk = await loop.run_in_executor(None, self.process.stdout.read, 4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_line(line.decode("utf-8", errors="replace"))
            except Exception:
                break

    def _handle_line(self, line: str) -> None:
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            return

        # Response to a pending request
        if "id" in msg and msg["id"] in self._pending_requests:
            future = self._pending_requests.pop(msg["id"])
            if "error" in msg:
                future.set_exception(RuntimeError(msg["error"].get("message", "Unknown error")))
            else:
                future.set_result(msg.get("result", {}))
            return

        # Notification / session update
        if "method" in msg:
            method = msg["method"]
            params = msg.get("params", {})

            if method == "sessionUpdate":
                self._handle_session_update(params.get("update", params))
            elif method == "requestPermission":
                self._handle_permission(params)
            elif method == "sessionNotification":
                self._handle_session_update(params.get("update", params))

    def _handle_session_update(self, update: Dict[str, Any]) -> None:
        update_type = update.get("sessionUpdate", "")
        if update_type == "agent_message_chunk":
            content = update.get("content", {})
            self._emit("agent-message", content)
        elif update_type == "agent_thought_chunk":
            content = update.get("content", {})
            self._emit("agent-thought", content)
        elif update_type == "tool_call":
            self._emit("tool-call", {
                "id": update.get("toolCallId", ""),
                "title": update.get("title", ""),
                "status": update.get("status", ""),
                "rawInput": update.get("rawInput", ""),
            })
        elif update_type == "tool_call_update":
            self._emit("tool-call-update", {
                "id": update.get("toolCallId", ""),
                "title": update.get("title", ""),
                "status": update.get("status", ""),
                "rawInput": update.get("rawInput", ""),
                "rawOutput": update.get("rawOutput", ""),
            })

    def _handle_permission(self, params: Dict[str, Any]) -> None:
        self._emit("permission", params)
        # Create a resolver future that will be resolved by resolve_permission()
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def resolver(response: Dict[str, Any]) -> None:
            if not future.done():
                future.set_result(response)

        self._permission_resolver = resolver

        async def send_response():
            try:
                result = await future
                await self._send_request("respondPermission", {
                    "sessionId": self.session_id,
                    "requestId": params.get("id", ""),
                    "response": result,
                })
            except Exception:
                pass

        asyncio.create_task(send_response())

    async def _read_stderr(self) -> None:
        if not self.process or not self.process.stderr:
            return
        loop = asyncio.get_event_loop()
        while not self._stopping and self.process and self.process.stderr:
            try:
                chunk = await loop.run_in_executor(None, self.process.stderr.read, 4096)
                if not chunk:
                    break
                print(f"[acp-engine stderr] {chunk.decode('utf-8', errors='replace').strip()}")
            except Exception:
                break
```

- [ ] **Step 3: 验证导入**

```bash
cd harness-engineering-py/backend
python -c "from app.services.engine_interface import Engine, EngineStreamEvent; from app.services.acp_engine import ACPEngine; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/engine_interface.py backend/app/services/acp_engine.py
git commit -m "feat: add engine interface and ACP engine implementation"
```

---

### Task 6: OpenCode Wrapper + Engine Factory

**Files:**
- Create: `harness-engineering-py/backend/app/services/opencode_wrapper.py`
- Create: `harness-engineering-py/backend/app/services/engine_factory.py`

- [ ] **Step 1: 创建 opencode_wrapper.py**

```python
import asyncio
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from app.services.engine_interface import Engine, EngineStreamEvent
from app.services.acp_engine import ACPEngine


class OpenCodeEngineWrapper(Engine):
    def __init__(self):
        self._engine: Optional[ACPEngine] = None
        self._current_session_id: Optional[str] = None
        self._streaming = False
        self._collected_output = ""
        self._seen_tool_ids: Set[str] = set()
        self._listeners: Dict[str, List[Callable]] = {}

    def get_name(self) -> str:
        return "opencode"

    async def is_available(self) -> bool:
        try:
            cmd = "where" if platform.system() == "Windows" else "command"
            shell = platform.system() == "Windows"
            subprocess.run(
                [cmd, "opencode"] if platform.system() == "Windows" else [cmd, "-v", "opencode"],
                capture_output=True, check=True, shell=shell
            )
            return True
        except Exception:
            return False

    async def execute(self, options: Dict[str, Any]) -> Dict[str, Any]:
        self._seen_tool_ids.clear()
        self._collected_output = ""

        prompt = options.get("prompt", "")
        model = options.get("model", "")
        session_id = options.get("sessionId")
        working_directory = options.get("workingDirectory", os.getcwd())
        agent = options.get("agent")

        can_reuse = session_id and self._engine and self._current_session_id == session_id

        if not can_reuse:
            if self._engine:
                try:
                    self._engine.stop()
                except Exception:
                    pass
            config = {
                "engineType": "opencode",
                "command": "opencode",
                "workingDirectory": working_directory,
                "agentName": agent,
                "model": model,
            }
            self._engine = ACPEngine(config)
            self._setup_engine_events()
            await self._engine.start()
            self._current_session_id = (
                await self._engine.resume_session(session_id)
                if session_id
                else await self._engine.create_session()
            )

        engine = self._engine
        if not engine:
            return {"success": False, "output": "", "error": "Engine not initialized"}

        if model:
            try:
                await engine.set_model(model)
            except Exception as err:
                self._emit("stream", EngineStreamEvent(
                    type="error",
                    content=f"Model unavailable: {err}",
                ))
                return {"success": False, "output": "", "error": str(err)}

        self._streaming = True
        try:
            stop_reason = await engine.send_prompt(prompt)
            self._streaming = False
            return {
                "success": not stop_reason or stop_reason == "end_turn",
                "output": self._collected_output.strip(),
                "sessionId": self._current_session_id,
                "stopReason": stop_reason,
            }
        except Exception as error:
            self._streaming = False
            return {
                "success": False,
                "output": self._collected_output.strip(),
                "error": str(error),
            }

    def cancel(self) -> None:
        if self._engine:
            self._engine.cancel_session()
            self._engine.stop()
            self._engine = None

    def resolve_permission(self, option_id: str) -> None:
        if self._engine:
            self._engine.resolve_permission(option_id)

    def on(self, event: str, listener: Callable[..., Any]) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable[..., Any]) -> None:
        if event in self._listeners:
            self._listeners[event] = [l for l in self._listeners[event] if l is not listener]

    def _emit(self, event: str, *args: Any) -> None:
        for listener in self._listeners.get(event, []):
            try:
                listener(*args)
            except Exception:
                pass

    def _setup_engine_events(self) -> None:
        if not self._engine:
            return

        def on_agent_message(content: Any) -> None:
            if not self._streaming:
                return
            text = content if isinstance(content, str) else content.get("text", "") or content.get("content", "")
            if text:
                self._collected_output += text
                self._emit("stream", EngineStreamEvent(type="text", content=text))

        def on_agent_thought(content: Any) -> None:
            if not self._streaming:
                return
            text = content if isinstance(content, str) else content.get("text", "") or content.get("content", "")
            if text:
                self._emit("stream", EngineStreamEvent(type="thought", content=text))

        def on_tool_call(tc: Dict[str, Any]) -> None:
            if not self._streaming:
                return
            tool_id = tc.get("id", "")
            if tool_id and tool_id not in self._seen_tool_ids:
                self._seen_tool_ids.add(tool_id)
                formatted = f"\n\n**🔧 {tc.get('title', 'Tool')}**\n"
                self._collected_output += formatted
                self._emit("stream", EngineStreamEvent(type="text", content=formatted, metadata=tc))

        def on_tool_call_update(tu: Dict[str, Any]) -> None:
            if not self._streaming:
                return
            if tu.get("status") in ("completed", "failed"):
                output = tu.get("rawOutput", "")
                if isinstance(output, dict):
                    output = output.get("output", "")
                if output:
                    formatted = f"\n```\n{output}\n```\n"
                    self._collected_output += formatted
                    self._emit("stream", EngineStreamEvent(type="text", content=formatted, metadata=tu))

        def on_permission(params: Dict[str, Any]) -> None:
            raw_options = params.get("options", [])
            options = []
            for o in raw_options:
                opt_id = o.get("optionId", o.get("id", ""))
                options.append({
                    "id": opt_id,
                    "label": o.get("label", opt_id),
                    "style": self._infer_option_style(opt_id),
                })
            request = {
                "id": params.get("id", f"perm-{int(datetime.now(timezone.utc).timestamp() * 1000)}"),
                "type": params.get("type", "unknown"),
                "description": params.get("description", params.get("title", "")),
                "detail": params.get("detail", params.get("message", json.dumps(params, ensure_ascii=False))),
                "options": options,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._emit("stream", EngineStreamEvent(
                type="permission_request",
                content=json.dumps(request, ensure_ascii=False),
                metadata=request,
            ))

        def on_error(error: Any) -> None:
            msg = str(error) if not isinstance(error, str) else error
            self._emit("stream", EngineStreamEvent(type="error", content=msg))

        self._engine.on("agent-message", on_agent_message)
        self._engine.on("agent-thought", on_agent_thought)
        self._engine.on("tool-call", on_tool_call)
        self._engine.on("tool-call-update", on_tool_call_update)
        self._engine.on("permission", on_permission)
        self._engine.on("error", on_error)

    @staticmethod
    def _infer_option_style(opt_id: str) -> str:
        lower = opt_id.lower()
        if any(kw in lower for kw in ("deny", "reject", "block")):
            return "danger"
        if any(kw in lower for kw in ("allow", "accept", "always")):
            return "primary"
        return "default"
```

- [ ] **Step 2: 创建 engine_factory.py**

```python
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.engine_interface import Engine
from app.services.opencode_wrapper import OpenCodeEngineWrapper
from app.models.schemas import EngineAvailability, ModelInfo


_engine_pool: Dict[str, Dict[str, Any]] = {}
ENGINE_POOL_TTL = 10 * 60  # 10 minutes in seconds

_cleanup_task_started = False


def _start_cleanup() -> None:
    global _cleanup_task_started
    if _cleanup_task_started:
        return
    _cleanup_task_started = True

    async def _cleanup_loop():
        while True:
            await asyncio.sleep(60)
            now = time.time()
            expired = [
                k for k, v in _engine_pool.items()
                if now - v["lastUsed"] > ENGINE_POOL_TTL
            ]
            for k in expired:
                entry = _engine_pool.pop(k, None)
                if entry:
                    try:
                        entry["engine"].cancel()
                    except Exception:
                        pass

    asyncio.ensure_future(_cleanup_loop())


async def get_or_create_engine(session_key: Optional[str] = None) -> Optional[Engine]:
    _start_cleanup()
    if session_key:
        cached = _engine_pool.get(session_key)
        if cached:
            cached["lastUsed"] = time.time()
            return cached["engine"]
    engine = await create_engine()
    if engine and session_key:
        _engine_pool[session_key] = {"engine": engine, "lastUsed": time.time()}
    return engine


async def create_engine() -> Optional[Engine]:
    engine = OpenCodeEngineWrapper()
    if not await engine.is_available():
        return None
    return engine


async def detect_engines() -> List[EngineAvailability]:
    engine = OpenCodeEngineWrapper()
    available = await engine.is_available()
    models = await _read_opencode_models()
    return [
        EngineAvailability(
            available=available,
            name="OpenCode",
            models=models,
            defaultModel=models[0].id if models else None,
        )
    ]


async def _read_opencode_models() -> List[ModelInfo]:
    config_path = Path.home() / ".config" / "opencode" / "opencode.json"
    if not config_path.exists():
        return [ModelInfo(id="default", name="Default")]

    try:
        content = config_path.read_text(encoding="utf-8")
        config = json.loads(content)
        models: List[ModelInfo] = []
        default_model = config.get("model", "")

        provider = config.get("provider", {})
        if isinstance(provider, dict):
            for provider_key, provider_val in provider.items():
                if not isinstance(provider_val, dict):
                    continue
                provider_models = provider_val.get("models", {})
                if not isinstance(provider_models, dict):
                    continue
                for model_key, model_val in provider_models.items():
                    if not isinstance(model_val, dict):
                        continue
                    full_id = f"{provider_key}/{model_key}"
                    is_default = default_model == full_id
                    models.append(ModelInfo(
                        id=full_id,
                        name=(model_val.get("name", model_key) + (" (默认)" if is_default else "")),
                    ))

        if not models:
            return [ModelInfo(id="default", name="Default")]

        # Sort: default model first, then alphabetically
        models.sort(key=lambda m: ("" if m.id == default_model else m.name))
        return models
    except Exception:
        return [ModelInfo(id="default", name="Default")]


async def is_engine_available() -> bool:
    engine = await create_engine()
    return engine is not None
```

- [ ] **Step 3: 验证导入**

```bash
cd harness-engineering-py/backend
python -c "from app.services.opencode_wrapper import OpenCodeEngineWrapper; from app.services.engine_factory import get_or_create_engine, detect_engines; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/opencode_wrapper.py backend/app/services/engine_factory.py
git commit -m "feat: add OpenCode engine wrapper and engine factory with pool"
```

---

### Task 7: API Routers

**Files:**
- Create: `harness-engineering-py/backend/app/routers/__init__.py`
- Create: `harness-engineering-py/backend/app/routers/sessions.py`
- Create: `harness-engineering-py/backend/app/routers/chat.py`
- Create: `harness-engineering-py/backend/app/routers/engines.py`

- [ ] **Step 1: 创建 app/routers/__init__.py** (空文件)

- [ ] **Step 2: 创建 routers/sessions.py**

```python
import random
import string
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ChatSession, ChatMessage, CreateSessionRequest, DeleteSessionRequest,
)
from app.services.session_store import list_sessions, save_session, delete_session

router = APIRouter()


def _gen_id(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{int(time.time() * 1000)}-{suffix}"


@router.get("/chat/sessions")
async def get_sessions():
    sessions = await list_sessions()
    return {"sessions": [s.model_dump() for s in sessions]}


@router.post("/chat/sessions")
async def create_session(body: CreateSessionRequest):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    session = ChatSession(
        id=_gen_id("session"),
        title="",
        engine=body.engine or "opencode",
        model=body.model or "claude-sonnet-4-6",
        messages=[],
        createdAt=now,
        updatedAt=now,
    )
    await save_session(session)
    return {"session": session.model_dump()}


@router.delete("/chat/sessions")
async def delete_session_route(body: DeleteSessionRequest):
    if not body.id:
        raise HTTPException(status_code=400, detail="Missing id")
    await delete_session(body.id)
    return {"deleted": True}
```

- [ ] **Step 3: 创建 routers/chat.py**

```python
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    SendMessageRequest, SendMessageResponse, ResolvePermissionRequest,
    ChatMessage, PermissionRequest,
)
from app.services.engine_factory import get_or_create_engine
from app.services.engine_interface import EngineStreamEvent
from app.services.stream_state import (
    register_stream, append_stream_content, set_stream_status,
    get_stream, remove_stream,
)
from app.services.session_store import append_message, update_session_agent_id
from app.services.permission_queue import register_pending_permission, resolve_permission

router = APIRouter()

# In-memory active chats
_active_chats: dict = {}
# Event bus: chat_id -> list of (event, data) queues
_stream_queues: dict = {}
_stream_buffers: dict = {}


async def _stream_event(chat_id: str, event_type: str, data: dict) -> None:
    """Send an event to all listeners for a chat_id."""
    if chat_id in _stream_queues:
        for q in _stream_queues[chat_id]:
            await q.put((event_type, data))


@router.post("/chat/stream")
async def start_chat(body: SendMessageRequest):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    chat_id = f"chat-{int(time.time() * 1000)}"
    engine = await get_or_create_engine(body.sessionId)

    if engine is None:
        raise HTTPException(status_code=500, detail="引擎不可用，请检查是否已安装 OpenCode")

    register_stream(chat_id, body.sessionId or "", "opencode")

    if body.sessionId:
        await append_message(body.sessionId, ChatMessage(
            id=f"msg-{int(time.time() * 1000)}",
            role="user",
            content=body.message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    def on_engine_stream(evt: EngineStreamEvent) -> None:
        if evt.type == "text" and evt.content:
            append_stream_content(chat_id, evt.content)
            asyncio.ensure_future(_stream_event(chat_id, "delta", {"content": evt.content}))
        elif evt.type == "thought" and evt.content:
            asyncio.ensure_future(_stream_event(chat_id, "thinking", {"content": evt.content}))
        elif evt.type == "permission_request" and evt.metadata:
            request = evt.metadata
            register_pending_permission(request["id"], engine)
            asyncio.ensure_future(_stream_event(chat_id, "permission_request", {"request": request}))
        elif evt.type == "error" and evt.content:
            asyncio.ensure_future(_stream_event(chat_id, "engine_error", {"message": evt.content}))

    engine.on("stream", on_engine_stream)

    async def execute_and_notify():
        try:
            result = await engine.execute({
                "prompt": body.message,
                "model": body.model or "",
                "workingDirectory": os.getcwd(),
                "sessionId": body.agentSessionId or None,
            })
            if body.sessionId:
                await append_message(body.sessionId, ChatMessage(
                    id=f"msg-assistant-{chat_id}",
                    role="assistant",
                    content=result.get("output", "") or "",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
                if result.get("sessionId"):
                    await update_session_agent_id(body.sessionId, result["sessionId"])
            return {
                "result": result.get("output", ""),
                "session_id": result.get("sessionId"),
                "is_error": not result.get("success", False),
                "error": result.get("error"),
            }
        finally:
            engine.off("stream", on_engine_stream)

    task = asyncio.ensure_future(execute_and_notify())
    _active_chats[chat_id] = task

    # Cleanup after 30 seconds of completion
    async def delayed_cleanup():
        try:
            await task
        except Exception:
            pass
        await asyncio.sleep(30)
        _active_chats.pop(chat_id, None)
        remove_stream(chat_id)

    asyncio.ensure_future(delayed_cleanup())

    return {"chatId": chat_id}


@router.get("/chat/stream")
async def stream_chat(id: str = Query(...), request: Request = None):
    task = _active_chats.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    queue: asyncio.Queue = asyncio.Queue()

    if id not in _stream_queues:
        _stream_queues[id] = []
    _stream_queues[id].append(queue)

    # Replay buffered content
    state = get_stream(id)
    buffered_content = state.stream_content if state else ""

    async def generate():
        try:
            # Send connected event
            yield f"event: connected\ndata: {json.dumps({'chatId': id})}\n\n"

            # Replay buffered content if any
            if buffered_content:
                yield f"event: delta\ndata: {json.dumps({'content': buffered_content})}\n\n"

            # Stream live events
            while True:
                try:
                    event_type, data = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # Check if task is done
                    if task.done():
                        try:
                            result = task.result()
                            if result:
                                yield f"event: done\ndata: {json.dumps({'result': result.get('result', ''), 'sessionId': result.get('session_id', ''), 'isError': result.get('is_error', False)}, ensure_ascii=False)}\n\n"
                            else:
                                yield f"event: done\ndata: {json.dumps({'result': '', 'sessionId': '', 'isError': False})}\n\n"
                        except Exception as err:
                            yield f"event: failed\ndata: {json.dumps({'message': str(err)})}\n\n"
                        break

            # Wait for final events
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            if id in _stream_queues:
                _stream_queues[id] = [q for q in _stream_queues[id] if q is not queue]
                if not _stream_queues[id]:
                    del _stream_queues[id]

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/chat/stream")
async def cancel_chat(id: str = Query(...)):
    task = _active_chats.get(id)
    if task and not task.done():
        task.cancel()
    _active_chats.pop(id, None)
    remove_stream(id)
    return {"cancelled": True}


@router.post("/chat/permission")
async def resolve_permission_route(body: ResolvePermissionRequest):
    if not body.requestId or not body.optionId:
        raise HTTPException(status_code=400, detail="Missing requestId or optionId")
    resolved = resolve_permission(body.requestId, body.optionId)
    if not resolved:
        raise HTTPException(status_code=404, detail="Permission request not found")
    return {"resolved": True}
```

- [ ] **Step 4: 创建 routers/engines.py**

```python
from fastapi import APIRouter
from app.services.engine_factory import detect_engines

router = APIRouter()


@router.get("/engines/availability")
async def get_engine_availability():
    engines = await detect_engines()
    return {"engines": [e.model_dump() for e in engines]}
```

- [ ] **Step 5: 验证所有路由可导入**

```bash
cd harness-engineering-py/backend
python -c "from app.routers import sessions, chat, engines; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: 验证 FastAPI 启动成功**

```bash
cd harness-engineering-py/backend
uvicorn app.main:app --port 8000 &
sleep 2
curl http://localhost:8000/api/health
curl http://localhost:8000/api/chat/sessions
curl http://localhost:8000/api/engines/availability
```

Expected: health returns ok, sessions returns `{"sessions":[]}`, availability returns engine info.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/
git commit -m "feat: add API routers (sessions, chat/stream SSE, engines)"
```

---

## Part 2: Frontend (Vue 3 + Vite)

### Task 8: Frontend 项目脚手架

**Files:**
- Create: `harness-engineering-py/frontend/package.json`
- Create: `harness-engineering-py/frontend/vite.config.ts`
- Create: `harness-engineering-py/frontend/tsconfig.json`
- Create: `harness-engineering-py/frontend/tsconfig.node.json`
- Create: `harness-engineering-py/frontend/index.html`
- Create: `harness-engineering-py/frontend/src/vite-env.d.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "harness-engineering-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "element-plus": "^2.8.0",
    "@element-plus/icons-vue": "^2.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "typescript": "~5.6.0",
    "vite": "^6.0.0",
    "vue-tsc": "^2.1.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Harness Engineering</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: 创建 src/vite-env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 7: 安装依赖并验证启动**

```bash
cd harness-engineering-py/frontend
npm install
```

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Vue 3 + Vite + Element Plus frontend project"
```

---

### Task 9: 类型定义 + Mock 数据

**Files:**
- Create: `harness-engineering-py/frontend/src/types/index.ts`
- Create: `harness-engineering-py/frontend/src/types/chat.ts`
- Create: `harness-engineering-py/frontend/src/mock/data.ts`

- [ ] **Step 1: 创建 src/types/index.ts**

```typescript
export interface MarketItem {
  id: string
  name: string
  description: string
  tags: string[]
  icon: string
  usageCount: number
  lastUsedAt: string
}

export type Skill = MarketItem
export type Agent = MarketItem
```

- [ ] **Step 2: 创建 src/types/chat.ts**

```typescript
export interface PermissionOption {
  id: string
  label: string
  style: "primary" | "danger" | "default"
}

export interface PermissionRequest {
  id: string
  type: string
  description: string
  detail: string
  options: PermissionOption[]
  timestamp: string
}

export interface ToolCall {
  name: string
  input: string
  output?: string
}

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

export interface ChatSession {
  id: string
  title: string
  engine: string
  model: string
  agentSessionId?: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
}

export interface EngineAvailability {
  available: boolean
  name: string
  version?: string
  models: ModelInfo[]
  defaultModel?: string
}

export interface ModelInfo {
  id: string
  name: string
}
```

- [ ] **Step 3: 创建 src/mock/data.ts**

```typescript
import type { Skill, Agent } from "@/types"

export const skills: Skill[] = [
  { id: "s1", name: "代码生成", description: "根据需求描述自动生成代码片段和函数实现", tags: ["代码生成"], icon: "Code", usageCount: 2340, lastUsedAt: "2026-05-27T10:30:00Z" },
  { id: "s2", name: "单元测试", description: "自动为指定函数生成单元测试用例", tags: ["测试"], icon: "TestTube", usageCount: 1890, lastUsedAt: "2026-05-27T09:15:00Z" },
  { id: "s3", name: "代码审查", description: "AI 驱动的代码审查，发现潜在问题和优化建议", tags: ["代码生成"], icon: "Search", usageCount: 1560, lastUsedAt: "2026-05-26T16:45:00Z" },
  { id: "s4", name: "文档生成", description: "自动生成 API 文档和代码注释", tags: ["文档"], icon: "FileText", usageCount: 1200, lastUsedAt: "2026-05-26T14:20:00Z" },
  { id: "s5", name: "自动部署", description: "一键部署应用到指定环境", tags: ["部署"], icon: "Rocket", usageCount: 980, lastUsedAt: "2026-05-25T11:00:00Z" },
  { id: "s6", name: "数据迁移", description: "数据库 schema 迁移和数据转换工具", tags: ["数据", "部署"], icon: "Database", usageCount: 760, lastUsedAt: "2026-05-24T15:30:00Z" },
  { id: "s7", name: "性能分析", description: "分析代码性能瓶颈并提供优化建议", tags: ["代码生成"], icon: "Gauge", usageCount: 650, lastUsedAt: "2026-05-23T10:00:00Z" },
  { id: "s8", name: "接口测试", description: "自动生成 API 接口测试脚本", tags: ["测试"], icon: "Webhook", usageCount: 580, lastUsedAt: "2026-05-22T09:30:00Z" },
  { id: "s9", name: "安全扫描", description: "扫描代码中的安全漏洞和敏感信息泄露", tags: ["安全"], icon: "Shield", usageCount: 520, lastUsedAt: "2026-05-21T14:00:00Z" },
  { id: "s10", name: "日志分析", description: "智能分析应用日志，定位异常和错误", tags: ["数据"], icon: "ScrollText", usageCount: 450, lastUsedAt: "2026-05-20T16:30:00Z" },
  { id: "s11", name: "依赖管理", description: "检测项目依赖更新和版本冲突", tags: ["部署"], icon: "Package", usageCount: 380, lastUsedAt: "2026-05-19T11:15:00Z" },
  { id: "s12", name: "配置生成", description: "根据项目类型生成配置文件模板", tags: ["文档"], icon: "Settings", usageCount: 310, lastUsedAt: "2026-05-18T08:45:00Z" },
]

export const agents: Agent[] = [
  { id: "a1", name: "编码助手", description: "全栈编码助手，支持代码生成、重构和调试", tags: ["编码"], icon: "Bot", usageCount: 3210, lastUsedAt: "2026-05-27T11:00:00Z" },
  { id: "a2", name: "测试助手", description: "自动化测试编排，覆盖单元、集成和 E2E 测试", tags: ["测试"], icon: "FlaskConical", usageCount: 2100, lastUsedAt: "2026-05-27T10:00:00Z" },
  { id: "a3", name: "运维助手", description: "监控、告警和自动化运维操作", tags: ["运维"], icon: "Server", usageCount: 1680, lastUsedAt: "2026-05-26T15:30:00Z" },
  { id: "a4", name: "文档助手", description: "自动生成和维护项目文档", tags: ["文档"], icon: "BookOpen", usageCount: 1200, lastUsedAt: "2026-05-25T09:00:00Z" },
  { id: "a5", name: "安全助手", description: "安全审计、合规检查和漏洞修复建议", tags: ["安全"], icon: "ShieldCheck", usageCount: 890, lastUsedAt: "2026-05-24T14:00:00Z" },
  { id: "a6", name: "数据助手", description: "数据分析、可视化和报告生成", tags: ["数据"], icon: "BarChart3", usageCount: 750, lastUsedAt: "2026-05-23T10:30:00Z" },
  { id: "a7", name: "架构助手", description: "系统架构设计和代码结构优化", tags: ["编码"], icon: "Blocks", usageCount: 620, lastUsedAt: "2026-05-22T16:00:00Z" },
  { id: "a8", name: "DevOps 助手", description: "CI/CD 流水线编排和部署管理", tags: ["运维"], icon: "GitBranch", usageCount: 540, lastUsedAt: "2026-05-21T11:30:00Z" },
]

export const skillTags: string[] = [...new Set(skills.flatMap(s => s.tags))]
export const agentTags: string[] = [...new Set(agents.flatMap(a => a.tags))]
```

- [ ] **Step 4: 验证编译**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit
```

Expected: No errors (may have some due to missing App.vue — that's expected).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/ frontend/src/mock/
git commit -m "feat: add TypeScript types and mock data for skills/agents"
```

---

### Task 10: App 入口 + Router + Pinia Stores

**Files:**
- Create: `harness-engineering-py/frontend/src/main.ts`
- Create: `harness-engineering-py/frontend/src/App.vue`
- Create: `harness-engineering-py/frontend/src/router/index.ts`
- Create: `harness-engineering-py/frontend/src/stores/chat.ts`
- Create: `harness-engineering-py/frontend/src/stores/engine.ts`

- [ ] **Step 1: 创建 src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
```

- [ ] **Step 2: 创建 src/App.vue**

```vue
<template>
  <div id="app-root">
    <Navbar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navbar from '@/components/layout/Navbar.vue'
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}
#app-root {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--el-bg-color-page);
}
</style>
```

- [ ] **Step 3: 创建 src/router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/skills',
    },
    {
      path: '/skills',
      name: 'Skills',
      component: () => import('@/views/SkillsView.vue'),
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('@/views/AgentsView.vue'),
    },
    {
      path: '/workflow',
      name: 'Workflow',
      component: () => import('@/views/WorkflowView.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 4: 创建 src/stores/chat.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage, PermissionRequest } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const pendingPermission = ref<PermissionRequest | null>(null)
  const model = ref('claude-sonnet-4-6')
  const agentSessionId = ref<string | undefined>(undefined)

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  function selectSession(id: string) {
    currentSessionId.value = id
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      messages.value = session.messages
      agentSessionId.value = session.agentSessionId
      model.value = session.model
    }
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
    agentSessionId.value = undefined
  }

  return {
    sessions, currentSessionId, messages, isStreaming,
    pendingPermission, model, agentSessionId,
    setSessions, selectSession, clearSession,
  }
})
```

- [ ] **Step 5: 创建 src/stores/engine.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { EngineAvailability, ModelInfo } from '@/types/chat'

export const useEngineStore = defineStore('engine', () => {
  const engineInfo = ref<EngineAvailability | null>(null)
  const loading = ref(false)

  async function fetchAvailability() {
    loading.value = true
    try {
      const res = await fetch('/api/engines/availability')
      const data = await res.json()
      engineInfo.value = (data.engines || [])[0] || null
    } catch (err) {
      console.error('[EngineStore] Failed to fetch engine availability:', err)
    } finally {
      loading.value = false
    }
  }

  return { engineInfo, loading, fetchAvailability }
})
```

- [ ] **Step 6: 创建空 views 占位文件以验证编译**

```bash
mkdir -p harness-engineering-py/frontend/src/views
mkdir -p harness-engineering-py/frontend/src/components/layout
```

Create `src/views/SkillsView.vue`:
```vue
<template><div>Skills</div></template>
```

Create `src/views/AgentsView.vue`:
```vue
<template><div>Agents</div></template>
```

Create `src/views/WorkflowView.vue`:
```vue
<template><div>Workflow</div></template>
```

Create `src/components/layout/Navbar.vue`:
```vue
<template><div>Navbar</div></template>
```

- [ ] **Step 7: 验证 dev server 启动**

```bash
cd harness-engineering-py/frontend
npm run dev &
sleep 3
curl http://localhost:3000
```

Expected: HTML page returned (200).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/main.ts frontend/src/App.vue frontend/src/router/ frontend/src/stores/ frontend/src/views/ frontend/src/components/
git commit -m "feat: add Vue app entry, router, Pinia stores, and placeholder views"
```

---

### Task 11: Navbar 组件

**Files:**
- Create/Replace: `harness-engineering-py/frontend/src/components/layout/Navbar.vue`

- [ ] **Step 1: 创建 Navbar.vue**

```vue
<template>
  <el-menu
    :default-active="activeRoute"
    mode="horizontal"
    :ellipsis="false"
    class="navbar-menu"
    @select="handleSelect"
  >
    <div class="navbar-brand">
      <span class="brand-text">Harness</span>
    </div>
    <div class="navbar-items">
      <el-menu-item index="/skills">
        <el-icon><MagicStick /></el-icon>
        <span>Skills</span>
      </el-menu-item>
      <el-menu-item index="/agents">
        <el-icon><Robot /></el-icon>
        <span>Agents</span>
      </el-menu-item>
      <el-menu-item index="/workflow">
        <el-icon><Connection /></el-icon>
        <span>工作流</span>
      </el-menu-item>
    </div>
    <div class="navbar-actions">
      <el-switch
        v-model="isDark"
        :active-action-icon="Sunny"
        :inactive-action-icon="Moon"
        inline-prompt
        @change="toggleTheme"
      />
    </div>
  </el-menu>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MagicStick, Robot, Connection, Sunny, Moon } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isDark = ref(false)

const activeRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/skills')) return '/skills'
  if (path.startsWith('/agents')) return '/agents'
  if (path.startsWith('/workflow')) return '/workflow'
  return '/skills'
})

function handleSelect(index: string) {
  router.push(index)
}

function toggleTheme(val: boolean) {
  document.documentElement.classList.toggle('dark', val)
}
</script>

<style scoped>
.navbar-menu {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  border-bottom: 1px solid var(--el-border-color-light);
}
.navbar-brand {
  margin-right: 16px;
}
.brand-text {
  font-size: 18px;
  font-weight: 600;
}
.navbar-items {
  display: flex;
  flex: 1;
  border-bottom: none !important;
}
.navbar-items .el-menu-item {
  border-bottom: none !important;
}
.navbar-actions {
  margin-left: auto;
}
</style>
```

- [ ] **Step 2: 验证编译**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/Navbar.vue
git commit -m "feat: add Navbar with el-menu navigation and dark mode toggle"
```

---

### Task 12: SkillCard + SkillFilter 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/skills/SkillCard.vue`
- Create: `harness-engineering-py/frontend/src/components/skills/SkillFilter.vue`

- [ ] **Step 1: 创建 SkillCard.vue**

```vue
<template>
  <el-card shadow="hover" class="skill-card">
    <div class="skill-header">
      <div class="skill-icon">
        <el-icon :size="20"><component :is="iconComponent" /></el-icon>
      </div>
      <div class="skill-info">
        <h3 class="skill-name">{{ skill.name }}</h3>
        <p class="skill-desc">{{ skill.description }}</p>
      </div>
    </div>
    <div class="skill-tags">
      <el-tag v-for="tag in skill.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'
import type { Skill } from '@/types'

const props = defineProps<{ skill: Skill }>()

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    Code: Icons.Document,
    TestTube: Icons.Orange,
    Search: Icons.Search,
    FileText: Icons.Document,
    Rocket: Icons.Promotion,
    Database: Icons.Coin,
    Gauge: Icons.Odometer,
    Webhook: Icons.Link,
    Shield: Icons.Lock,
    ScrollText: Icons.Tickets,
    Package: Icons.Box,
    Settings: Icons.Setting,
  }
  return iconMap[props.skill.icon] || Icons.MagicStick
})
</script>

<style scoped>
.skill-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.skill-card:hover {
  transform: translateY(-2px);
}
.skill-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.skill-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  flex-shrink: 0;
}
.skill-info {
  min-width: 0;
  flex: 1;
}
.skill-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
}
.skill-desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
</style>
```

- [ ] **Step 2: 创建 SkillFilter.vue**

```vue
<template>
  <div class="skill-filter">
    <el-input
      v-model="searchModel"
      placeholder="搜索 Skills..."
      :prefix-icon="Search"
      clearable
      @input="onSearchChange"
    />
    <div class="filter-tags">
      <el-tag
        :type="selectedTags.length === 0 ? 'primary' : 'info'"
        class="filter-tag"
        @click="onTagChange([])"
      >
        全部
      </el-tag>
      <el-tag
        v-for="tag in tags"
        :key="tag"
        :type="selectedTags.includes(tag) ? 'primary' : 'info'"
        class="filter-tag"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{
  tags: string[]
  selectedTags: string[]
  searchQuery: string
}>()

const emit = defineEmits<{
  'update:selectedTags': [tags: string[]]
  'update:searchQuery': [query: string]
}>()

const searchModel = ref(props.searchQuery)

watch(() => props.searchQuery, (val) => {
  searchModel.value = val
})

function toggleTag(tag: string) {
  const current = [...props.selectedTags]
  if (current.includes(tag)) {
    emit('update:selectedTags', current.filter(t => t !== tag))
  } else {
    emit('update:selectedTags', [...current, tag])
  }
}

function onTagChange(tags: string[]) {
  emit('update:selectedTags', tags)
}

function onSearchChange(val: string | number) {
  emit('update:searchQuery', String(val))
}
</script>

<style scoped>
.skill-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}
.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-tag {
  cursor: pointer;
}
</style>
```

- [ ] **Step 3: 验证编译**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/skills/
git commit -m "feat: add SkillCard and SkillFilter components"
```

---

### Task 13: AgentCard + AgentFilter 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/agents/AgentCard.vue`
- Create: `harness-engineering-py/frontend/src/components/agents/AgentFilter.vue`

- [ ] **Step 1: 创建 AgentCard.vue**

```vue
<template>
  <el-card shadow="hover" class="agent-card">
    <div class="agent-header">
      <div class="agent-icon">
        <el-icon :size="20"><component :is="iconComponent" /></el-icon>
      </div>
      <div class="agent-info">
        <h3 class="agent-name">{{ agent.name }}</h3>
        <p class="agent-desc">{{ agent.description }}</p>
      </div>
    </div>
    <div class="agent-tags">
      <el-tag v-for="tag in agent.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'
import type { Agent } from '@/types'

const props = defineProps<{ agent: Agent }>()

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    Bot: Icons.Robot,
    FlaskConical: Icons.Orange,
    Server: Icons.Monitor,
    BookOpen: Icons.Reading,
    ShieldCheck: Icons.Checked,
    BarChart3: Icons.DataAnalysis,
    Blocks: Icons.Grid,
    GitBranch: Icons.Connection,
  }
  return iconMap[props.agent.icon] || Icons.Robot
})
</script>

<style scoped>
.agent-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.agent-card:hover {
  transform: translateY(-2px);
}
.agent-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.agent-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  flex-shrink: 0;
}
.agent-info {
  min-width: 0;
  flex: 1;
}
.agent-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
}
.agent-desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.agent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
</style>
```

- [ ] **Step 2: 创建 AgentFilter.vue**

```vue
<template>
  <div class="agent-filter">
    <el-input
      v-model="searchModel"
      placeholder="搜索 Agents..."
      :prefix-icon="Search"
      clearable
      @input="onSearchChange"
    />
    <div class="filter-tags">
      <el-tag
        :type="selectedTags.length === 0 ? 'primary' : 'info'"
        class="filter-tag"
        @click="onTagChange([])"
      >
        全部
      </el-tag>
      <el-tag
        v-for="tag in tags"
        :key="tag"
        :type="selectedTags.includes(tag) ? 'primary' : 'info'"
        class="filter-tag"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{
  tags: string[]
  selectedTags: string[]
  searchQuery: string
}>()

const emit = defineEmits<{
  'update:selectedTags': [tags: string[]]
  'update:searchQuery': [query: string]
}>()

const searchModel = ref(props.searchQuery)

watch(() => props.searchQuery, (val) => {
  searchModel.value = val
})

function toggleTag(tag: string) {
  const current = [...props.selectedTags]
  if (current.includes(tag)) {
    emit('update:selectedTags', current.filter(t => t !== tag))
  } else {
    emit('update:selectedTags', [...current, tag])
  }
}

function onTagChange(tags: string[]) {
  emit('update:selectedTags', tags)
}

function onSearchChange(val: string | number) {
  emit('update:searchQuery', String(val))
}
</script>

<style scoped>
.agent-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}
.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-tag {
  cursor: pointer;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/agents/
git commit -m "feat: add AgentCard and AgentFilter components"
```

---

### Task 14: SkillsView + AgentsView + useMarketFilter

**Files:**
- Create: `harness-engineering-py/frontend/src/composables/useMarketFilter.ts`
- Replace: `harness-engineering-py/frontend/src/views/SkillsView.vue`
- Replace: `harness-engineering-py/frontend/src/views/AgentsView.vue`

- [ ] **Step 1: 创建 src/composables/useMarketFilter.ts**

```typescript
import { ref, computed } from 'vue'
import type { MarketItem } from '@/types'

export function useMarketFilter(items: MarketItem[], tags: string[]) {
  const selectedTags = ref<string[]>([])
  const searchQuery = ref('')

  const filtered = computed(() => {
    let result = [...items]
    if (selectedTags.value.length > 0) {
      result = result.filter(item =>
        item.tags.some(tag => selectedTags.value.includes(tag))
      )
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      result = result.filter(item =>
        item.name.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q)
      )
    }
    return result
  })

  return { selectedTags, searchQuery, filtered }
}
```

- [ ] **Step 2: 创建 SkillsView.vue**

```vue
<template>
  <div class="skills-page">
    <h2 class="page-title">Skills 市场</h2>
    <SkillFilter
      :tags="skillTags"
      v-model:selected-tags="selectedTags"
      v-model:search-query="searchQuery"
    />
    <div class="skills-grid">
      <SkillCard v-for="skill in filtered" :key="skill.id" :skill="skill" />
    </div>
    <el-empty v-if="filtered.length === 0" description="没有匹配的 Skills" />
  </div>
</template>

<script setup lang="ts">
import SkillCard from '@/components/skills/SkillCard.vue'
import SkillFilter from '@/components/skills/SkillFilter.vue'
import { useMarketFilter } from '@/composables/useMarketFilter'
import { skills, skillTags } from '@/mock/data'

const { selectedTags, searchQuery, filtered } = useMarketFilter(skills, skillTags)
</script>

<style scoped>
.skills-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
}
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
```

- [ ] **Step 3: 创建 AgentsView.vue**

```vue
<template>
  <div class="agents-page">
    <h2 class="page-title">Agents 市场</h2>
    <AgentFilter
      :tags="agentTags"
      v-model:selected-tags="selectedTags"
      v-model:search-query="searchQuery"
    />
    <div class="agents-grid">
      <AgentCard v-for="agent in filtered" :key="agent.id" :agent="agent" />
    </div>
    <el-empty v-if="filtered.length === 0" description="没有匹配的 Agents" />
  </div>
</template>

<script setup lang="ts">
import AgentCard from '@/components/agents/AgentCard.vue'
import AgentFilter from '@/components/agents/AgentFilter.vue'
import { useMarketFilter } from '@/composables/useMarketFilter'
import { agents, agentTags } from '@/mock/data'

const { selectedTags, searchQuery, filtered } = useMarketFilter(agents, agentTags)
</script>

<style scoped>
.agents-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
}
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
```

- [ ] **Step 4: 验证编译和启动**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useMarketFilter.ts frontend/src/views/SkillsView.vue frontend/src/views/AgentsView.vue
git commit -m "feat: add SkillsView, AgentsView and useMarketFilter composable"
```

---

### Task 15: ChatMessage + ThoughtBlock 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/workflow/ChatMessage.vue`
- Create: `harness-engineering-py/frontend/src/components/workflow/ThoughtBlock.vue`

- [ ] **Step 1: 创建 ThoughtBlock.vue**

```vue
<template>
  <div v-if="content" class="thought-block">
    <div class="thought-header" @click="expanded = !expanded">
      <el-icon :size="14"><component :is="expanded ? ArrowDown : ArrowRight" /></el-icon>
      <span class="thought-label">思考过程</span>
    </div>
    <div v-show="expanded" class="thought-content">
      <pre>{{ content }}</pre>
      <div v-if="isStreaming" class="thought-streaming-indicator">...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ArrowDown, ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  content: string
  isStreaming: boolean
}>()

const expanded = ref(false)
</script>

<style scoped>
.thought-block {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
.thought-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  background: var(--el-fill-color-light);
}
.thought-label {
  font-weight: 500;
}
.thought-content {
  padding: 10px;
  background: var(--el-bg-color);
}
.thought-content pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--el-text-color-regular);
  max-height: 200px;
  overflow-y: auto;
}
.thought-streaming-indicator {
  color: var(--el-color-primary);
  font-size: 12px;
  margin-top: 4px;
}
</style>
```

- [ ] **Step 2: 创建 ChatMessage.vue**

```vue
<template>
  <div class="chat-message" :class="[message.role]">
    <template v-if="message.role === 'user'">
      <div class="message-bubble user-bubble">
        <p>{{ message.content }}</p>
      </div>
    </template>

    <template v-else-if="message.role === 'assistant' && message.permissionRequest">
      <PermissionCard
        :request="message.permissionRequest"
        :decision="message.permissionDecision"
        @resolve="onResolvePermission"
      />
    </template>

    <template v-else-if="message.role === 'assistant'">
      <div class="message-bubble assistant-bubble">
        <ThoughtBlock
          v-if="message.thoughtContent"
          :content="message.thoughtContent"
          :is-streaming="message.isStreaming ?? false"
        />
        <div v-if="message.content" class="message-text" v-html="renderedContent" />
        <div v-if="message.isStreaming" class="streaming-cursor">|</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import ThoughtBlock from './ThoughtBlock.vue'
import PermissionCard from './PermissionCard.vue'

const props = defineProps<{
  message: ChatMessageType
}>()

const emit = defineEmits<{
  resolvePermission: [requestId: string, optionId: string]
}>()

const renderedContent = computed(() => {
  let text = props.message.content
  // Bold markers
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Inline code
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  // Code blocks
  text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
  // Line breaks
  text = text.replace(/\n/g, '<br/>')
  return text
})

function onResolvePermission(requestId: string, optionId: string) {
  emit('resolvePermission', requestId, optionId)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 16px;
}
.chat-message.user {
  justify-content: flex-end;
}
.chat-message.assistant {
  justify-content: flex-start;
}
.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.user-bubble {
  background: var(--el-color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.user-bubble p {
  margin: 0;
}
.assistant-bubble {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-bottom-left-radius: 4px;
}
.message-text {
  word-break: break-word;
}
.message-text :deep(code) {
  background: var(--el-fill-color);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.message-text :deep(pre) {
  background: var(--el-fill-color);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.message-text :deep(pre code) {
  background: none;
  padding: 0;
}
.streaming-cursor {
  display: inline;
  animation: blink 1s infinite;
  color: var(--el-color-primary);
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/workflow/ChatMessage.vue frontend/src/components/workflow/ThoughtBlock.vue
git commit -m "feat: add ChatMessage and ThoughtBlock components"
```

---

### Task 16: PermissionCard + ToolCallCard 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/workflow/PermissionCard.vue`
- Create: `harness-engineering-py/frontend/src/components/workflow/ToolCallCard.vue`

- [ ] **Step 1: 创建 PermissionCard.vue**

```vue
<template>
  <el-card class="permission-card" :class="{ 'is-resolved': !!decision }">
    <div class="perm-header">
      <el-icon :size="16"><WarningFilled /></el-icon>
      <span class="perm-type">{{ request.type }}</span>
    </div>
    <p class="perm-desc">{{ request.description }}</p>
    <p v-if="request.detail" class="perm-detail">{{ request.detail }}</p>
    <div v-if="!decision" class="perm-actions">
      <el-button
        v-for="option in request.options"
        :key="option.id"
        :type="option.style === 'danger' ? 'danger' : option.style === 'primary' ? 'primary' : 'default'"
        size="small"
        @click="onResolve(option.id)"
      >
        {{ option.label }}
      </el-button>
    </div>
    <div v-else class="perm-resolved">
      <el-tag type="info">已选择: {{ decision.label }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'
import type { PermissionRequest } from '@/types/chat'

const props = defineProps<{
  request: PermissionRequest
  decision?: { optionId: string; label: string }
}>()

const emit = defineEmits<{
  resolve: [requestId: string, optionId: string]
}>()

function onResolve(optionId: string) {
  emit('resolve', props.request.id, optionId)
}
</script>

<style scoped>
.permission-card {
  max-width: 400px;
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-5);
}
.permission-card.is-resolved {
  opacity: 0.7;
}
.perm-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.perm-type {
  font-weight: 600;
  font-size: 14px;
}
.perm-desc {
  margin: 0 0 4px;
  font-size: 13px;
}
.perm-detail {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
.perm-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.perm-resolved {
  margin-top: 8px;
}
</style>
```

- [ ] **Step 2: 创建 ToolCallCard.vue**

```vue
<template>
  <div class="tool-call-card">
    <div class="tool-header" @click="expanded = !expanded">
      <el-icon :size="14"><Tools /></el-icon>
      <span class="tool-name">{{ name }}</span>
      <el-icon :size="12" class="expand-icon"><component :is="expanded ? ArrowDown : ArrowRight" /></el-icon>
    </div>
    <div v-show="expanded" class="tool-body">
      <div v-if="input" class="tool-section">
        <div class="tool-label">Input:</div>
        <pre>{{ input }}</pre>
      </div>
      <div v-if="output" class="tool-section">
        <div class="tool-label">Output:</div>
        <pre>{{ output }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Tools, ArrowDown, ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  name: string
  input?: string
  output?: string
}>()

const expanded = ref(false)
</script>

<style scoped>
.tool-call-card {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
.tool-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  background: var(--el-fill-color-light);
}
.tool-name {
  font-weight: 500;
  flex: 1;
}
.expand-icon {
  color: var(--el-text-color-secondary);
}
.tool-body {
  padding: 10px;
  background: var(--el-bg-color);
}
.tool-section {
  margin-bottom: 8px;
}
.tool-section:last-child {
  margin-bottom: 0;
}
.tool-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}
.tool-body pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 150px;
  overflow-y: auto;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/workflow/PermissionCard.vue frontend/src/components/workflow/ToolCallCard.vue
git commit -m "feat: add PermissionCard and ToolCallCard components"
```

---

### Task 17: ChatInput + EngineInfo 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/workflow/ChatInput.vue`
- Create: `harness-engineering-py/frontend/src/components/workflow/EngineInfo.vue`

- [ ] **Step 1: 创建 ChatInput.vue**

```vue
<template>
  <div class="chat-input-area">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
      :disabled="isStreaming"
      resize="none"
      @keydown.enter.exact.prevent="handleSend"
    />
    <div class="input-actions">
      <el-button
        v-if="isStreaming"
        type="danger"
        :icon="CloseBold"
        @click="$emit('cancel')"
      >
        取消
      </el-button>
      <el-button
        v-else
        type="primary"
        :icon="Promotion"
        :disabled="!inputText.trim()"
        @click="handleSend"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion, CloseBold } from '@element-plus/icons-vue'

defineProps<{ isStreaming: boolean }>()
const emit = defineEmits<{
  send: [content: string]
  cancel: []
}>()

const inputText = ref('')

function handleSend() {
  const content = inputText.value.trim()
  if (!content) return
  emit('send', content)
  inputText.value = ''
}
</script>

<style scoped>
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}
.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
```

- [ ] **Step 2: 创建 EngineInfo.vue**

```vue
<template>
  <div class="engine-info">
    <span class="engine-label">{{ engineName }}</span>
    <el-divider direction="vertical" />
    <span class="model-label">{{ modelName }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  engineName: string
  modelName: string
}>()
</script>

<style scoped>
.engine-info {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}
.engine-label {
  font-weight: 500;
}
.model-label {
  color: var(--el-text-color-regular);
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/workflow/ChatInput.vue frontend/src/components/workflow/EngineInfo.vue
git commit -m "feat: add ChatInput and EngineInfo components"
```

---

### Task 18: ChatStream + ChatSidebar 组件

**Files:**
- Create: `harness-engineering-py/frontend/src/components/workflow/ChatStream.vue`
- Create: `harness-engineering-py/frontend/src/components/workflow/ChatSidebar.vue`

- [ ] **Step 1: 创建 ChatStream.vue**

```vue
<template>
  <div class="chat-stream" ref="scrollContainer">
    <div v-if="messages.length === 0" class="chat-empty">
      <el-empty description="发送消息开始对话" />
    </div>
    <ChatMessage
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
      @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import ChatMessage from './ChatMessage.vue'

const props = defineProps<{
  messages: ChatMessageType[]
}>()

defineEmits<{
  resolvePermission: [requestId: string, optionId: string]
}>()

const scrollContainer = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-stream {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
```

- [ ] **Step 2: 创建 ChatSidebar.vue**

```vue
<template>
  <div class="chat-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" :icon="Plus" size="small" @click="$emit('newSession')" class="new-session-btn">
        新建会话
      </el-button>
    </div>

    <div class="sidebar-sessions">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentSessionId }"
        @click="$emit('selectSession', session.id)"
      >
        <span class="session-title">{{ session.title || '新会话' }}</span>
        <el-button
          :icon="Delete"
          size="small"
          text
          type="danger"
          @click.stop="$emit('deleteSession', session.id)"
        />
      </div>
      <el-empty v-if="sessions.length === 0" description="暂无会话，点击新建" :image-size="60" />
    </div>

    <div class="sidebar-footer">
      <EngineInfo
        :engine-name="engineInfo?.name || 'OpenCode'"
        :model-name="model"
      />
      <div class="model-select">
        <span class="model-label">模型</span>
        <el-select v-model="modelValue" size="small" @change="onModelChange" class="model-selector">
          <el-option
            v-for="m in (engineInfo?.models || [])"
            :key="m.id"
            :label="m.name"
            :value="m.id"
          />
        </el-select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { ChatSession, EngineAvailability } from '@/types/chat'
import EngineInfo from './EngineInfo.vue'
import { useEngineStore } from '@/stores/engine'

const props = defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
}>()

const emit = defineEmits<{
  selectSession: [id: string]
  newSession: []
  deleteSession: [id: string]
  modelChange: [model: string]
}>()

const engineStore = useEngineStore()
const engineInfo = ref<EngineAvailability | null>(null)
const modelValue = ref(props.model)

watch(() => props.model, (val) => { modelValue.value = val })

onMounted(async () => {
  await engineStore.fetchAvailability()
  engineInfo.value = engineStore.engineInfo
  if (engineInfo.value?.defaultModel && !props.model) {
    emit('modelChange', engineInfo.value.defaultModel)
  }
})

function onModelChange(val: string) {
  emit('modelChange', val)
}
</script>

<style scoped>
.chat-sidebar {
  width: 260px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color);
}
.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.new-session-btn {
  width: 100%;
}
.sidebar-sessions {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  margin-bottom: 2px;
}
.session-item:hover {
  background: var(--el-fill-color-light);
}
.session-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sidebar-footer {
  border-top: 1px solid var(--el-border-color-lighter);
}
.model-select {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
}
.model-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
.model-selector {
  flex: 1;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/workflow/ChatStream.vue frontend/src/components/workflow/ChatSidebar.vue
git commit -m "feat: add ChatStream and ChatSidebar components"
```

---

### Task 19: useChatStream Composable

**Files:**
- Create: `harness-engineering-py/frontend/src/composables/useChatStream.ts`

- [ ] **Step 1: 创建 useChatStream.ts**

```typescript
import { ref } from 'vue'
import type { ChatMessage, PermissionRequest } from '@/types/chat'

interface UseChatStreamOptions {
  sessionId: string
  model: string
  agentSessionId?: string
  onAgentSessionIdChange?: (id: string) => void
}

export function useChatStream(options: UseChatStreamOptions) {
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const currentChatId = ref<string | null>(null)
  const pendingPermission = ref<PermissionRequest | null>(null)
  let eventSource: EventSource | null = null

  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming.value) return

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMsg)
    isStreaming.value = true

    const assistantMsgId = `msg-assistant-${Date.now()}`
    messages.value.push({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    })

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          model: options.model,
          sessionId: options.sessionId,
          agentSessionId: options.agentSessionId || undefined,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        updateAssistant(assistantMsgId, { content: `错误: ${err.detail || err.error}`, isStreaming: false })
        isStreaming.value = false
        return
      }

      const { chatId } = await res.json()
      currentChatId.value = chatId

      const es = new EventSource(`/api/chat/stream?id=${chatId}`)
      eventSource = es

      es.addEventListener('delta', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + data.content }
            : m
        )
      })

      es.addEventListener('thinking', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, thoughtContent: (m.thoughtContent || '') + data.content }
            : m
        )
      })

      es.addEventListener('permission_request', (e) => {
        const data = JSON.parse(e.data)
        pendingPermission.value = data.request
        messages.value.push({
          id: `perm-msg-${data.request.id}`,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          permissionRequest: data.request,
        })
      })

      es.addEventListener('done', (e) => {
        const data = JSON.parse(e.data)
        if (data.sessionId && options.onAgentSessionIdChange) {
          options.onAgentSessionIdChange(data.sessionId)
        }
        updateAssistant(assistantMsgId, { isStreaming: false })
        isStreaming.value = false
        es.close()
        eventSource = null
      })

      es.addEventListener('failed', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false }
            : m
        )
        isStreaming.value = false
        es.close()
        eventSource = null
      })

      es.addEventListener('engine_error', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false }
            : m
        )
      })

      es.onerror = () => {
        updateAssistant(assistantMsgId, { isStreaming: false })
        isStreaming.value = false
        es.close()
        eventSource = null
      }
    } catch (error) {
      updateAssistant(assistantMsgId, { content: `连接失败: ${error}`, isStreaming: false })
      isStreaming.value = false
    }
  }

  function updateAssistant(id: string, updates: Partial<ChatMessage>) {
    messages.value = messages.value.map(m =>
      m.id === id ? { ...m, ...updates } : m
    )
  }

  async function resolvePermission(requestId: string, optionId: string) {
    pendingPermission.value = null
    messages.value = messages.value.map(m =>
      m.permissionRequest?.id === requestId
        ? { ...m, permissionDecision: { optionId, label: optionId } }
        : m
    )
    await fetch('/api/chat/permission', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requestId, optionId }),
    })
  }

  async function cancelStream() {
    if (currentChatId.value) {
      await fetch(`/api/chat/stream?id=${currentChatId.value}`, { method: 'DELETE' })
    }
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isStreaming.value = false
  }

  return {
    messages,
    isStreaming,
    pendingPermission,
    sendMessage,
    resolvePermission,
    cancelStream,
  }
}
```

- [ ] **Step 2: 验证编译**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/useChatStream.ts
git commit -m "feat: add useChatStream composable for SSE chat streaming"
```

---

### Task 20: ChatLayout + WorkflowView

**Files:**
- Create: `harness-engineering-py/frontend/src/components/workflow/ChatLayout.vue`
- Replace: `harness-engineering-py/frontend/src/views/WorkflowView.vue`

- [ ] **Step 1: 创建 ChatLayout.vue**

```vue
<template>
  <div class="chat-layout">
    <ChatSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :model="model"
      @select-session="$emit('selectSession', $event)"
      @new-session="$emit('newSession')"
      @delete-session="$emit('deleteSession', $event)"
      @model-change="$emit('modelChange', $event)"
    />
    <div class="chat-main">
      <EngineInfo
        v-if="currentSessionId"
        engine-name="OpenCode"
        :model-name="model"
      />
      <ChatStream
        :messages="messages"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
      <ChatInput
        :is-streaming="isStreaming"
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession, ChatMessage } from '@/types/chat'
import ChatSidebar from './ChatSidebar.vue'
import ChatStream from './ChatStream.vue'
import ChatInput from './ChatInput.vue'
import EngineInfo from './EngineInfo.vue'

defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
  messages: ChatMessage[]
  isStreaming: boolean
}>()

defineEmits<{
  selectSession: [id: string]
  newSession: []
  deleteSession: [id: string]
  modelChange: [model: string]
  sendMessage: [content: string]
  resolvePermission: [requestId: string, optionId: string]
  cancelStream: []
}>()
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 80px);
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>
```

- [ ] **Step 2: 创建 WorkflowView.vue**

```vue
<template>
  <div class="workflow-page">
    <ChatLayout
      :sessions="chatStore.sessions"
      :current-session-id="chatStore.currentSessionId"
      :model="chatStore.model"
      :messages="chatMessages"
      :is-streaming="isStreaming"
      @select-session="handleSelectSession"
      @new-session="handleNewSession"
      @delete-session="handleDeleteSession"
      @model-change="handleModelChange"
      @send-message="handleSendMessage"
      @resolve-permission="handleResolvePermission"
      @cancel-stream="handleCancelStream"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, ref } from 'vue'
import ChatLayout from '@/components/workflow/ChatLayout.vue'
import { useChatStore } from '@/stores/chat'
import { useChatStream } from '@/composables/useChatStream'
import type { ChatMessage } from '@/types/chat'

const chatStore = useChatStore()

const {
  messages,
  isStreaming,
  sendMessage,
  resolvePermission,
  cancelStream,
} = useChatStream({
  get sessionId() { return chatStore.currentSessionId || '' },
  get model() { return chatStore.model },
  get agentSessionId() { return chatStore.agentSessionId },
  onAgentSessionIdChange(id: string) {
    chatStore.agentSessionId = id
  },
})

const chatMessages = ref<ChatMessage[]>(messages.value || [])

watch(messages, (val) => { chatMessages.value = val }, { deep: true })

async function loadSessions() {
  try {
    const res = await fetch('/api/chat/sessions')
    const data = await res.json()
    chatStore.setSessions(data.sessions || [])
  } catch (err) {
    console.error('Failed to load sessions:', err)
  }
}

onMounted(() => {
  loadSessions()
})

function handleSelectSession(id: string) {
  chatStore.selectSession(id)
  // Sync messages from composable
  messages.value = chatStore.messages
}

async function handleNewSession() {
  try {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine: 'opencode', model: chatStore.model }),
    })
    const data = await res.json()
    chatStore.setSessions([data.session, ...chatStore.sessions])
    chatStore.selectSession(data.session.id)
    messages.value = []
  } catch (err) {
    console.error('Failed to create session:', err)
  }
}

async function handleDeleteSession(id: string) {
  try {
    await fetch('/api/chat/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    chatStore.setSessions(chatStore.sessions.filter(s => s.id !== id))
    if (chatStore.currentSessionId === id) {
      chatStore.clearSession()
      messages.value = []
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

function handleModelChange(model: string) {
  chatStore.model = model
}

function handleSendMessage(content: string) {
  sendMessage(content)
}

function handleResolvePermission(requestId: string, optionId: string) {
  resolvePermission(requestId, optionId)
}

function handleCancelStream() {
  cancelStream()
}
</script>

<style scoped>
.workflow-page {
  height: 100%;
  margin: -24px;
}
</style>
```

- [ ] **Step 3: 验证编译**

```bash
cd harness-engineering-py/frontend
npx vue-tsc --noEmit 2>&1 | head -30
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/workflow/ChatLayout.vue frontend/src/views/WorkflowView.vue
git commit -m "feat: add ChatLayout and WorkflowView with full chat integration"
```

---

## Part 3: 集成验证

### Task 21: 端到端验证

- [ ] **Step 1: 启动后端**

```bash
cd harness-engineering-py/backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000 &
sleep 3
```

- [ ] **Step 2: 验证后端 API**

```bash
# Health check
curl -s http://localhost:8000/api/health

# List sessions (should be empty)
curl -s http://localhost:8000/api/chat/sessions

# Create a session
curl -s -X POST http://localhost:8000/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"engine":"opencode","model":"claude-sonnet-4-6"}'

# Engine availability
curl -s http://localhost:8000/api/engines/availability
```

Expected: All return valid JSON with 200 status.

- [ ] **Step 3: 启动前端**

```bash
cd harness-engineering-py/frontend
npm run dev &
sleep 5
```

- [ ] **Step 4: 验证前端页面**

```bash
# Homepage redirects to /skills
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/

# Skills page
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/skills

# Agents page
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/agents

# Workflow page
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/workflow
```

Expected: All return 200.

- [ ] **Step 5: 验证前端 Vite 代理到后端**

```bash
curl -s http://localhost:3000/api/health
```

Expected: `{"status":"ok"}` (proxied from backend).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: complete Vue 3 + FastAPI migration - all pages and APIs functional"
```
