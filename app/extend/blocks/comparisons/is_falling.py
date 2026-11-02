"""Is Falling comparative condition strategy block.

Description:
    Evaluates whether indicator is falling monotonically over a bar window,
    matching StrategyQuant IsFalling snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsFalling block.
Key Capabilities:
    - FR-comparison-trend: Test monotonic falling progression over window.
Python API Usage:
    from app.extend.blocks.comparisons.is_falling import is_falling
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    MIN_TREND_BARS,
    _log_comparison,
    resolve_shift_value,
    round_value,
)

is_falling_spec = BlockSpec(
    id="condition.is_falling",
    version="1.0.0",
    name="Is Falling",
    description="Evaluates whether indicator is falling monotonically over a window",
    category="comparisons",
    tags=("condition", "trend", "falling"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Indicator series"),
        InputPort("bars", PortType.NUMBER, "Number of lookback bars", default=2),
        InputPort(
            "not_strict",
            PortType.BOOLEAN,
            "Allow flat intervals",
            default=False,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if falling"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_falling_spec)
def is_falling(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether indicator is falling monotonically over a bar window."""
    if bars < MIN_TREND_BARS:
        return _log_comparison("is_falling", False)
    p = precision if round_digits is None else round_digits
    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), p)
    if math.isnan(prev_val):
        return _log_comparison("is_falling", False)
    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(resolve_shift_value(indicator, bars + shift - 1 - i), p)
        if math.isnan(curr_val) or curr_val > prev_val:
            return _log_comparison("is_falling", False)
        if curr_val == prev_val and not not_strict:
            return _log_comparison("is_falling", False)
        if curr_val < prev_val:
            at_least_once = True
        prev_val = curr_val
    return _log_comparison("is_falling", at_least_once)


__all__ = ["is_falling", "is_falling_spec"]
