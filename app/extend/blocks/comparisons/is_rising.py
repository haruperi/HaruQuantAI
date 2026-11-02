"""Is Rising comparative condition strategy block.

Description:
    Evaluates whether indicator is rising monotonically over a bar window,
    matching StrategyQuant IsRising snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsRising block.
Key Capabilities:
    - FR-comparison-trend: Test monotonic rising progression over window.
Python API Usage:
    from app.extend.blocks.comparisons.is_rising import is_rising
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    MIN_TREND_BARS,
    _log_comparison,
    resolve_shift_value,
    round_value,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

is_rising_spec = BlockSpec(
    id="condition.is_rising",
    version="1.0.0",
    name="Is Rising",
    description="Evaluates whether indicator is rising monotonically over a bar window",
    category="comparisons",
    tags=("condition", "trend", "rising"),
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
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if rising"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_rising_spec)
def is_rising(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether indicator is rising monotonically over a bar window."""
    if bars < MIN_TREND_BARS:
        return _log_comparison("is_rising", False)
    p = precision if round_digits is None else round_digits
    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), p)
    if math.isnan(prev_val):
        return _log_comparison("is_rising", False)
    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(resolve_shift_value(indicator, bars + shift - 1 - i), p)
        if math.isnan(curr_val) or curr_val < prev_val:
            return _log_comparison("is_rising", False)
        if curr_val == prev_val and not not_strict:
            return _log_comparison("is_rising", False)
        if curr_val > prev_val:
            at_least_once = True
        prev_val = curr_val
    return _log_comparison("is_rising", at_least_once)


__all__ = ["is_rising", "is_rising_spec"]
