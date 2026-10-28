"""Bar Day Of Week temporal value strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import DateTime, resolve_time_ms
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_day_of_week_spec = BlockSpec(
    id="bar_time.bar_day_of_week",
    version="1.0.0",
    name="Bar Day Of Week",
    description="Extract day of week (0=Sunday ... 6=Saturday) of bar at shift",
    category="bar_time",
    tags=("time", "day_of_week", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("day_of_week", PortType.NUMBER, "Day of week (0-6)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_day_of_week_spec)
def bar_day_of_week(source: Any, shift: int = 0) -> int:
    """Extract day of week (0=Sunday ... 6=Saturday) of bar at shift."""
    if hasattr(source, "bar_day_of_week") and callable(source.bar_day_of_week):
        return int(source.bar_day_of_week(shift))
    ms = resolve_time_ms(source, shift)
    return DateTime.get_day_of_week_original(ms) if ms != -1 else -1
