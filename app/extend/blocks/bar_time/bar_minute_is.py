"""Bar Minute Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.bar_minute import bar_minute
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_minute_is_spec = BlockSpec(
    id="condition.bar_minute_is",
    version="1.0.0",
    name="Bar Minute Is",
    description="Evaluate whether bar minute equals target minute",
    category="bar_time",
    tags=("condition", "minute", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("minute", PortType.NUMBER, "Target minute (0-59)"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if minute matches"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_minute_is_spec)
def bar_minute_is(source: Any, minute: int, shift: int = 0) -> bool:
    """Evaluate whether bar minute equals target minute."""
    if hasattr(source, "bar_minute_is") and callable(source.bar_minute_is):
        return bool(source.bar_minute_is(minute, shift))
    m = bar_minute(source, shift)
    return _log_cond("bar_minute_is", minute, m == minute if m != -1 else False)
