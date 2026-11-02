"""Bar Day Of Month temporal value strategy block.

Description:
    Extracts day of month (1-31) of bar at specified historical shift,
    matching StrategyQuant BarDayOfMonth snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarDayOfMonth block.
Key Capabilities:
    - FR-bar-time-value: Extract bar day of month (1-31).
Python API Usage:
    from app.extend.blocks.bar_time.bar_day_of_month import bar_day_of_month
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
from app.extend.blocks.bar_time._common import DateTime, _log_val, resolve_time_ms

bar_day_of_month_spec = BlockSpec(
    id="bar_time.bar_day_of_month",
    version="1.0.0",
    name="Bar Day Of Month",
    description="Extract day of month (1-31) of bar at shift",
    category="bar_time",
    tags=("time", "day_of_month", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("day_of_month", PortType.NUMBER, "Day of month (1-31)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_day_of_month_spec)
def bar_day_of_month(source: Any, shift: int = 0) -> int:
    """Extract day of month (1-31) of bar at shift."""
    if hasattr(source, "bar_day_of_month") and callable(source.bar_day_of_month):
        return int(source.bar_day_of_month(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_day(ms) if ms != -1 else -1
    return _log_val("bar_day_of_month", shift, res)
