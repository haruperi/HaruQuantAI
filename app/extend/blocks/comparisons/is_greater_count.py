"""Is Greater Count condition persistence strategy block.

Description:
    Evaluates whether left > right remains true across a window of bars,
    matching StrategyQuant IsGreaterCount snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsGreaterCount block.
Key Capabilities:
    - FR-comparison-count: Test inequality persistence across lookback window.
Python API Usage:
    from app.extend.blocks.comparisons.is_greater_count import is_greater_count
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
    DEFAULT_COUNT_PRECISION,
    _log_comparison,
    _pair,
)

is_greater_count_spec = BlockSpec(
    id="condition.is_greater_count",
    version="1.0.0",
    name="Is Greater Count",
    description="Evaluates whether left > right remains true across a window of bars",
    category="comparisons",
    tags=("condition", "comparison", "count", "greater_count"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand"),
        InputPort("right", PortType.ANY, "Right operand"),
        InputPort("bars", PortType.NUMBER, "Number of lookback bars", default=2),
        InputPort(
            "not_strict",
            PortType.BOOLEAN,
            "Allow equal values",
            default=False,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if condition persisted"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_greater_count_spec)
def is_greater_count(
    left: Any,
    right: Any,
    bars: int = 2,
    *,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether left > right remains true across a window of bars."""
    if bars < 1:
        return _log_comparison("is_greater_count", False)
    at_least_once = False
    for i in range(bars):
        l_val, r_val = _pair(left, right, shift + i, precision)
        if math.isnan(l_val) or math.isnan(r_val) or l_val < r_val:
            return _log_comparison("is_greater_count", False)
        if l_val == r_val and not not_strict:
            return _log_comparison("is_greater_count", False)
        if l_val > r_val:
            at_least_once = True
    return _log_comparison("is_greater_count", at_least_once)


__all__ = ["is_greater_count", "is_greater_count_spec"]
