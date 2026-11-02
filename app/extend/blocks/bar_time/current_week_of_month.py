"""Current Week Of Month temporal value strategy block.

Description:
    Retrieves current active broker Monday-aligned week of month (1-6),
    matching StrategyQuant CurrentWeekOfMonth snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentWeekOfMonth block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current week of month (1-6).
Python API Usage:
    from app.extend.blocks.bar_time.current_week_of_month import (
        current_week_of_month,
    )
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

current_week_of_month_spec = BlockSpec(
    id="bar_time.current_week_of_month",
    version="1.0.0",
    name="Current Week Of Month",
    description="Retrieve current Monday-aligned week of month (1-6)",
    category="bar_time",
    tags=("time", "week_of_month", "clock"),
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
    outputs=(
        OutputPort(
            "week_of_month",
            PortType.NUMBER,
            "Current week of month (1-6)",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_week_of_month_spec)
def current_week_of_month(source: Any = None) -> int:
    """Retrieve current Monday-aligned week of month (1-6)."""
    if hasattr(source, "current_week_of_month") and callable(
        source.current_week_of_month
    ):
        return int(source.current_week_of_month())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_week_of_month(ms)
    return _log_val("current_week_of_month", 0, res)
