"""Current Day Of Week temporal value strategy block."""

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

current_day_of_week_spec = BlockSpec(
    id="bar_time.current_day_of_week",
    version="1.0.0",
    name="Current Day Of Week",
    description="Retrieve current day of week (0=Sunday ... 6=Saturday)",
    category="bar_time",
    tags=("time", "day_of_week", "clock"),
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
    outputs=(OutputPort("day_of_week", PortType.NUMBER, "Current day of week (0-6)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_day_of_week_spec)
def current_day_of_week(source: Any = None) -> int:
    """Retrieve current day of week (0=Sunday ... 6=Saturday)."""
    if hasattr(source, "current_day_of_week") and callable(source.current_day_of_week):
        return int(source.current_day_of_week())
    ms = resolve_current_time_ms(source)
    return DateTime.get_day_of_week_original(ms)
