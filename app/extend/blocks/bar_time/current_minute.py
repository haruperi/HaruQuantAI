"""Current Minute temporal value strategy block."""

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

current_minute_spec = BlockSpec(
    id="bar_time.current_minute",
    version="1.0.0",
    name="Current Minute",
    description="Retrieve current minute (0-59)",
    category="bar_time",
    tags=("time", "minute", "clock"),
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
    outputs=(OutputPort("minute", PortType.NUMBER, "Current minute (0-59)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_minute_spec)
def current_minute(source: Any = None) -> int:
    """Retrieve current minute (0-59)."""
    if hasattr(source, "current_minute") and callable(source.current_minute):
        return int(source.current_minute())
    ms = resolve_current_time_ms(source)
    return DateTime.get_minute(ms)
