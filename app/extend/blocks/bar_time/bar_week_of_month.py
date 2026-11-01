"""Bar Week Of Month temporal value strategy block."""

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

bar_week_of_month_spec = BlockSpec(
    id="bar_time.bar_week_of_month",
    version="1.0.0",
    name="Bar Week Of Month",
    description="Extract Monday-aligned week of month (1-6) of bar at shift",
    category="bar_time",
    tags=("time", "week_of_month", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("week_of_month", PortType.NUMBER, "Week of month (1-6)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_week_of_month_spec)
def bar_week_of_month(source: Any, shift: int = 0) -> int:
    """Extract Monday-aligned week of month (1-6) of bar at shift."""
    if hasattr(source, "bar_week_of_month") and callable(source.bar_week_of_month):
        return int(source.bar_week_of_month(shift))
    ms = resolve_time_ms(source, shift)
    return DateTime.get_week_of_month(ms) if ms != -1 else -1
