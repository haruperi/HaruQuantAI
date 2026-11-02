"""Current Date temporal value strategy block.

Description:
    Retrieves current active broker or system date as YYYYMMDD integer,
    matching StrategyQuant CurrentDate snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentDate block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current date in YYYYMMDD format.
Python API Usage:
    from app.extend.blocks.bar_time.current_date import current_date
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

current_date_spec = BlockSpec(
    id="bar_time.current_date",
    version="1.0.0",
    name="Current Date",
    description="Retrieve current date as YYYYMMDD integer",
    category="bar_time",
    tags=("time", "date", "clock"),
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
    outputs=(OutputPort("date", PortType.NUMBER, "Current date as YYYYMMDD"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_date_spec)
def current_date(source: Any = None) -> int:
    """Retrieve current date as YYYYMMDD integer."""
    if hasattr(source, "current_date") and callable(source.current_date):
        return int(source.current_date())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_ymd(ms)
    return _log_val("current_date", 0, res)
