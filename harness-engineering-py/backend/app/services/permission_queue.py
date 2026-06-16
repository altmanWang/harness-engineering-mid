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
