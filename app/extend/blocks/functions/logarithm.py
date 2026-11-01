"""Natural logarithm mathematical expression strategy block."""

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

logarithm_spec = BlockSpec(
    id="function.logarithm",
    version="1.0.0",
    name="Logarithm",
    description="Calculates the natural logarithm ln(x) of a positive operand",
    category="functions",
    tags=("math", "logarithm", "log", "ln"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val", PortType.ANY, "Numerical operand (> 0) (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "ln(val)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(logarithm_spec)
def logarithm(val: Any, shift: int = 0) -> float:
    """Calculate natural logarithm ln(x).

    Args:
        val: Numeric operand (> 0).
        shift: Historical bar offset.

    Returns:
        ln(val) as float, or NaN if val <= 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v <= 0.0:
        return float("nan")
    res = math.log(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: log(%s) = %s", v, res)
    return res


__all__ = ["logarithm", "logarithm_spec"]
