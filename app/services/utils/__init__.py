"""Shared services utility modules for temporal, price, and comparison operations.

Description:
    Consolidates utility primitives and feature extractors consumed by trading
    strategies, indicators, and broker services:
    - BarAndTime primitives: DateTimeSeries, BarTime, TimeConditions,
      normalize_timestamps, and format_timestamp.
    - Price primitives: BarPrice, QuotePrice, MTFPrice, SessionPrice,
      and HeikenAshiPrice.
    - Comparison primitives: Comparisons facade, MAType, arithmetic comparisons,
      bar-to-bar crossovers, trend/count persistence, percentile rankings,
      indicator-to-MA conditions, and compound boolean combinators.

Purpose:
    FEAT-SERVICES-UTILS: Re-export temporal, price, and comparison utility building
    blocks.

Key Capabilities:
    - FR-SERVICES-UTILS-EXPORTS: Provide centralized public access to utilities.
      Associated: `format_timestamp()`, `BarTime`, `BarPrice`, `Comparisons`.
      Logging: Re-export namespace declarations; operational logging occurs
        in component modules.

Python API Usage:
    ```python
    from app.services.utils import BarPrice, BarTime, Comparisons, format_timestamp

    formatted = format_timestamp(1704110400)
    comps = Comparisons()
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_comparisons.py --no-cov
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
from app.services.utils.comparisons import (
    Comparisons,
    MAType,
    calculate_ma,
    calculate_wma,
    condition_and,
    condition_not,
    condition_or,
    crosses_above,
    crosses_below,
    equals,
    indicator_above_ma,
    indicator_below_ma,
    indicator_crosses_above_ma,
    indicator_crosses_below_ma,
    is_falling,
    is_greater,
    is_greater_count,
    is_greater_or_equal,
    is_greater_percentile,
    is_lower,
    is_lower_count,
    is_lower_or_equal,
    is_lower_percentile,
    is_rising,
    not_equals,
    resolve_shift_value,
    round_value,
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
    "Comparisons",
    "DateTimeSeries",
    "HeikenAshiPrice",
    "MAType",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "TimeConditions",
    "calculate_ma",
    "calculate_wma",
    "condition_and",
    "condition_not",
    "condition_or",
    "crosses_above",
    "crosses_below",
    "equals",
    "format_timestamp",
    "indicator_above_ma",
    "indicator_below_ma",
    "indicator_crosses_above_ma",
    "indicator_crosses_below_ma",
    "is_falling",
    "is_greater",
    "is_greater_count",
    "is_greater_or_equal",
    "is_greater_percentile",
    "is_lower",
    "is_lower_count",
    "is_lower_or_equal",
    "is_lower_percentile",
    "is_rising",
    "normalize_timestamps",
    "not_equals",
    "resolve_shift_value",
    "round_value",
]
