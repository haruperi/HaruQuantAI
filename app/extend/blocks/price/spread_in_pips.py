"""Spread in pips strategy block.

Description:
    Computes difference between Ask and Bid prices scaled by instrument pip size
    ((Ask - Bid) / PipSize) at specified historical shift.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-SPREAD-IN-PIPS: Pip-normalized spread difference evaluation.
Python API Usage:
    from app.extend.blocks.price.spread_in_pips import (
        SpreadInPips,
        spread_in_pips,
    )
    pips = spread_in_pips(chart, shift=0, pip_size=0.0001)
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

import math
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
from app.extend.blocks.price._common import (
    DEFAULT_PIP_SIZE,
    QuotePrice,
    resolve_chart_field,
)

logger = get_logger(__name__)

spread_in_pips_spec = BlockSpec(
    id="price.spread_in_pips",
    version="1.0.0",
    name="Spread In Pips",
    description="Returns spread in pips ((Ask - Bid) / PipSize) at specified shift",
    category="price",
    tags=("price", "quote", "spread", "pips"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.SUB,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or Chart container"),
        InputPort(
            "pip_size",
            PortType.NUMBER,
            "Instrument pip size",
            default=DEFAULT_PIP_SIZE,
        ),
        InputPort("shift", PortType.NUMBER, "Historical offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Spread in pips at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(spread_in_pips_spec)
def spread_in_pips(
    chart: Any,
    shift: int = 0,
    pip_size: float = DEFAULT_PIP_SIZE,
) -> float:
    """Get Spread in pips ((Ask - Bid) / PipSize) at historical shift.

    Args:
        chart: QuotePrice or container providing ask/bid fields.
        shift: Historical offset (default 0).
        pip_size: Pip size multiplier (default 0.0001).

    Returns:
        Spread in pips as float, or NaN.
    """
    logger.debug(
        "FR-PRICE-SPREAD-IN-PIPS: SpreadInPips(shift=%d, pip=%.6f)",
        shift,
        pip_size,
    )
    if isinstance(chart, QuotePrice):
        return chart.spread_in_pips(shift)

    ask_val = resolve_chart_field(chart, "ask", shift)
    bid_val = resolve_chart_field(chart, "bid", shift)

    if math.isnan(ask_val) or math.isnan(bid_val) or pip_size <= 0.0:
        return float("nan")

    return (ask_val - bid_val) / pip_size


# Direct donor class alias matching SQ.Blocks.Price.SpreadInPips
SpreadInPips = spread_in_pips

__all__ = ["SpreadInPips", "spread_in_pips", "spread_in_pips_spec"]
