import random
import string
import time
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ChatSession, CreateSessionRequest, DeleteSessionRequest,
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
        model=body.model or "",
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
