# -*- coding: utf-8 -*-
"""Stub: report_language for standalone a_stock_client."""

from __future__ import annotations

from typing import Optional


def normalize_report_language(lang: Optional[str] = None) -> str:
    """Stub: always returns 'zh'."""
    return "zh"


def is_supported_report_language_value(lang: str) -> bool:
    return lang in ("zh", "en")


def get_report_labels(lang: str = "zh") -> dict:
    return {}


def localize_operation_advice(text: str, lang: str = "zh") -> str:
    return text or ""


def localize_trend_prediction(text: str, lang: str = "zh") -> str:
    return text or ""


def localize_confidence_level(text: str, lang: str = "zh") -> str:
    return text or ""


def get_bias_status_emoji(status: str) -> str:
    return ""


def localize_bias_status(status: str, lang: str = "zh") -> str:
    return status or ""


def localize_chip_health(health: str, lang: str = "zh") -> str:
    return health or ""


def get_chip_unavailable_reason() -> str:
    return "chip data not available"


def is_chip_structure_unavailable(chip: object) -> bool:
    return True


def get_localized_stock_name(code: str, name: Optional[str] = None, lang: str = "zh") -> str:
    return name or code or ""


def get_signal_level(level: str) -> str:
    return level or ""


def infer_decision_type_from_advice(advice: str) -> str:
    return ""
