# -*- coding: utf-8 -*-
"""Stub: notification_noise for standalone a_stock_client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

NOTIFICATION_SEVERITIES: List[str] = []


def is_supported_notification_severity(severity: str) -> bool:
    return True


def parse_notification_quiet_hours(raw: str) -> Dict[str, Any]:
    return {}


def validate_notification_timezone(tz: str) -> str:
    return tz or "Asia/Shanghai"
