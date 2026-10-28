"""Is Greater Than strictly comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import resolve_shift_value, round_value

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
def is_greater(left: Any, right: Any, shift: int = 0) -> bool:
    """Evaluate whether left operand is strictly greater than right operand.

    Args:
        left: Left operand (scalar, series, array, or callable).
        right: Right operand (scalar, series, array, or callable).
        shift: Historical bar offset.

    Returns:
        True if left > right, False if either is NaN or invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return False
    return round_value(v1) > round_value(v2)


__all__ = ["is_greater", "is_greater_spec"]
