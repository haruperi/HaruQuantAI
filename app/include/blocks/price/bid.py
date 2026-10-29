"""Bid price strategy block."""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.price._common import resolve_chart_field

logger = get_logger(__name__)

bid_spec = BlockSpec(
    id="price.bid",
    version="1.0.0",
    name="Bid",
    description="Returns Bid price at specified historical shift",
    category="price",
    tags=("price", "quote", "bid"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical quote offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Bid price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bid_spec)
def bid(chart: Any, shift: int = 0) -> float:
    """Get Bid price at historical shift.

    Args:
        chart: QuotePrice, symbol proxy, or container.
        shift: Historical quote offset (default 0).

    Returns:
        Bid price as float, or NaN.
    """
    return resolve_chart_field(chart, "bid", shift)


__all__ = ["bid", "bid_spec"]
