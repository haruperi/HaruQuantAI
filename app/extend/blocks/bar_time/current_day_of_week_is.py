"""Current Day Of Week Is condition strategy block.

Description:
    Evaluates whether current broker day of week equals target day,
    matching StrategyQuant CurrentDayOfWeekIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentDayOfWeekIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare current day of week against target.
Python API Usage:
    from app.extend.blocks.bar_time.current_day_of_week_is import (
        current_day_of_week_is,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import DateTime, _log_cond
from app.extend.blocks.bar_time.current_day_of_week import current_day_of_week
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_day_of_week_is_spec = BlockSpec(
    id="condition.current_day_of_week_is",
    version="1.0.0",
    name="Current Day Of Week Is",
    description="Evaluate whether current day of week matches target (0=Sun..6=Sat)",
    category="bar_time",
    tags=("condition", "day_of_week"),
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
            "day",
            PortType.NUMBER,
            "Target day of week (0=Sun..6=Sat; 7=Sun)",
            default=0,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if current day matches"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_day_of_week_is_spec)
def current_day_of_week_is(source: Any = None, day: int = 0) -> bool:
    """Evaluate whether current day of week matches target (0=Sun..6=Sat)."""
    if hasattr(source, "current_day_of_week_is") and callable(
        source.current_day_of_week_is
    ):
        return bool(source.current_day_of_week_is(day))
    target = 0 if day == DateTime.SUNDAY else day
    dow = current_day_of_week(source)
    res = (dow == target) if dow != -1 else False
    return _log_cond("current_day_of_week_is", day, res)
