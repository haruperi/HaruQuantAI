"""Last Week Of Month condition strategy block.

Description:
    Evaluates whether bar falls within the last Monday-aligned week of month,
    matching StrategyQuant LastWeekOfMonth snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful LastWeekOfMonth block.
Key Capabilities:
    - FR-bar-time-predicate: Test if bar week of month == last week of month.
Python API Usage:
    from app.extend.blocks.bar_time.last_week_of_month import last_week_of_month
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import (
    DateTime,
    _log_cond,
    resolve_time_ms,
)
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

last_week_of_month_spec = BlockSpec(
    id="condition.last_week_of_month",
    version="1.0.0",
    name="Last Week Of Month",
    description="Evaluate whether bar falls within last Monday-aligned week of month",
    category="bar_time",
    tags=("condition", "week_of_month", "calendar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if in last week"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(last_week_of_month_spec)
def last_week_of_month(source: Any, shift: int = 0) -> bool:
    """Evaluate whether bar falls within last Monday-aligned week of month."""
    if hasattr(source, "last_week_of_month") and callable(source.last_week_of_month):
        return bool(source.last_week_of_month(shift))
    ms = resolve_time_ms(source, shift)
    if ms == -1:
        return False
    last_ms = DateTime.set_day_of_month(ms, DateTime.get_days_in_month(ms))
    res = DateTime.get_week_of_month(ms) == DateTime.get_week_of_month(last_ms)
    return _log_cond("last_week_of_month", shift, res)
