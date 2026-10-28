"""Current Month temporal value strategy block."""

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

current_month_spec = BlockSpec(
    id="bar_time.current_month",
    version="1.0.0",
    name="Current Month",
    description="Retrieve current month (1-12)",
    category="bar_time",
    tags=("time", "month", "clock"),
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
    outputs=(OutputPort("month", PortType.NUMBER, "Current month (1-12)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_month_spec)
def current_month(source: Any = None) -> int:
    """Retrieve current month (1-12)."""
    if hasattr(source, "current_month") and callable(source.current_month):
        return int(source.current_month())
    ms = resolve_current_time_ms(source)
    return DateTime.get_month(ms)
