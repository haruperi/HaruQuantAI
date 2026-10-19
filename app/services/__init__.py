# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Domain services, technical indicators, and core quantitative primitives.

Description:
    Provides centralized lazy export routing for quantitative services,
    technical indicator bases, temporal condition evaluators, and price
    primitives without triggering early circular package initialization.

Purpose:
    FEAT-SERVICES-ROUTER: Centralized lazy export facade for services packages.

Key Capabilities:
    - FR-SERVICES-LAZY-EXPORTS: Lazily export indicator and include primitives.
      Associated: `__getattr__()`
      Logging: Re-export namespace declarations; operational logging occurs in
        subsystem modules.

Python API Usage:
    ```python
    from app.services import BarPrice, BaseIndicator, format_timestamp
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_contracts.py --no-cov
    ```
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "Actions",
    "BarPrice",
    "BarTime",
    "BaseIndicator",
    "Comparisons",
    "DateTimeSeries",
    "Functions",
    "HeikenAshiPrice",
    "IndicatorSeries",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "TimeConditions",
    "Types",
    "Variable",
    "format_timestamp",
    "normalize_timestamps",
]


def __getattr__(name: str) -> Any:
    """Lazily load symbols from indicators and include on first access."""
    if name in ("BaseIndicator", "IndicatorSeries"):
        from app.services.indicators.base import BaseIndicator, IndicatorSeries

        return BaseIndicator if name == "BaseIndicator" else IndicatorSeries
    if name in (
        "BarTime",
        "DateTimeSeries",
        "TimeConditions",
        "format_timestamp",
        "normalize_timestamps",
    ):
        from app.services.include import bar_time

        return getattr(bar_time, name)
    if name in __all__:
        from app.services import include

        return getattr(include, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
