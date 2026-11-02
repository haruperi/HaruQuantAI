"""Is Greater Or Equal comparative condition strategy block.

Description:
    Evaluates whether left operand is greater than or equal to right operand,
    matching StrategyQuant IsGreaterOrEqual snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsGreaterOrEqual block.
Key Capabilities:
    - FR-comparison-inequality: Test greater than or equal comparison.
Python API Usage:
    from app.extend.blocks.comparisons.is_greater_or_equal import (
        is_greater_or_equal,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    _log_comparison,
    _pair,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

is_greater_or_equal_spec = BlockSpec(
    id="condition.is_greater_or_equal",
    version="1.0.0",
    name="Is Greater Or Equal",
    description="Evaluates whether left operand is greater than or equal to right",
    category="comparisons",
    tags=("condition", "comparison", "order", "is_greater_or_equal"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left >= right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_greater_or_equal_spec)
def is_greater_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left operand is greater than or equal to right operand."""
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
        return _log_comparison("is_greater_or_equal", False)
    res = val1 >= val2
    return _log_comparison("is_greater_or_equal", res)


__all__ = ["is_greater_or_equal", "is_greater_or_equal_spec"]
