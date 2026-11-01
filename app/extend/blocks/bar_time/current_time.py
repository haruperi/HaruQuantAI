"""Current Time temporal value strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import DateTime, resolve_current_time_ms
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_time_spec = BlockSpec(
    id="bar_time.current_time",
    version="1.0.0",
    name="Current Time",
    description="Retrieve current time as packed HHMM integer",
    category="bar_time",
    tags=("time", "clock"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
    ),
    outputs=(OutputPort("time", PortType.NUMBER, "Current time as packed HHMM"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_time_spec)
def current_time(source: Any = None) -> int:
    """Retrieve current time as packed HHMM integer."""
    if hasattr(source, "current_time") and callable(source.current_time):
        return int(source.current_time())
    ms = resolve_current_time_ms(source)
    return DateTime.get_hhmm(ms)
