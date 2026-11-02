"""Current Day Of Week temporal value strategy block.

Description:
    Retrieves current active broker day of week (Sunday=0 .. Saturday=6),
    matching StrategyQuant CurrentDayOfWeek snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentDayOfWeek block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current day of week (0-6).
Python API Usage:
    from app.extend.blocks.bar_time.current_day_of_week import current_day_of_week
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import (
    DateTime,
    _log_val,
    resolve_current_time_ms,
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

current_day_of_week_spec = BlockSpec(
    id="bar_time.current_day_of_week",
    version="1.0.0",
    name="Current Day Of Week",
    description="Retrieve current day of week (0=Sunday ... 6=Saturday)",
    category="bar_time",
    tags=("time", "day_of_week", "clock"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
    ),
    outputs=(OutputPort("day_of_week", PortType.NUMBER, "Day of week (0-6)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_day_of_week_spec)
def current_day_of_week(source: Any = None) -> int:
    """Retrieve current day of week (0=Sunday ... 6=Saturday)."""
    if hasattr(source, "current_day_of_week") and callable(source.current_day_of_week):
        return int(source.current_day_of_week())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_day_of_week_original(ms)
    return _log_val("current_day_of_week", 0, res)
