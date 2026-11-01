"""First Week Of Month condition strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.bar_week_of_month import bar_week_of_month
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

first_week_of_month_spec = BlockSpec(
    id="condition.first_week_of_month",
    version="1.0.0",
    name="First Week Of Month",
    description="Evaluate whether bar falls within first Monday-aligned week of month",
    category="bar_time",
    tags=("condition", "week_of_month", "calendar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if in first week"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(first_week_of_month_spec)
def first_week_of_month(source: Any, shift: int = 0) -> bool:
    """Evaluate whether bar falls within first Monday-aligned week of month."""
    if hasattr(source, "first_week_of_month") and callable(source.first_week_of_month):
        return bool(source.first_week_of_month(shift))
    return _log_cond(
        "first_week_of_month", shift, bar_week_of_month(source, shift) == 1
    )
