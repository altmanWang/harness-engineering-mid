# -*- coding: utf-8 -*-
"""Stub: stock index loader for standalone a_stock_client.

Returns None for all lookups since the stock index JSON files
are not bundled with the standalone module.
"""

from __future__ import annotations

from typing import Dict, Optional


def get_index_stock_name(stock_code: str) -> Optional[str]:
    """Stub: always returns None."""
    return None


def get_stock_name_index_map() -> Dict[str, str]:
    """Stub: always returns empty dict."""
    return {}


def resolve_index_stock_code(query: str) -> Optional[str]:
    """Stub: always returns None."""
    return None


def clear_stock_index_cache() -> None:
    """No-op stub."""
