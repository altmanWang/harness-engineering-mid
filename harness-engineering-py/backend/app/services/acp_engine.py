import asyncio
import json
import os
import platform
import subprocess
from typing import Any, Callable, Dict, List, Optional


class ACPEngine:
    """通过子进程 stdio 与 opencode acp 通信的 ACP 协议引擎。

    使用手动 ndjson JSON-RPC 通信，不依赖 @agentclientprotocol/sdk。
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
        self.available_models = [
            {"modelId": m.get("modelId", m.get("id", "")), "name": m.get("name", m.get("modelId", ""))}
            for m in models_raw
        ]
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
