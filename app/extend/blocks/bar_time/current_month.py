"""Current Month temporal value strategy block.

Description:
    Retrieves current active broker month (1=January..12=December),
    matching StrategyQuant CurrentMonth snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentMonth block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current broker month component (1-12).
Python API Usage:
    from app.extend.blocks.bar_time.current_month import current_month
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
from app.extend.blocks.bar_time._common import (
    DateTime,
    _log_val,
    resolve_current_time_ms,
)

current_month_spec = BlockSpec(
    id="bar_time.current_month",
    version="1.0.0",
    name="Current Month",
    description="Retrieve current month (1-12) in broker time",
    category="bar_time",
    tags=("time", "month", "clock"),
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
    outputs=(OutputPort("month", PortType.NUMBER, "Current month (1-12)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_month_spec)
def current_month(source: Any = None) -> int:
    """Retrieve current month (1-12) in broker time."""
    if hasattr(source, "current_month") and callable(source.current_month):
        return int(source.current_month())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_month(ms)
    return _log_val("current_month", 0, res)
