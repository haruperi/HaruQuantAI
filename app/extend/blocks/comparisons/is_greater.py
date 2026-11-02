"""Is Greater comparative inequality condition strategy block.

Description:
    Evaluates whether left operand is strictly greater than right operand,
    matching StrategyQuant IsGreater snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsGreater block.
Key Capabilities:
    - FR-comparison-inequality: Test strictly greater comparison.
Python API Usage:
    from app.extend.blocks.comparisons.is_greater import is_greater
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
    _log_comparison,
    _pair,
)

is_greater_spec = BlockSpec(
    id="condition.is_greater",
    version="1.0.0",
    name="Is Greater",
    description="Evaluates whether left operand is strictly greater than right",
    category="comparisons",
    tags=("condition", "comparison", "order", "is_greater"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left > right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_greater_spec)
def is_greater(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left operand is strictly greater than right operand."""
    val1, val2 = _pair(
        left,
        right,
        shift,
        precision,
        s1=shift1,
        s2=shift2,
        rd=round_digits,
    )
    if math.isnan(val1) or math.isnan(val2):
        return _log_comparison("is_greater", False)
    res = val1 > val2
    return _log_comparison("is_greater", res)


__all__ = ["is_greater", "is_greater_spec"]
