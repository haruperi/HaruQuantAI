"""Bar Close price strategy block."""

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

close_spec = BlockSpec(
    id="price.close",
    version="1.0.0",
    name="Close",
    description="Returns bar Close price at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "close"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Close price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(close_spec)
def bar_close(chart: Any, shift: int = 0) -> float:
    """Get bar Close price at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        Close price as float, or NaN.
    """
    return resolve_chart_field(chart, "close", shift)


close_price = bar_close

__all__ = ["bar_close", "close_price", "close_spec"]
