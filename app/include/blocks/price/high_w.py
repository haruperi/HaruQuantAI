"""Weekly High price strategy block (HighW)."""

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

high_w_spec = BlockSpec(
    id="price.high_w",
    version="1.0.0",
    name="Weekly High (HighW)",
    description="Returns Weekly High price at specified historical weekly shift",
    category="price",
    tags=("price", "mtf", "weekly", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical weekly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Weekly High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(high_w_spec)
def high_w(chart: Any, shift: int = 0) -> float:
    """Get Weekly High price at historical weekly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical weekly bar offset (default 0).

    Returns:
        Weekly High price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.weekly_high(shift)
    return resolve_chart_field(chart, "weekly_high", shift)


__all__ = ["high_w", "high_w_spec"]
