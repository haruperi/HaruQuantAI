"""Minimum mathematical expression strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.functions._common import resolve_shift_value
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

minimum_spec = BlockSpec(
    id="function.minimum",
    version="1.0.0",
    name="Minimum",
    description="Determines the minimum of two numerical operands at specified shift",
    category="functions",
    tags=("math", "minimum", "min"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val1", PortType.ANY, "First operand (scalar, series, or callable)"),
        InputPort("val2", PortType.ANY, "Second operand (scalar, series, or callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Minimum value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(minimum_spec)
def minimum(val1: Any, val2: Any, shift: int = 0) -> float:
    """Calculate minimum of two operands.

    Args:
        val1: First operand.
        val2: Second operand.
        shift: Historical bar offset.

    Returns:
        Smaller value as float, or NaN.
    """
    v1 = resolve_shift_value(val1, shift)
    v2 = resolve_shift_value(val2, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = min(v1, v2)
    logger.debug("FR-SERVICES-FUNCTION-MATH: min(%s, %s) = %s", v1, v2, res)
    return res


__all__ = ["minimum", "minimum_spec"]
