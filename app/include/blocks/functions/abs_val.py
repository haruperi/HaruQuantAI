"""Absolute value mathematical expression strategy block."""

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

abs_val_spec = BlockSpec(
    id="function.abs_val",
    version="1.0.0",
    name="Absolute Value",
    description="Calculates absolute value of numerical operand at specified shift",
    category="functions",
    tags=("math", "arithmetic", "abs", "absolute"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "val", PortType.ANY, "Numerical operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Absolute value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(abs_val_spec)
def abs_val(val: Any, shift: int = 0) -> float:
    """Calculate absolute value for numeric operand.

    Args:
        val: Numeric operand.
        shift: Historical bar offset.

    Returns:
        Absolute float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    res = abs(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: abs_val(%s) = %s", v, res)
    return res


__all__ = ["abs_val", "abs_val_spec"]
