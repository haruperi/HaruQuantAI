"""Bar Open price strategy block."""

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

open_spec = BlockSpec(
    id="price.open",
    version="1.0.0",
    name="Open",
    description="Returns bar Open price at specified historical shift",
    category="price",
    tags=("price", "ohlcv", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "Chart data container or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Open price at shift"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_spec)
def bar_open(chart: Any, shift: int = 0) -> float:
    """Get bar Open price at historical shift.

    Args:
        chart: Chart data container, BarPrice, series, or array.
        shift: Historical bar offset (default 0).

    Returns:
        Open price as float, or NaN.
    """
    return resolve_chart_field(chart, "open", shift)


open_price = bar_open

__all__ = ["bar_open", "open_price", "open_spec"]
