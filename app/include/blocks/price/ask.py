"""Ask price strategy block."""

from __future__ import annotations

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
from app.include.blocks.price._common import resolve_chart_field

logger = get_logger(__name__)

ask_spec = BlockSpec(
    id="price.ask",
    version="1.0.0",
    name="Ask",
    description="Returns Ask price at specified historical shift",
    category="price",
    tags=("price", "quote", "ask"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "QuotePrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical quote offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Ask price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(ask_spec)
def ask(chart: Any, shift: int = 0) -> float:
    """Get Ask price at historical shift.

    Args:
        chart: QuotePrice, symbol proxy, or container.
        shift: Historical quote offset (default 0).

    Returns:
        Ask price as float, or NaN.
    """
    return resolve_chart_field(chart, "ask", shift)


__all__ = ["ask", "ask_spec"]
