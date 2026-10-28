"""Equals comparative condition strategy block."""

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

equals_spec = BlockSpec(
    id="condition.equals",
    version="1.0.0",
    name="Equals",
    description=(
        "Evaluates whether left value equals right value within rounding precision"
    ),
    category="comparisons",
    tags=("condition", "comparison", "equals"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (value or series)"),
        InputPort("right", PortType.ANY, "Right operand (value or series)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left == right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(equals_spec)
def equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value equals right value within rounding precision."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 == val2


__all__ = ["equals", "equals_spec"]
