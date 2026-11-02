"""Comparative condition strategy blocks and logical operators.

Description:
    Implements all 21 StrategyQuant comparison snippet classes as modular
    typed blocks and facades for rule generation, builder integration, and
    backtesting execution.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful comparison blocks.
Key Capabilities:
    - FR-comparison-arithmetic: Order and equality comparison predicates.
    - FR-comparison-crossover: Directional line crossing predicates.
    - FR-comparison-trends: Monotonic rising, falling, and turning checks.
    - FR-comparison-count: Multi-bar condition persistence and percentiles.
    - FR-comparison-ma: Indicator moving average relationship checks.
    - FR-comparison-logic: Short-circuit AND, OR, and NOT logical operators.
Python API Usage:
    from app.extend.blocks.comparisons import (
        Comparisons,
        crosses_above,
        is_greater,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

from app.core.enums import MAType
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    DEFAULT_COUNT_PRECISION,
    MIN_TREND_BARS,
    _log_comparison,
    calculate_ma,
    calculate_wma,
    resolve_shift_value,
)
from app.extend.blocks.comparisons.changes_down import (
    changes_down,
    changes_down_spec,
)
from app.extend.blocks.comparisons.changes_up import (
    changes_up,
    changes_up_spec,
)
from app.extend.blocks.comparisons.condition_and import (
    condition_and,
    condition_and_spec,
)
from app.extend.blocks.comparisons.condition_not import (
    condition_not,
    condition_not_spec,
)
from app.extend.blocks.comparisons.condition_or import (
    condition_or,
    condition_or_spec,
)
from app.extend.blocks.comparisons.crosses_above import (
    crosses_above,
    crosses_above_spec,
)
from app.extend.blocks.comparisons.crosses_below import (
    crosses_below,
    crosses_below_spec,
)
from app.extend.blocks.comparisons.equals import equals, equals_spec
from app.extend.blocks.comparisons.facade import Comparisons
from app.extend.blocks.comparisons.indicator_above_ma import (
    indicator_above_ma,
    indicator_above_ma_spec,
)
from app.extend.blocks.comparisons.indicator_below_ma import (
    indicator_below_ma,
    indicator_below_ma_spec,
)
from app.extend.blocks.comparisons.indicator_crosses_above_ma import (
    indicator_crosses_above_ma,
    indicator_crosses_above_ma_spec,
)
from app.extend.blocks.comparisons.indicator_crosses_below_ma import (
    indicator_crosses_below_ma,
    indicator_crosses_below_ma_spec,
)
from app.extend.blocks.comparisons.is_falling import (
    is_falling,
    is_falling_spec,
)
from app.extend.blocks.comparisons.is_greater import (
    is_greater,
    is_greater_spec,
)
from app.extend.blocks.comparisons.is_greater_count import (
    is_greater_count,
    is_greater_count_spec,
)
from app.extend.blocks.comparisons.is_greater_or_equal import (
    is_greater_or_equal,
    is_greater_or_equal_spec,
)
from app.extend.blocks.comparisons.is_greater_percentile import (
    is_greater_percentile,
    is_greater_percentile_spec,
)
from app.extend.blocks.comparisons.is_lower import is_lower, is_lower_spec
from app.extend.blocks.comparisons.is_lower_count import (
    is_lower_count,
    is_lower_count_spec,
)
from app.extend.blocks.comparisons.is_lower_or_equal import (
    is_lower_or_equal,
    is_lower_or_equal_spec,
)
from app.extend.blocks.comparisons.is_lower_percentile import (
    is_lower_percentile,
    is_lower_percentile_spec,
)
from app.extend.blocks.comparisons.is_rising import is_rising, is_rising_spec
from app.extend.blocks.comparisons.not_equals import (
    not_equals,
    not_equals_spec,
)

__all__ = [
    "DEFAULT_COMPARISON_PRECISION",
    "DEFAULT_COUNT_PRECISION",
    "MIN_TREND_BARS",
    "Comparisons",
    "MAType",
    "_log_comparison",
    "calculate_ma",
    "calculate_wma",
    "changes_down",
    "changes_down_spec",
    "changes_up",
    "changes_up_spec",
    "condition_and",
    "condition_and_spec",
    "condition_not",
    "condition_not_spec",
    "condition_or",
    "condition_or_spec",
    "crosses_above",
    "crosses_above_spec",
    "crosses_below",
    "crosses_below_spec",
    "equals",
    "equals_spec",
    "indicator_above_ma",
    "indicator_above_ma_spec",
    "indicator_below_ma",
    "indicator_below_ma_spec",
    "indicator_crosses_above_ma",
    "indicator_crosses_above_ma_spec",
    "indicator_crosses_below_ma",
    "indicator_crosses_below_ma_spec",
    "is_falling",
    "is_falling_spec",
    "is_greater",
    "is_greater_count",
    "is_greater_count_spec",
    "is_greater_or_equal",
    "is_greater_or_equal_spec",
    "is_greater_percentile",
    "is_greater_percentile_spec",
    "is_greater_spec",
    "is_lower",
    "is_lower_count",
    "is_lower_count_spec",
    "is_lower_or_equal",
    "is_lower_or_equal_spec",
    "is_lower_percentile",
    "is_lower_percentile_spec",
    "is_lower_spec",
    "is_rising",
    "is_rising_spec",
    "not_equals",
    "not_equals_spec",
    "resolve_shift_value",
]
