"""Bar Hour Is Smaller condition strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.bar_hour import bar_hour
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_hour_is_smaller_spec = BlockSpec(
    id="condition.bar_hour_is_smaller",
    version="1.0.0",
    name="Bar Hour Is Smaller",
    description="Evaluate whether bar hour is less than target hour",
    category="bar_time",
    tags=("condition", "hour", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("hour", PortType.NUMBER, "Target hour (0-23)"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if hour < target"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_hour_is_smaller_spec)
def bar_hour_is_smaller(source: Any, hour: int, shift: int = 0) -> bool:
    """Evaluate whether bar hour is less than target hour."""
    if hasattr(source, "bar_hour_is_smaller") and callable(source.bar_hour_is_smaller):
        return bool(source.bar_hour_is_smaller(hour, shift))
    h = bar_hour(source, shift)
    return _log_cond("bar_hour_is_smaller", hour, h < hour if h != -1 else False)
