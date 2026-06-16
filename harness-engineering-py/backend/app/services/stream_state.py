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
