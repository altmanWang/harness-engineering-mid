import asyncio
import json
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    SendMessageRequest, ResolvePermissionRequest, ChatMessage,
)
from app.services.engine_factory import get_or_create_engine
from app.services.engine_interface import EngineStreamEvent
from app.services.stream_state import (
    register_stream, append_stream_content, set_stream_status,
    get_stream, remove_stream,
)
from app.services.session_store import append_message, update_session_agent_id
from app.services.permission_queue import register_pending_permission, resolve_permission
from app.services.worktree_manager import ensure_worktree

router = APIRouter()

_active_chats: dict = {}
_stream_queues: dict = {}


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
                "workingDirectory": str(ensure_worktree(body.sessionId or None)),
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
async def stream_chat(id: str = Query(...)):
    task = _active_chats.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    queue: asyncio.Queue = asyncio.Queue()

    if id not in _stream_queues:
        _stream_queues[id] = []
    _stream_queues[id].append(queue)

    state = get_stream(id)
    buffered_content = state.stream_content if state else ""

    async def generate():
        try:
            yield f"event: connected\ndata: {json.dumps({'chatId': id})}\n\n"

            if buffered_content:
                yield f"event: delta\ndata: {json.dumps({'content': buffered_content})}\n\n"

            while True:
                try:
                    event_type, data = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
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
