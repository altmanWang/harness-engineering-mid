# -*- coding: utf-8 -*-
"""Minimal Config stub for a_stock_client standalone operation.

Provides just the fields that data_provider modules access at runtime.
Reads from environment variables (os.environ), matching the original
src/config.py defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


def _parse_env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key, "").strip().lower()
    if val in ("true", "1", "yes", "on"):
        return True
    if val in ("false", "0", "no", "off"):
        return False
    return default


def _parse_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _parse_env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


@dataclass
class Config:
    """Minimal config for data_provider standalone operation."""

    # --- Data source auth ---
    tushare_token: str = ""
    tickflow_api_key: str = ""
    finnhub_api_key: str = ""
    alphavantage_api_key: str = ""
    longbridge_app_key: str = ""
    longbridge_app_secret: str = ""
    longbridge_access_token: str = ""
    longbridge_oauth_client_id: str = ""

    # --- Realtime / enhancement toggles ---
    enable_realtime_quote: bool = True
    enable_realtime_technical_indicators: bool = True
    enable_chip_distribution: bool = True
    enable_eastmoney_patch: bool = False
    realtime_source_priority: str = "tencent,akshare_sina,efinance,akshare_em"
    realtime_cache_ttl: int = 600
    circuit_breaker_cooldown: int = 300
    prefetch_realtime_quotes: bool = True

    # --- Fundamental pipeline ---
    enable_fundamental_pipeline: bool = True
    fundamental_stage_timeout_seconds: float = 30.0
    fundamental_fetch_timeout_seconds: float = 15.0
    fundamental_retry_max: int = 2
    fundamental_cache_ttl_seconds: int = 300
    fundamental_cache_max_entries: int = 500

    # --- SQLite (unused by data_provider but referenced in config_registry) ---
    sqlite_wal_enabled: bool = True
    sqlite_busy_timeout_ms: int = 5000
    sqlite_write_retry_max: int = 3
    sqlite_write_retry_base_delay: float = 0.1

    # Singleton
    _instance: Optional["Config"] = field(default=None, init=False, repr=False)

    @classmethod
    def get_instance(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls._load_from_env()
        return cls._instance

    @classmethod
    def _load_from_env(cls) -> "Config":
        return cls(
            tushare_token=os.getenv("TUSHARE_TOKEN", "").strip(),
            tickflow_api_key=os.getenv("TICKFLOW_API_KEY", "").strip(),
            finnhub_api_key=os.getenv("FINNHUB_API_KEY", "").strip(),
            alphavantage_api_key=os.getenv("ALPHAVANTAGE_API_KEY", "").strip(),
            longbridge_app_key=os.getenv("LONGBRIDGE_APP_KEY", "").strip(),
            longbridge_app_secret=os.getenv("LONGBRIDGE_APP_SECRET", "").strip(),
            longbridge_access_token=os.getenv("LONGBRIDGE_ACCESS_TOKEN", "").strip(),
            longbridge_oauth_client_id=os.getenv("LONGBRIDGE_OAUTH_CLIENT_ID", "").strip(),
            enable_realtime_quote=_parse_env_bool("ENABLE_REALTIME_QUOTE", True),
            enable_realtime_technical_indicators=_parse_env_bool("ENABLE_REALTIME_TECHNICAL_INDICATORS", True),
            enable_chip_distribution=_parse_env_bool("ENABLE_CHIP_DISTRIBUTION", True),
            enable_eastmoney_patch=_parse_env_bool("ENABLE_EASTMONEY_PATCH", False),
            realtime_source_priority=os.getenv("REALTIME_SOURCE_PRIORITY", "tencent,akshare_sina,efinance,akshare_em").strip(),
            realtime_cache_ttl=_parse_env_int("REALTIME_CACHE_TTL", 600),
            circuit_breaker_cooldown=_parse_env_int("CIRCUIT_BREAKER_COOLDOWN", 300),
            prefetch_realtime_quotes=_parse_env_bool("PREFETCH_REALTIME_QUOTES", True),
            enable_fundamental_pipeline=_parse_env_bool("ENABLE_FUNDAMENTAL_PIPELINE", True),
            fundamental_stage_timeout_seconds=_parse_env_float("FUNDAMENTAL_STAGE_TIMEOUT_SECONDS", 30.0),
            fundamental_fetch_timeout_seconds=_parse_env_float("FUNDAMENTAL_FETCH_TIMEOUT_SECONDS", 15.0),
            fundamental_retry_max=_parse_env_int("FUNDAMENTAL_RETRY_MAX", 2),
            fundamental_cache_ttl_seconds=_parse_env_int("FUNDAMENTAL_CACHE_TTL_SECONDS", 300),
            fundamental_cache_max_entries=_parse_env_int("FUNDAMENTAL_CACHE_MAX_ENTRIES", 500),
        )


def get_config() -> Config:
    return Config.get_instance()


def setup_env():
    """No-op: env is already set by the caller or dotenv."""
    pass


FUNDAMENTAL_STAGE_TIMEOUT_SECONDS_DEFAULT = 30.0
