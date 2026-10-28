"""Round to decimals mathematical expression strategy block."""

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

round_to_decimals_spec = BlockSpec(
    id="function.round_to_decimals",
    version="1.0.0",
    name="Round to Decimals",
    description="Rounds numerical operand to specified decimal places",
    category="functions",
    tags=("math", "round", "precision"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("val", PortType.ANY, "Value to round (scalar, series, or callable)"),
        InputPort("decimals", PortType.NUMBER, "Decimal places", default=5),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Rounded value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(round_to_decimals_spec)
def round_to_decimals(val: Any, decimals: int = 5, shift: int = 0) -> float:
    """Round operand to specified decimal places.

    Args:
        val: Numeric operand.
        decimals: Number of decimal places (default 5).
        shift: Historical bar offset.

    Returns:
        Rounded float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    res = round(v, decimals)
    logger.debug(
        "FR-SERVICES-FUNCTION-MATH: round_to_decimals(%s, dec=%d) = %s",
        v,
        decimals,
        res,
    )
    return res


__all__ = ["round_to_decimals", "round_to_decimals_spec"]
