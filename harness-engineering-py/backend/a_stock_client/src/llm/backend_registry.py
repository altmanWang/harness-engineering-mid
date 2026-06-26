# -*- coding: utf-8 -*-
"""Stub: llm backend_registry for standalone a_stock_client."""

from __future__ import annotations

from typing import List

AUTO_AGENT_BACKEND_ID = "auto"
LITELLM_BACKEND_ID = "litellm"
SUPPORTED_AGENT_GENERATION_BACKENDS: List[str] = [AUTO_AGENT_BACKEND_ID, LITELLM_BACKEND_ID]
SUPPORTED_GENERATION_BACKENDS: List[str] = [LITELLM_BACKEND_ID]
