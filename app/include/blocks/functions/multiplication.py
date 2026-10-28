"""Multiplication mathematical expression strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.functions._common import resolve_shift_value
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

multiplication_spec = BlockSpec(
    id="function.multiplication",
    version="1.0.0",
    name="Multiplication",
    description="Multiplies two numerical operands at specified historical shift",
    category="functions",
    tags=("math", "arithmetic", "multiplication", "multiply"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "First factor (scalar, series, or callable)"),
        InputPort("right", PortType.ANY, "Second factor (scalar, series, or callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Product"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(multiplication_spec)
def multiplication(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate multiplication of two operands at historical bar shift.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.

    Returns:
        Product as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 * v2
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: mult(shift=%d) %s * %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


__all__ = ["multiplication", "multiplication_spec"]
