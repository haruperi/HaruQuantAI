"""Current Week Of Month temporal value strategy block."""

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

current_week_of_month_spec = BlockSpec(
    id="bar_time.current_week_of_month",
    version="1.0.0",
    name="Current Week Of Month",
    description="Retrieve current Monday-aligned week of month (1-6)",
    category="bar_time",
    tags=("time", "week_of_month", "clock"),
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
    outputs=(
        OutputPort(
            "week_of_month",
            PortType.NUMBER,
            "Current week of month (1-6)",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_week_of_month_spec)
def current_week_of_month(source: Any = None) -> int:
    """Retrieve current Monday-aligned week of month (1-6)."""
    if hasattr(source, "current_week_of_month") and callable(
        source.current_week_of_month
    ):
        return int(source.current_week_of_month())
    ms = resolve_current_time_ms(source)
    return DateTime.get_week_of_month(ms)
