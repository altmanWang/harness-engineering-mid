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
