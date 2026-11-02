"""Is Greater Percentile rank comparative condition strategy block.

Description:
    Evaluates whether indicator value exceeds percentile rank over past bars,
    matching StrategyQuant IsGreaterPercentil snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsGreaterPercentil block.
Key Capabilities:
    - FR-comparison-percentile: Test percentile rank exceedance over window.
Python API Usage:
    from app.extend.blocks.comparisons.is_greater_percentile import (
        is_greater_percentile,
    )
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
    resolve_shift_value,
    round_value,
)

is_greater_percentile_spec = BlockSpec(
    id="condition.is_greater_percentile",
    version="1.0.0",
    name="Is Greater Percentile",
    description=(
        "Evaluates whether indicator value exceeds percentile rank over past bars"
    ),
    category="comparisons",
    tags=("condition", "percentile", "greater_percentile"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Indicator series"),
        InputPort(
            "percentile",
            PortType.NUMBER,
            "Threshold percentage (0-100)",
            default=50.0,
        ),
        InputPort("bars", PortType.NUMBER, "Window lookback bars", default=10),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if rank > percentile"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_greater_percentile_spec)
def is_greater_percentile(
    indicator: Any,
    percentile: float = 50.0,
    bars: int = 10,
    shift: int = 0,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether indicator value exceeds percentile rank over past bars."""
    if bars <= 0:
        return _log_comparison("is_greater_percentile", False)
    curr_val = round_value(resolve_shift_value(indicator, shift), precision)
    if math.isnan(curr_val):
        return _log_comparison("is_greater_percentile", False)
    count = 1
    for i in range(bars):
        prev_val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(prev_val):
            return _log_comparison("is_greater_percentile", False)
        if curr_val > prev_val:
            count += 1
    res = (count / float(bars)) * 100.0 > round_value(percentile, precision)
    return _log_comparison("is_greater_percentile", res)


__all__ = ["is_greater_percentile", "is_greater_percentile_spec"]
