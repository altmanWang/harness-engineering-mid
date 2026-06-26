# -*- coding: utf-8 -*-
"""Stub: no-op run diagnostics for standalone a_stock_client."""

from __future__ import annotations

from typing import Any, Dict, Optional


def record_provider_run(
    data_type: str = "",
    provider: str = "",
    operation: str = "",
    success: bool = True,
    latency_ms: int = 0,
    error_type: str = "",
    error_message: str = "",
    fallback_to: Optional[str] = None,
    record_count: int = 0,
) -> None:
    """No-op stub."""


def record_provider_run_started(
    data_type: str = "",
    provider: str = "",
    operation: str = "",
) -> None:
    """No-op stub."""


def activate_run_diagnostic_context(*args: Any, **kwargs: Any) -> None:
    """No-op stub."""


def current_diagnostic_snapshot() -> Dict[str, Any]:
    return {}


def get_current_diagnostic_context() -> Optional[Any]:
    return None


def reset_run_diagnostic_context() -> None:
    """No-op stub."""


def record_history_run(*args: Any, **kwargs: Any) -> None:
    """No-op stub."""


def record_llm_run(*args: Any, **kwargs: Any) -> None:
    """No-op stub."""


def record_llm_run_started(*args: Any, **kwargs: Any) -> None:
    """No-op stub."""


def record_notification_run(*args: Any, **kwargs: Any) -> None:
    """No-op stub."""


def sanitize_diagnostic_text(text: str) -> str:
    return text or ""


def build_run_diagnostic_summary(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    return {}
