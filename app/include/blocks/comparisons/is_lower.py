"""Is Lower Than strictly comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.include.blocks.base import block
from app.include.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    _pair,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

is_lower_spec = BlockSpec(
    id="condition.is_lower",
    version="1.0.0",
    name="Is Lower Than",
    description="Evaluates whether left operand is strictly lower than right",
    category="comparisons",
    tags=("condition", "comparison", "lower"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (value or series)"),
        InputPort("right", PortType.ANY, "Right operand (value or series)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left < right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_lower_spec)
def is_lower(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value is strictly lower than right value."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 < val2


__all__ = ["is_lower", "is_lower_spec"]
