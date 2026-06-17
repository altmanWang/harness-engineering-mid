import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.acp_engine import ACPEngine


class _FakeProcess:
    def __init__(self, stdout):
        self.stdout = stdout


class _WritableStdin:
    def __init__(self):
        self.data = b""

    def write(self, data):
        self.data += data

    def flush(self):
        pass


class _FakeWritableProcess:
    def __init__(self):
        self.stdin = _WritableStdin()


class _RespondingStdin:
    def __init__(self, engine):
        self.engine = engine

    def write(self, data):
        request = __import__("json").loads(data.decode())
        self.engine._handle_line(__import__("json").dumps({"jsonrpc": "2.0", "id": request["id"], "result": {}}))

    def flush(self):
        pass


class _ImmediateResponseProcess:
    def __init__(self, engine):
        self.stdin = _RespondingStdin(engine)


class _CapturingACPEngine(ACPEngine):
    def __init__(self):
        super().__init__({"workingDirectory": "/workspace"})
        self.initialized = True
        self.session_id = "session-1"
        self.requests = []

    async def _send_request(self, method, params):
        self.requests.append((method, params))
        if method in ("session/new", "session/load"):
            return {"sessionId": "session-1"}
        if method == "session/prompt":
            return {"stopReason": "end_turn"}
        return {}


class ACPEngineMethodNameTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_session_uses_acp_session_new_method(self):
        engine = _CapturingACPEngine()

        await engine.create_session()

        self.assertEqual(engine.requests[0][0], "session/new")

    async def test_resume_session_uses_acp_session_load_method(self):
        engine = _CapturingACPEngine()

        await engine.resume_session("session-1")

        self.assertEqual(engine.requests[0][0], "session/load")

    async def test_prompt_uses_acp_session_prompt_method(self):
        engine = _CapturingACPEngine()

        await engine.send_prompt("hello")

        self.assertEqual(engine.requests[0][0], "session/prompt")

    async def test_set_model_uses_acp_session_set_model_method(self):
        engine = _CapturingACPEngine()

        await engine.set_model("provider/model")

        self.assertEqual(engine.requests[0][0], "session/set_model")

    def test_cancel_session_sends_acp_session_cancel_notification(self):
        engine = ACPEngine({})
        engine.session_id = "session-1"
        engine.process = _FakeWritableProcess()

        engine.cancel_session()

        self.assertEqual(
            engine.process.stdin.data.decode().strip(),
            '{"jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": "session-1"}}'
        )

    async def test_send_request_tracks_pending_before_writing(self):
        engine = ACPEngine({})
        engine.process = _ImmediateResponseProcess(engine)

        result = await asyncio.wait_for(engine._send_request("initialize", {}), timeout=0.3)

        self.assertEqual(result, {})


class ACPEngineInboundMethodTest(unittest.TestCase):
    def test_session_update_notification_emits_agent_message(self):
        engine = ACPEngine({})
        messages = []
        engine.on("agent-message", messages.append)

        engine._handle_line('{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"session-1","update":{"sessionUpdate":"agent_message_chunk","content":{"text":"hi"}}}}')

        self.assertEqual(messages, [{"text": "hi"}])

    def test_session_request_permission_registers_resolver_for_request(self):
        engine = ACPEngine({})
        permissions = []
        engine.on("permission", permissions.append)

        engine._handle_line('{"jsonrpc":"2.0","id":7,"method":"session/request_permission","params":{"sessionId":"session-1","id":"perm-1","options":[]}}')

        self.assertEqual(permissions, [{"sessionId": "session-1", "id": "perm-1", "options": []}])
        self.assertIsNotNone(engine._permission_resolver)

    def test_resolve_permission_replies_to_original_json_rpc_request_id(self):
        engine = ACPEngine({})
        engine.process = _FakeWritableProcess()

        engine._handle_line('{"jsonrpc":"2.0","id":7,"method":"session/request_permission","params":{"sessionId":"session-1","id":"perm-1","options":[]}}')
        engine.resolve_permission("allow")

        self.assertEqual(
            engine.process.stdin.data.decode().strip(),
            '{"jsonrpc": "2.0", "id": 7, "result": {"outcome": {"outcome": "selected", "optionId": "allow"}}}'
        )


class ACPEngineReadLoopTest(unittest.IsolatedAsyncioTestCase):
    async def test_read_loop_handles_newline_delimited_message_without_waiting_for_eof(self):
        engine = ACPEngine({})
        read_fd, write_fd = os.pipe()
        reader = os.fdopen(read_fd, "rb")
        writer = os.fdopen(write_fd, "wb", buffering=0)
        handled = asyncio.Event()
        lines = []

        def handle_line(line):
            lines.append(line)
            handled.set()

        engine.process = _FakeProcess(reader)
        engine._handle_line = handle_line

        task = asyncio.create_task(engine._read_loop())
        try:
            writer.write(b'{"jsonrpc":"2.0","id":1,"result":{}}\n')
            await asyncio.wait_for(handled.wait(), timeout=0.3)
            self.assertEqual(lines, ['{"jsonrpc":"2.0","id":1,"result":{}}'])
        finally:
            engine._stopping = True
            writer.close()
            await asyncio.wait_for(task, timeout=1)
            reader.close()


if __name__ == "__main__":
    unittest.main()
