# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""HaruQuantAI services and indicators library."""

from __future__ import annotations

from typing import Any

__all__ = [
    "BarPrice",
    "BarTime",
    "BaseIndicator",
    "DateTimeSeries",
    "HeikenAshiPrice",
    "IndicatorSeries",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "TimeConditions",
    "format_timestamp",
    "normalize_timestamps",
]


def __getattr__(name: str) -> Any:
    """Lazily load symbols from indicators and utils on first access."""
    if name in ("BaseIndicator", "IndicatorSeries"):
        from app.services.indicators.base import BaseIndicator, IndicatorSeries

        symbols: dict[str, Any] = {
            "BaseIndicator": BaseIndicator,
            "IndicatorSeries": IndicatorSeries,
        }
        return symbols[name]
    if name in (
        "BarTime",
        "DateTimeSeries",
        "TimeConditions",
        "format_timestamp",
        "normalize_timestamps",
    ):
        from app.services.libs import bar_time

        return getattr(bar_time, name)
    if name in __all__:
        from app.services import utils

        return getattr(utils, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
