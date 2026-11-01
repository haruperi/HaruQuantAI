"""Indicator highest ranking expression strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.functions._common import (
    MIN_RANK_PERIOD,
    resolve_shift_value,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

indicator_highest_spec = BlockSpec(
    id="function.indicator_highest",
    version="1.0.0",
    name="Indicator Highest",
    description="Extracts Nth highest indicator value in a rolling window",
    category="functions",
    tags=("ranking", "rolling", "highest", "indicator"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.ANY, "Indicator series or callable"),
        InputPort("period", PortType.NUMBER, "Lookback period (minimum 2)", default=5),
        InputPort(
            "nth_value", PortType.NUMBER, "0-indexed rank (0=highest)", default=0
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Nth highest value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_highest_spec)
def indicator_highest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth highest indicator value in a rolling window.

    NthValue=0 means highest, 1 means second highest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth highest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        logger.debug(
            "FR-SERVICES-FUNCTION-RANK: indicator_highest invalid "
            "period=%d, nth=%d -> -1.0",
            period,
            nth_value,
        )
        return -1.0

    vals: list[float] = []
    for i in range(period):
        v = resolve_shift_value(indicator, shift + i)
        if math.isnan(v):
            return -1.0
        vals.append(v)

    vals.sort(reverse=True)
    res = vals[nth_value]
    logger.debug(
        "FR-SERVICES-FUNCTION-RANK: indicator_highest(period=%d, nth=%d, "
        "shift=%d) = %s",
        period,
        nth_value,
        shift,
        res,
    )
    return res


__all__ = ["indicator_highest", "indicator_highest_spec"]
