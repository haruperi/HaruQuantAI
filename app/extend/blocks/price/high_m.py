"""Monthly High price strategy block (HighM)."""

from __future__ import annotations

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
from app.extend.blocks.price._common import MTFPrice, resolve_chart_field

logger = get_logger(__name__)

high_m_spec = BlockSpec(
    id="price.high_m",
    version="1.0.0",
    name="Monthly High (HighM)",
    description="Returns Monthly High price at specified historical monthly shift",
    category="price",
    tags=("price", "mtf", "monthly", "high"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical monthly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Monthly High price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(high_m_spec)
def high_m(chart: Any, shift: int = 0) -> float:
    """Get Monthly High price at historical monthly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical monthly bar offset (default 0).

    Returns:
        Monthly High price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.monthly_high(shift)
    return resolve_chart_field(chart, "monthly_high", shift)


__all__ = ["high_m", "high_m_spec"]
