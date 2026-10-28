"""Bar Day Of Week Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import DateTime, _log_cond
from app.include.blocks.bar_time.bar_day_of_week import bar_day_of_week
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_day_of_week_is_spec = BlockSpec(
    id="condition.bar_day_of_week_is",
    version="1.0.0",
    name="Bar Day Of Week Is",
    description="Evaluate whether bar day of week equals target (0=Sun..6=Sat; 7=Sun)",
    category="bar_time",
    tags=("condition", "day_of_week", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("day", PortType.NUMBER, "Target day of week (0=Sun..6=Sat; 7=Sun)"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if day matches target"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_day_of_week_is_spec)
def bar_day_of_week_is(source: Any, day: int, shift: int = 0) -> bool:
    """Evaluate whether bar day of week equals target (0=Sun..6=Sat; 7=Sun)."""
    if hasattr(source, "bar_day_of_week_is") and callable(source.bar_day_of_week_is):
        return bool(source.bar_day_of_week_is(day, shift))
    target = 0 if day == DateTime.SUNDAY else day
    dow = bar_day_of_week(source, shift)
    return _log_cond("bar_day_of_week_is", day, dow == target if dow != -1 else False)
