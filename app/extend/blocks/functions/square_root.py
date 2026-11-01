"""Square root mathematical expression strategy block."""

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

square_root_spec = BlockSpec(
    id="function.square_root",
    version="1.0.0",
    name="Square Root",
    description="Calculates the square root of a non-negative operand",
    category="functions",
    tags=("math", "square_root", "sqrt"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val",
            PortType.ANY,
            "Numerical operand (>= 0) (scalar, series, or callable)",
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "sqrt(val)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(square_root_spec)
def square_root(val: Any, shift: int = 0) -> float:
    """Calculate square root of numeric operand.

    Args:
        val: Numeric operand (>= 0).
        shift: Historical bar offset.

    Returns:
        sqrt(val) as float, or NaN if val < 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v < 0.0:
        return float("nan")
    res = math.sqrt(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: sqrt(%s) = %s", v, res)
    return res


__all__ = ["square_root", "square_root_spec"]
