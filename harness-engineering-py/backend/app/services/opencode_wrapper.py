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
                ["where", "opencode"] if platform.system() == "Windows" else ["command", "-v", "opencode"],
                capture_output=True, check=True, shell=shell
            )
            return True
        except Exception:
            return False

    async def execute(self, options: Dict[str, Any]) -> Dict[str, Any]:
        self._seen_tool_ids.clear()
        self._collected_output = ""

        prompt = options.get("prompt", "")
        # OpenCode interprets leading "/" as a slash command (e.g. /help, /clear)
        # and consumes it locally without sending to the AI agent.
        # Strip it so skill-name-like queries reach the LLM.
        if prompt.startswith("/"):
            prompt = prompt.lstrip("/")
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
                    "style": OpenCodeEngineWrapper._infer_option_style(opt_id),
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
