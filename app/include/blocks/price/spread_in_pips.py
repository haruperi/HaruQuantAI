"""Bid/Ask spread in pips strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.price._common import (
    DEFAULT_PIP_SIZE,
    QuotePrice,
    resolve_chart_field,
)

logger = get_logger(__name__)

spread_in_pips_spec = BlockSpec(
    id="price.spread_in_pips",
    version="1.0.0",
    name="Spread in Pips",
    description="Returns Bid/Ask spread converted to pips at historical shift",
    category="price",
    tags=("price", "quote", "spread", "pips"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical quote offset", default=0),
        InputPort("pip_size", PortType.NUMBER, "Pip size override", default=None),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Spread in pips"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(spread_in_pips_spec)
def spread_in_pips(
    chart: Any,
    shift: int = 0,
    pip_size: float | None = None,
) -> float:
    """Get spread converted to pips at historical shift.

    Args:
        chart: QuotePrice or container.
        shift: Historical quote offset (default 0).
        pip_size: Explicit pip size override (optional).

    Returns:
        Spread in pips as float, or NaN.
    """
    if isinstance(chart, QuotePrice):
        return chart.spread_in_pips(shift, pip_size=pip_size)

    ask_val = resolve_chart_field(chart, "ask", shift)
    bid_val = resolve_chart_field(chart, "bid", shift)
    if math.isnan(ask_val) or math.isnan(bid_val):
        return float("nan")

    eff_pip = (
        pip_size
        if pip_size is not None and pip_size > 0.0
        else getattr(chart, "pip_size", DEFAULT_PIP_SIZE)
    )
    if eff_pip <= 0.0:
        return float("nan")
    return float(abs(ask_val - bid_val) / eff_pip)


__all__ = ["spread_in_pips", "spread_in_pips_spec"]
