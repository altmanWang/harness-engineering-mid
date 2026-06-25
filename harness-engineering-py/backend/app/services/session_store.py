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
                data = json.loads(content)
                # 兼容旧数据：没有 type 字段的默认为 "chat"
                if "type" not in data:
                    data["type"] = "chat"
                sessions.append(ChatSession(**data))
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
            data = json.loads(content)
            if "type" not in data:
                data["type"] = "chat"
            return ChatSession(**data)
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
