"""Monthly Open price strategy block (OpenM)."""

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

open_m_spec = BlockSpec(
    id="price.open_m",
    version="1.0.0",
    name="Monthly Open (OpenM)",
    description="Returns Monthly Open price at specified historical monthly shift",
    category="price",
    tags=("price", "mtf", "monthly", "open"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("chart", PortType.ANY, "MTFPrice or chart container"),
        InputPort("shift", PortType.NUMBER, "Historical monthly bar offset", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Monthly Open price"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(open_m_spec)
def open_m(chart: Any, shift: int = 0) -> float:
    """Get Monthly Open price at historical monthly shift.

    Args:
        chart: MTFPrice or chart container.
        shift: Historical monthly bar offset (default 0).

    Returns:
        Monthly Open price as float, or NaN.
    """
    if isinstance(chart, MTFPrice):
        return chart.monthly_open(shift)
    return resolve_chart_field(chart, "monthly_open", shift)


__all__ = ["open_m", "open_m_spec"]
