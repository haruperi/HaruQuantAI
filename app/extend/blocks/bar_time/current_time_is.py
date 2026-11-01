"""Current Time Is condition strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import HHMM_PACKED_SEC_THRESHOLD
from app.extend.blocks.bar_time.current_hour import current_hour
from app.extend.blocks.bar_time.current_minute import current_minute
from app.extend.blocks.bar_time.current_time import current_time
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_time_is_spec = BlockSpec(
    id="condition.current_time_is",
    version="1.0.0",
    name="Current Time Is",
    description="Evaluate whether current time matches packed HHMM or (hour, minute)",
    category="bar_time",
    tags=("condition", "clock"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort(
            "hour_or_hhmm",
            PortType.NUMBER,
            "Hour (0-23) or packed HHMM",
            default=0,
        ),
        InputPort(
            "minute",
            PortType.NUMBER,
            "Optional minute (0-59)",
            default=None,
        ),
    ),
    outputs=(
        OutputPort("condition", PortType.BOOLEAN, "True if current time matches"),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_time_is_spec)
def current_time_is(
    source: Any = None,
    hour_or_hhmm: int = 0,
    minute: int | None = None,
) -> bool:
    """Evaluate whether current time matches packed HHMM or (hour, minute)."""
    if hasattr(source, "current_time_is") and callable(source.current_time_is):
        return bool(source.current_time_is(hour_or_hhmm, minute=minute))
    if minute is not None:
        return current_hour(source) == hour_or_hhmm and current_minute(source) == minute
    ct = current_time(source)
    target = (
        hour_or_hhmm // 100
        if hour_or_hhmm >= HHMM_PACKED_SEC_THRESHOLD
        else hour_or_hhmm
    )
    return ct != -1 and ct == target
