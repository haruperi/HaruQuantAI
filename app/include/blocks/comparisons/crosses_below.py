"""Crosses Below comparative crossover condition strategy block."""

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

crosses_below_spec = BlockSpec(
    id="condition.crosses_below",
    version="1.0.0",
    name="Crosses Below",
    description=(
        "Evaluates whether left operand crossed below right operand from shift+1"
        " to shift"
    ),
    category="comparisons",
    tags=("condition", "comparison", "crossover", "crosses_below"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if left crossed below right",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(crosses_below_spec)
def crosses_below(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left crossed below right between shift + 1 and shift."""
    val11, val21 = _pair(left, right, shift + 1, precision, rd=round_digits)
    val10, val20 = _pair(left, right, shift, precision, rd=round_digits)
    if any(math.isnan(v) for v in (val11, val21, val10, val20)):
        return False
    return val11 > val21 and val10 < val20


__all__ = ["crosses_below", "crosses_below_spec"]
