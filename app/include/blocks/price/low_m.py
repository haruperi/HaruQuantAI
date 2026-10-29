"""Monthly Low price strategy block (LowM)."""

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

low_m_spec = BlockSpec(
    id="price.low_m",
    version="1.0.0",
    name="Monthly Low (LowM)",
    description="Returns Monthly Low price at specified historical monthly shift",
    category="price",
    tags=("price", "mtf", "monthly", "low"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical monthly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Monthly Low price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(low_m_spec)
def low_m(chart: Any, shift: int = 0) -> float:
    """Get Monthly Low price at historical monthly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical monthly bar offset (default 0).

    Returns:
        Monthly Low price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.monthly_low(shift)
    return resolve_chart_field(chart, "monthly_low", shift)


__all__ = ["low_m", "low_m_spec"]
