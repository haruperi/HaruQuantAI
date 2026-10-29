"""Daily High price strategy block (HighD)."""

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
from app.include.blocks.price._common import MTFPrice, resolve_chart_field

logger = get_logger(__name__)

high_d_spec = BlockSpec(
    id="price.high_d",
    version="1.0.0",
    name="Daily High (HighD)",
    description="Returns Daily High price at specified historical daily shift",
    category="price",
    tags=("price", "mtf", "daily", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical daily bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Daily High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(high_d_spec)
def high_d(chart: Any, shift: int = 0) -> float:
    """Get Daily High price at historical daily shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical daily bar offset (default 0).

    Returns:
        Daily High price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.daily_high(shift)
    return resolve_chart_field(chart, "daily_high", shift)


__all__ = ["high_d", "high_d_spec"]
