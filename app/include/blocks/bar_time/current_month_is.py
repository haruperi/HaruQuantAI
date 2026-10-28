"""Current Month Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time.current_month import current_month
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_month_is_spec = BlockSpec(
    id="condition.current_month_is",
    version="1.0.0",
    name="Current Month Is",
    description="Evaluate whether current month equals target month (1-12)",
    category="bar_time",
    tags=("condition", "month", "clock"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("month", PortType.NUMBER, "Target month (1-12)", default=1),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if current month matches",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_month_is_spec)
def current_month_is(source: Any = None, month: int = 1) -> bool:
    """Evaluate whether current month equals target month (1-12)."""
    if hasattr(source, "current_month_is") and callable(source.current_month_is):
        return bool(source.current_month_is(month))
    return current_month(source) == month
