"""Current Day Of Week Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import DateTime
from app.include.blocks.bar_time.current_day_of_week import current_day_of_week
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_day_of_week_is_spec = BlockSpec(
    id="condition.current_day_of_week_is",
    version="1.0.0",
    name="Current Day Of Week Is",
    description="Evaluate whether current day of week equals target",
    category="bar_time",
    tags=("condition", "day_of_week", "clock"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("day", PortType.NUMBER, "Target day of week (0=Sun..6=Sat; 7=Sun)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if day matches target"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_day_of_week_is_spec)
def current_day_of_week_is(source: Any = None, day: int = 0) -> bool:
    """Evaluate whether current day of week equals target (0=Sun..6=Sat; 7=Sun)."""
    if hasattr(source, "current_day_of_week_is") and callable(
        source.current_day_of_week_is
    ):
        return bool(source.current_day_of_week_is(day))
    target = 0 if day == DateTime.SUNDAY else day
    return current_day_of_week(source) == target
