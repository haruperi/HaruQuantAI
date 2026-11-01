"""Exponential mathematical expression strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.functions._common import FLOAT_MAX_VALUE, resolve_shift_value
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

exponential_spec = BlockSpec(
    id="function.exponential",
    version="1.0.0",
    name="Exponential",
    description="Calculates the natural exponential (e^x) of an operand",
    category="functions",
    tags=("math", "exponential", "exp"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val", PortType.ANY, "Exponent operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "e^val"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(exponential_spec)
def exponential(val: Any, shift: int = 0) -> float:
    """Calculate natural exponential (e^x).

    Args:
        val: Numeric exponent.
        shift: Historical bar offset.

    Returns:
        e^val as float, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    try:
        res = math.exp(v)
    except OverflowError:
        res = FLOAT_MAX_VALUE
    logger.debug("FR-SERVICES-FUNCTION-MATH: exp(%s) = %s", v, res)
    return res


__all__ = ["exponential", "exponential_spec"]
