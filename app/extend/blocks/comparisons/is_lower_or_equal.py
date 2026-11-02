"""Is Lower Or Equal comparative condition strategy block.

Description:
    Evaluates whether left operand is lower than or equal to right operand,
    matching StrategyQuant IsLowerOrEqual snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful IsLowerOrEqual block.
Key Capabilities:
    - FR-comparison-inequality: Test lower than or equal comparison.
Python API Usage:
    from app.extend.blocks.comparisons.is_lower_or_equal import (
        is_lower_or_equal,
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
    DEFAULT_COMPARISON_PRECISION,
    _log_comparison,
    _pair,
)

is_lower_or_equal_spec = BlockSpec(
    id="condition.is_lower_or_equal",
    version="1.0.0",
    name="Is Lower Or Equal",
    description="Evaluates whether left operand is lower than or equal to right",
    category="comparisons",
    tags=("condition", "comparison", "order", "is_lower_or_equal"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left <= right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_lower_or_equal_spec)
def is_lower_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left operand is lower than or equal to right operand."""
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
        return _log_comparison("is_lower_or_equal", False)
    res = val1 <= val2
    return _log_comparison("is_lower_or_equal", res)


__all__ = ["is_lower_or_equal", "is_lower_or_equal_spec"]
