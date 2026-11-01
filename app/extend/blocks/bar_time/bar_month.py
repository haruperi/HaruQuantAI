"""Bar Month temporal value strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import DateTime, resolve_time_ms
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_month_spec = BlockSpec(
    id="bar_time.bar_month",
    version="1.0.0",
    name="Bar Month",
    description="Extract month of year (1-12) of bar at shift",
    category="bar_time",
    tags=("time", "month", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("month", PortType.NUMBER, "Month of year (1-12)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_month_spec)
def bar_month(source: Any, shift: int = 0) -> int:
    """Extract month of year (1-12) of bar at shift."""
    if hasattr(source, "bar_month") and callable(source.bar_month):
        return int(source.bar_month(shift))
    ms = resolve_time_ms(source, shift)
    return DateTime.get_month(ms) if ms != -1 else -1
