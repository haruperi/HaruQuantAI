"""Shared services utility modules for temporal and price operations.

Description:
    Consolidates utility primitives and feature extractors consumed by trading
    strategies, indicators, and broker services:
    - BarAndTime primitives: DateTimeSeries, BarTime, TimeConditions,
      normalize_timestamps, and format_timestamp.
    - Price primitives: BarPrice, QuotePrice, MTFPrice, SessionPrice,
      and HeikenAshiPrice.

Purpose:
    FEAT-SERVICES-UTILS: Re-export temporal and price utility building blocks.

Key Capabilities:
    - FR-SERVICES-UTILS-EXPORTS: Provide centralized public access to utilities.
      Associated: `format_timestamp()`, `BarTime`, `BarPrice`.
      Logging: Re-export namespace declarations; operational logging occurs
        in component modules.

Python API Usage:
    ```python
    from app.services.utils import BarTime, format_timestamp
    from app.services.utils.price import BarPrice

    formatted = format_timestamp(1704110400)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_time.py --no-cov
    ```
"""

from __future__ import annotations

from app.services.utils.bar_time import (
    BarTime,
    DateTimeSeries,
    TimeConditions,
    format_timestamp,
    normalize_timestamps,
)
from app.services.utils.price import (
    BarPrice,
    HeikenAshiPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
)

__all__ = [
    "BarPrice",
    "BarTime",
    "DateTimeSeries",
    "HeikenAshiPrice",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "TimeConditions",
    "format_timestamp",
    "normalize_timestamps",
]
