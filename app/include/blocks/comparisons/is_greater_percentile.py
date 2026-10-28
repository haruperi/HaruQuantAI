"""Is Greater Percentile rank comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.include.blocks.base import block
from app.include.blocks.comparisons._common import (
    DEFAULT_COUNT_PRECISION,
    resolve_shift_value,
    round_value,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
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
        InputPort("percentile", PortType.NUMBER, "Threshold percentage (0-100)"),
        InputPort("bars", PortType.NUMBER, "Window lookback bars"),
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
        return False
    curr_val = round_value(resolve_shift_value(indicator, shift), precision)
    if math.isnan(curr_val):
        return False
    count = 1
    for i in range(bars):
        prev_val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(prev_val):
            return False
        if curr_val > prev_val:
            count += 1
    return (count / float(bars)) * 100.0 > round_value(percentile, precision)


__all__ = ["is_greater_percentile", "is_greater_percentile_spec"]
