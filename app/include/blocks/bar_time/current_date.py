"""Current Date temporal value strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import DateTime, resolve_current_time_ms
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_date_spec = BlockSpec(
    id="bar_time.current_date",
    version="1.0.0",
    name="Current Date",
    description="Retrieve current date as YYYYMMDD integer",
    category="bar_time",
    tags=("time", "date", "clock"),
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
    outputs=(OutputPort("date", PortType.NUMBER, "Current date as YYYYMMDD"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_date_spec)
def current_date(source: Any = None) -> int:
    """Retrieve current date as YYYYMMDD integer."""
    if hasattr(source, "current_date") and callable(source.current_date):
        return int(source.current_date())
    ms = resolve_current_time_ms(source)
    return DateTime.get_ymd(ms)
