"""Spread price difference strategy block.

Description:
    Computes difference between Ask and Bid prices (Ask - Bid) at specified
    historical shift in raw currency price units.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-SPREAD: Raw price spread evaluation.
Python API Usage:
    from app.extend.blocks.price.spread import Spread, spread
    diff = spread(chart, shift=0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

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
    description="Returns raw price spread (Ask - Bid) at specified shift",
    category="price",
    tags=("price", "quote", "spread"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.SUB,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or Chart container"),
        InputPort("shift", PortType.NUMBER, "Historical offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Spread value at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(spread_spec)
def spread(chart: Any, shift: int = 0) -> float:
    """Get raw Spread (Ask - Bid) at historical shift.

    Args:
        chart: QuotePrice or container providing ask/bid fields.
        shift: Historical offset (default 0).

    Returns:
        Spread as float, or NaN.
    """
    logger.debug("FR-PRICE-SPREAD: Spread(shift=%d)", shift)
    if isinstance(chart, QuotePrice):
        return chart.spread(shift)

    ask_val = resolve_chart_field(chart, "ask", shift)
    bid_val = resolve_chart_field(chart, "bid", shift)

    if math.isnan(ask_val) or math.isnan(bid_val):
        return float("nan")

    return ask_val - bid_val


# Direct donor class alias matching SQ.Blocks.Price.Spread
Spread = spread

__all__ = ["Spread", "spread", "spread_spec"]
