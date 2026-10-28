"""Bar Month Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import _log_cond
from app.include.blocks.bar_time.bar_month import bar_month
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_month_is_spec = BlockSpec(
    id="condition.bar_month_is",
    version="1.0.0",
    name="Bar Month Is",
    description="Evaluate whether bar month equals target month (1-12)",
    category="bar_time",
    tags=("condition", "month", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("month", PortType.NUMBER, "Target month (1-12)"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if month matches"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_month_is_spec)
def bar_month_is(source: Any, month: int, shift: int = 0) -> bool:
    """Evaluate whether bar month equals target month (1-12)."""
    if hasattr(source, "bar_month_is") and callable(source.bar_month_is):
        return bool(source.bar_month_is(month, shift))
    m = bar_month(source, shift)
    return _log_cond("bar_month_is", month, m == month if m != -1 else False)
