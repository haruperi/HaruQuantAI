"""Bar Minute temporal value strategy block."""

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

bar_minute_spec = BlockSpec(
    id="bar_time.bar_minute",
    version="1.0.0",
    name="Bar Minute",
    description="Extract minute of bar (0-59) at shift",
    category="bar_time",
    tags=("time", "minute", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("minute", PortType.NUMBER, "Minute of bar (0-59)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_minute_spec)
def bar_minute(source: Any, shift: int = 0) -> int:
    """Extract minute of bar (0-59) at shift."""
    if hasattr(source, "bar_minute") and callable(source.bar_minute):
        return int(source.bar_minute(shift))
    ms = resolve_time_ms(source, shift)
    return DateTime.get_minute(ms) if ms != -1 else -1
