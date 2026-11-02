"""Bid price strategy block.

Description:
    Returns the current or historical Bid quote price for the specified symbol
    or chart container.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-BID: Historical Bid quote price retrieval.
Python API Usage:
    from app.extend.blocks.price.bid import Bid, bid
    val = bid(chart, shift=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.price._common import resolve_chart_field

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
        InputPort("chart", PortType.ANY, "Chart or QuotePrice container"),
        InputPort("shift", PortType.NUMBER, "Historical offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Bid price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bid_spec)
def bid(chart: Any, shift: int = 0) -> float:
    """Get Bid price at historical shift.

    Args:
        chart: QuotePrice, BarPrice, series, or array.
        shift: Historical offset (default 0).

    Returns:
        Bid price as float, or NaN.
    """
    logger.debug("FR-PRICE-BID: Bid(shift=%d)", shift)
    return resolve_chart_field(chart, "bid", shift)


# Direct donor class alias matching SQ.Blocks.Price.Bid
Bid = bid

__all__ = ["Bid", "bid", "bid_spec"]
