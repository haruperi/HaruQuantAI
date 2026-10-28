"""Weekly Low price strategy block (LowW)."""

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
from app.include.blocks.price._common import MTFPrice, resolve_chart_field

logger = get_logger(__name__)

low_w_spec = BlockSpec(
    id="price.low_w",
    version="1.0.0",
    name="Weekly Low (LowW)",
    description="Returns Weekly Low price at specified historical weekly shift",
    category="price",
    tags=("price", "mtf", "weekly", "low"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical weekly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Weekly Low price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(low_w_spec)
def low_w(chart: Any, shift: int = 0) -> float:
    """Get Weekly Low price at historical weekly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical weekly bar offset (default 0).

    Returns:
        Weekly Low price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.weekly_low(shift)
    return resolve_chart_field(chart, "weekly_low", shift)


__all__ = ["low_w", "low_w_spec"]
