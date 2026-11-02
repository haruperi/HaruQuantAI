"""Base contract and time utility helpers for TradingOptions.

Description:
    Defines the BaseTradingOption contract and time window calculation
    utilities for session and order gate evaluation.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Base class and utilities for TradingOptions.

Key Capabilities:
    - FR-trading-option-base: Base trading option contract and time parsing helpers.

Python API Usage:
    from app.extend.trading_options.base import BaseTradingOption, TradingOption

CLI Usage:
    python -m app.cli extend trading-options --list
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _parse_hhmm(time_val: int | str) -> int:
    """Convert HH:MM string or packed HHMM integer to packed HHMM (e.g. 1430)."""
    if isinstance(time_val, int):
        return time_val
    cleaned = time_val.strip()
    if ":" in cleaned:
        parts = cleaned.split(":")
        return int(parts[0]) * 100 + int(parts[1])
    return int(cleaned)


def _in_time_window(current_hhmm: int, start_hhmm: int, end_hhmm: int) -> bool:
    """Return whether current_hhmm falls within [start_hhmm, end_hhmm] (inclusive)."""
    if start_hhmm <= end_hhmm:
        return start_hhmm <= current_hhmm <= end_hhmm
    return current_hhmm >= start_hhmm or current_hhmm <= end_hhmm


class BaseTradingOption:
    """Base contract for runtime trading session and order options."""

    name: str = "BaseTradingOption"
    category: str = "TradingOptions"


TradingOption = BaseTradingOption

__all__ = [
    "BaseTradingOption",
    "TradingOption",
    "_in_time_window",
    "_parse_hhmm",
]
