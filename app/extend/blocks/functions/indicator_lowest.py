"""Indicator lowest ranking expression strategy block."""

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

indicator_lowest_spec = BlockSpec(
    id="function.indicator_lowest",
    version="1.0.0",
    name="Indicator Lowest",
    description="Extracts Nth lowest indicator value in a rolling window",
    category="functions",
    tags=("ranking", "rolling", "lowest", "indicator"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.ANY, "Indicator series or callable"),
        InputPort("period", PortType.NUMBER, "Lookback period (minimum 2)", default=5),
        InputPort("nth_value", PortType.NUMBER, "0-indexed rank (0=lowest)", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Nth lowest value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(indicator_lowest_spec)
def indicator_lowest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth lowest indicator value in a rolling window.

    NthValue=0 means lowest, 1 means second lowest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth lowest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        logger.debug(
            "FR-SERVICES-FUNCTION-RANK: indicator_lowest invalid "
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

    vals.sort()
    res = vals[nth_value]
    logger.debug(
        "FR-SERVICES-FUNCTION-RANK: indicator_lowest(period=%d, nth=%d, shift=%d) = %s",
        period,
        nth_value,
        shift,
        res,
    )
    return res


__all__ = ["indicator_lowest", "indicator_lowest_spec"]
