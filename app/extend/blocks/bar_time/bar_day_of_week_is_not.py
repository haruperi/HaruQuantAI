"""Bar Day Of Week Is Not condition strategy block.

Description:
    Evaluates whether bar day of week does not match target day at shift,
    matching StrategyQuant BarDayOfWeekIsNot snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarDayOfWeekIsNot block.
Key Capabilities:
    - FR-bar-time-predicate: Compare bar day of week against non-target day.
Python API Usage:
    from app.extend.blocks.bar_time.bar_day_of_week_is_not import (
        bar_day_of_week_is_not,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.bar_time._common import DateTime, _log_cond
from app.extend.blocks.bar_time.bar_day_of_week import bar_day_of_week

bar_day_of_week_is_not_spec = BlockSpec(
    id="condition.bar_day_of_week_is_not",
    version="1.0.0",
    name="Bar Day Of Week Is Not",
    description="Evaluate whether bar day of week is not target (0=Sun..6=Sat; 7=Sun)",
    category="bar_time",
    tags=("condition", "day_of_week", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort(
            "day",
            PortType.NUMBER,
            "Non-target day of week (0=Sun..6=Sat; 7=Sun)",
            default=0,
        ),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if day does not match"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_day_of_week_is_not_spec)
def bar_day_of_week_is_not(source: Any, day: int = 0, shift: int = 0) -> bool:
    """Evaluate whether bar day of week is not target (0=Sun..6=Sat; 7=Sun)."""
    if hasattr(source, "bar_day_of_week_is_not") and callable(
        source.bar_day_of_week_is_not
    ):
        return bool(source.bar_day_of_week_is_not(day, shift))
    target = 0 if day == DateTime.SUNDAY else day
    dow = bar_day_of_week(source, shift)
    res = (dow != target) if dow != -1 else False
    return _log_cond("bar_day_of_week_is_not", day, res)
