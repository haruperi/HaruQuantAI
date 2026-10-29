"""Maximum mathematical expression strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
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

maximum_spec = BlockSpec(
    id="function.maximum",
    version="1.0.0",
    name="Maximum",
    description="Determines the maximum of two numerical operands at specified shift",
    category="functions",
    tags=("math", "maximum", "max"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val1", PortType.ANY, "First operand (scalar, series, or callable)"),
        InputPort("val2", PortType.ANY, "Second operand (scalar, series, or callable)"),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Maximum value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(maximum_spec)
def maximum(val1: Any, val2: Any, shift: int = 0) -> float:
    """Calculate maximum of two operands.

    Args:
        val1: First operand.
        val2: Second operand.
        shift: Historical bar offset.

    Returns:
        Larger value as float, or NaN.
    """
    v1 = resolve_shift_value(val1, shift)
    v2 = resolve_shift_value(val2, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = max(v1, v2)
    logger.debug("FR-SERVICES-FUNCTION-MATH: max(%s, %s) = %s", v1, v2, res)
    return res


__all__ = ["maximum", "maximum_spec"]
