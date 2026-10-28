"""Current Hour Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time.current_hour import current_hour
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_hour_is_spec = BlockSpec(
    id="condition.current_hour_is",
    version="1.0.0",
    name="Current Hour Is",
    description="Evaluate whether current hour equals target hour (0-23)",
    category="bar_time",
    tags=("condition", "hour", "clock"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("hour", PortType.NUMBER, "Target hour (0-23)", default=0),
    ),
    outputs=(
        OutputPort("condition", PortType.BOOLEAN, "True if current hour matches"),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_hour_is_spec)
def current_hour_is(source: Any = None, hour: int = 0) -> bool:
    """Evaluate whether current hour equals target hour (0-23)."""
    if hasattr(source, "current_hour_is") and callable(source.current_hour_is):
        return bool(source.current_hour_is(hour))
    return current_hour(source) == hour
