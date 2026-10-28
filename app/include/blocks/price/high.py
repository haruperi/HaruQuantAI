"""Bar High price strategy block."""

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

high_spec = BlockSpec(
    id="price.high",
    version="1.0.0",
    name="High",
    description="Returns bar High price at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "High price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(high_spec)
def bar_high(chart: Any, shift: int = 0) -> float:
    """Get bar High price at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        High price as float, or NaN.
    """
    return resolve_chart_field(chart, "high", shift)


high_price = bar_high

__all__ = ["bar_high", "high_price", "high_spec"]
