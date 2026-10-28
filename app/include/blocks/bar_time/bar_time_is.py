"""Bar Time Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.include.blocks.bar_time._common import (
    HHMM_PACKED_SEC_THRESHOLD,
    _log_cond,
)
from app.include.blocks.bar_time.bar_hour import bar_hour
from app.include.blocks.bar_time.bar_minute import bar_minute
from app.include.blocks.bar_time.bar_time import bar_time
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_time_is_spec = BlockSpec(
    id="condition.bar_time_is",
    version="1.0.0",
    name="Bar Time Is",
    description="Evaluate whether bar time matches packed HHMM or (hour, minute)",
    category="bar_time",
    tags=("condition", "clock", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("hour_or_hhmm", PortType.NUMBER, "Hour (0-23) or packed HHMM"),
        InputPort(
            "minute",
            PortType.NUMBER,
            "Optional minute (0-59)",
            default=None,
        ),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if bar time matches"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_time_is_spec)
def bar_time_is(
    source: Any,
    hour_or_hhmm: int,
    minute: int | None = None,
    shift: int = 0,
) -> bool:
    """Evaluate whether bar time matches packed HHMM or (hour, minute)."""
    if hasattr(source, "bar_time_is") and callable(source.bar_time_is):
        return bool(source.bar_time_is(hour_or_hhmm, minute=minute, shift=shift))
    if minute is not None:
        res = (
            bar_hour(source, shift) == hour_or_hhmm
            and bar_minute(source, shift) == minute
        )
    else:
        bt = bar_time(source, shift)
        target = (
            hour_or_hhmm // 100
            if hour_or_hhmm >= HHMM_PACKED_SEC_THRESHOLD
            else hour_or_hhmm
        )
        res = bt != -1 and bt == target
    return _log_cond("bar_time_is", hour_or_hhmm, res)
