"""Bar Hour temporal value strategy block."""

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

bar_hour_spec = BlockSpec(
    id="bar_time.bar_hour",
    version="1.0.0",
    name="Bar Hour",
    description="Extract hour of bar (0-23) at shift",
    category="bar_time",
    tags=("time", "hour", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("hour", PortType.NUMBER, "Hour of bar (0-23)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_hour_spec)
def bar_hour(source: Any, shift: int = 0) -> int:
    """Extract hour of bar (0-23) at shift."""
    if hasattr(source, "bar_hour") and callable(source.bar_hour):
        return int(source.bar_hour(shift))
    ms = resolve_time_ms(source, shift)
    return DateTime.get_hour(ms) if ms != -1 else -1
