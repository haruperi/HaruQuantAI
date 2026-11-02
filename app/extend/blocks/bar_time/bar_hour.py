"""Bar Hour temporal value strategy block.

Description:
    Extracts hour (0-23) of bar at specified historical shift,
    matching StrategyQuant BarHour snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarHour block.
Key Capabilities:
    - FR-bar-time-value: Extract bar hour component (0-23).
Python API Usage:
    from app.extend.blocks.bar_time.bar_hour import bar_hour
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import DateTime, _log_val, resolve_time_ms
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_hour_spec = BlockSpec(
    id="bar_time.bar_hour",
    version="1.0.0",
    name="Bar Hour",
    description="Extract hour of the bar (0-23) at shift",
    category="bar_time",
    tags=("time", "hour", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("hour", PortType.NUMBER, "Hour of the bar (0-23)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_hour_spec)
def bar_hour(source: Any, shift: int = 0) -> int:
    """Extract hour of the bar (0-23) at shift."""
    if hasattr(source, "bar_hour") and callable(source.bar_hour):
        return int(source.bar_hour(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_hour(ms) if ms != -1 else -1
    return _log_val("bar_hour", shift, res)
