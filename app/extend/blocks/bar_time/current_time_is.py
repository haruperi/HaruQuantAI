"""Current Time Is condition strategy block.

Description:
    Evaluates whether current broker time matches target packed HHMM or
    (hour, minute) pair, matching StrategyQuant CurrentTimeIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentTimeIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare current broker time against target.
Python API Usage:
    from app.extend.blocks.bar_time.current_time_is import current_time_is
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import (
    HHMM_PACKED_SEC_THRESHOLD,
    _log_cond,
)
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
        res = current_hour(source) == hour_or_hhmm and current_minute(source) == minute
    else:
        ct = current_time(source)
        target = (
            hour_or_hhmm // 100
            if hour_or_hhmm >= HHMM_PACKED_SEC_THRESHOLD
            else hour_or_hhmm
        )
        res = (ct == target) if ct != -1 else False
    return _log_cond("current_time_is", hour_or_hhmm, res)
