"""Bar Month temporal value strategy block.

Description:
    Extracts month (1=January..12=December) of bar at specified historical shift,
    matching StrategyQuant BarMonth snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarMonth block.
Key Capabilities:
    - FR-bar-time-value: Extract bar month component (1-12).
Python API Usage:
    from app.extend.blocks.bar_time.bar_month import bar_month
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

bar_month_spec = BlockSpec(
    id="bar_time.bar_month",
    version="1.0.0",
    name="Bar Month",
    description="Extract month of the bar (1-12) at shift",
    category="bar_time",
    tags=("time", "month", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("month", PortType.NUMBER, "Month of the bar (1-12)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_month_spec)
def bar_month(source: Any, shift: int = 0) -> int:
    """Extract month of the bar (1-12) at shift."""
    if hasattr(source, "bar_month") and callable(source.bar_month):
        return int(source.bar_month(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_month(ms) if ms != -1 else -1
    return _log_val("bar_month", shift, res)
