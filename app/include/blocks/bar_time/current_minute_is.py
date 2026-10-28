"""Current Minute Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time.current_minute import current_minute
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_minute_is_spec = BlockSpec(
    id="condition.current_minute_is",
    version="1.0.0",
    name="Current Minute Is",
    description="Evaluate whether current minute equals target minute (0-59)",
    category="bar_time",
    tags=("condition", "minute", "clock"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("minute", PortType.NUMBER, "Target minute (0-59)", default=0),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if current minute matches",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_minute_is_spec)
def current_minute_is(source: Any = None, minute: int = 0) -> bool:
    """Evaluate whether current minute equals target minute (0-59)."""
    if hasattr(source, "current_minute_is") and callable(source.current_minute_is):
        return bool(source.current_minute_is(minute))
    return current_minute(source) == minute
