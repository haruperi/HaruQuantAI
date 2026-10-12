"""Shared services utility modules for temporal, price, comparison, and function ops.

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
    - Function primitives: Functions facade, arithmetic operators (plus, minus,
      multiplication, division), math functions (abs, round, exp, log, sqrt,
      min/max), temporal builders (get_date, get_time), rolling rank extractors
      (indicator_highest, indicator_lowest), and MT5 broker symbol-integrated
      pip conversions (convert_price_to_pips, convert_pips_to_price).

Purpose:
    FEAT-SERVICES-UTILS: Re-export temporal, price, comparison, and function
    utility building blocks.

Key Capabilities:
    - FR-SERVICES-UTILS-EXPORTS: Provide centralized public access to utilities.
      Associated: `format_timestamp()`, `BarTime`, `BarPrice`, `Comparisons`,
        `Functions`.
      Logging: Re-export namespace declarations; operational logging occurs
        in component modules.

Python API Usage:
    ```python
    from app.services.utils import (
        BarPrice,
        BarTime,
        Comparisons,
        Functions,
        convert_price_to_pips,
        format_timestamp,
    )

    formatted = format_timestamp(1704110400)
    funcs = Functions()
    pips = convert_price_to_pips(0.0020, point=0.00001, digits=5)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_functions.py --no-cov
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
from app.services.utils.functions import (
    Functions,
    abs_val,
    convert_pips_to_price,
    convert_pips_to_price_symbol,
    convert_price_to_pips,
    convert_price_to_pips_symbol,
    custom_function,
    division,
    exponential,
    get_date,
    get_time,
    indicator_highest,
    indicator_lowest,
    logarithm,
    maximum,
    minimum,
    minus,
    multiplication,
    plus,
    register_custom_function,
    round_to_decimals,
    square_root,
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
    "Functions",
    "HeikenAshiPrice",
    "MAType",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "TimeConditions",
    "abs_val",
    "calculate_ma",
    "calculate_wma",
    "condition_and",
    "condition_not",
    "condition_or",
    "convert_pips_to_price",
    "convert_pips_to_price_symbol",
    "convert_price_to_pips",
    "convert_price_to_pips_symbol",
    "crosses_above",
    "crosses_below",
    "custom_function",
    "division",
    "equals",
    "exponential",
    "format_timestamp",
    "get_date",
    "get_time",
    "indicator_above_ma",
    "indicator_below_ma",
    "indicator_crosses_above_ma",
    "indicator_crosses_below_ma",
    "indicator_highest",
    "indicator_lowest",
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
    "logarithm",
    "maximum",
    "minimum",
    "minus",
    "multiplication",
    "normalize_timestamps",
    "not_equals",
    "plus",
    "register_custom_function",
    "resolve_shift_value",
    "round_to_decimals",
    "round_value",
    "square_root",
]
