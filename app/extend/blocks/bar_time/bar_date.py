"""Bar Date temporal value strategy block.

Description:
    Extracts date of bar at specified historical shift as YYYYMMDD integer,
    matching StrategyQuant BarDate snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarDate block.
Key Capabilities:
    - FR-bar-time-value: Extract bar date in YYYYMMDD format.
Python API Usage:
    from app.extend.blocks.bar_time.bar_date import bar_date
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

bar_date_spec = BlockSpec(
    id="bar_time.bar_date",
    version="1.0.0",
    name="Bar Date",
    description="Extract date of bar at shift as YYYYMMDD integer",
    category="bar_time",
    tags=("time", "date", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("date", PortType.NUMBER, "Date as YYYYMMDD integer"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_date_spec)
def bar_date(source: Any, shift: int = 0) -> int:
    """Extract date of bar at shift as YYYYMMDD integer."""
    if hasattr(source, "bar_date") and callable(source.bar_date):
        return int(source.bar_date(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_ymd(ms) if ms != -1 else -1
    return _log_val("bar_date", shift, res)
