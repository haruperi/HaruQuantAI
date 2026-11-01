"""Division mathematical expression strategy block."""

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

division_spec = BlockSpec(
    id="function.division",
    version="1.0.0",
    name="Division",
    description="Divides dividend by divisor at specified historical shift",
    category="functions",
    tags=("math", "arithmetic", "division", "divide"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "left", PortType.ANY, "Dividend operand (scalar, series, or callable)"
        ),
        InputPort(
            "right", PortType.ANY, "Divisor operand (scalar, series, or callable)"
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Quotient"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(division_spec)
def division(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate division of two operands.

    When the divisor is 0, returns safe FLOAT_MAX_VALUE (Double.MAX_VALUE parity).

    Args:
        left: Dividend operand.
        right: Divisor operand.
        shift: Historical bar offset.

    Returns:
        Quotient as float, FLOAT_MAX_VALUE on division by zero, or NaN on invalid input.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 / v2 if v2 != 0.0 else FLOAT_MAX_VALUE
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: div(shift=%d) %s / %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


__all__ = ["division", "division_spec"]
