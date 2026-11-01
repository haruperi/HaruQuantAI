"""Is Greater Than strictly comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.comparisons._common import resolve_shift_value, round_value
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

DEFAULT_COMPARISON_PRECISION: int = 6

is_greater_spec = BlockSpec(
    id="condition.is_greater",
    version="1.0.0",
    name="Is Greater Than",
    description="Evaluates whether left operand is strictly greater than right",
    category="comparisons",
    tags=("condition", "comparison", "greater"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (value or series)"),
        InputPort("right", PortType.ANY, "Right operand (value or series)"),
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
    """Evaluate whether left operand is strictly greater than right operand.

    Args:
        left: Left operand (scalar, series, array, or callable).
        right: Right operand (scalar, series, array, or callable).
        shift: Historical bar offset.
        precision: Comparison rounding precision.
        shift1: Optional explicit bar offset for left operand.
        shift2: Optional explicit bar offset for right operand.
        round_digits: Optional override for rounding precision.

    Returns:
        True if left > right, False if either is NaN or invalid.
    """
    p = precision if round_digits is None else round_digits
    s1 = shift if shift1 is None else shift1
    s2 = shift if shift2 is None else shift2
    v1 = round_value(resolve_shift_value(left, s1), p)
    v2 = round_value(resolve_shift_value(right, s2), p)
    if math.isnan(v1) or math.isnan(v2):
        return False
    return v1 > v2


__all__ = ["DEFAULT_COMPARISON_PRECISION", "is_greater", "is_greater_spec"]
