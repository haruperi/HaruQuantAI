"""Bar Minute temporal value strategy block.

Description:
    Extracts minute (0-59) of bar at specified historical shift,
    matching StrategyQuant BarMinute snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarMinute block.
Key Capabilities:
    - FR-bar-time-value: Extract bar minute component (0-59).
Python API Usage:
    from app.extend.blocks.bar_time.bar_minute import bar_minute
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

bar_minute_spec = BlockSpec(
    id="bar_time.bar_minute",
    version="1.0.0",
    name="Bar Minute",
    description="Extract minute of the bar (0-59) at shift",
    category="bar_time",
    tags=("time", "minute", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("minute", PortType.NUMBER, "Minute of the bar (0-59)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_minute_spec)
def bar_minute(source: Any, shift: int = 0) -> int:
    """Extract minute of the bar (0-59) at shift."""
    if hasattr(source, "bar_minute") and callable(source.bar_minute):
        return int(source.bar_minute(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_minute(ms) if ms != -1 else -1
    return _log_val("bar_minute", shift, res)
