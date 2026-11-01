"""Bid/Ask spread strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.price._common import QuotePrice, resolve_chart_field

logger = get_logger(__name__)

spread_spec = BlockSpec(
    id="price.spread",
    version="1.0.0",
    name="Spread",
    description="Returns raw Bid/Ask spread in points at specified historical shift",
    category="price",
    tags=("price", "quote", "spread"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical quote offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Spread in points"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(spread_spec)
def spread(chart: Any, shift: int = 0) -> float:
    """Get raw Bid/Ask spread (Ask - Bid in points) at historical shift.

    Args:
        chart: QuotePrice or container.
        shift: Historical quote offset (default 0).

    Returns:
        Spread in points as float, or NaN.
    """
    if isinstance(chart, QuotePrice):
        return chart.spread(shift)

    ask_val = resolve_chart_field(chart, "ask", shift)
    bid_val = resolve_chart_field(chart, "bid", shift)
    if math.isnan(ask_val) or math.isnan(bid_val):
        return float("nan")
    return float(abs(ask_val - bid_val))


__all__ = ["spread", "spread_spec"]
