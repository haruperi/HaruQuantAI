"""Bar Time temporal value strategy block.

Description:
    Extracts time of bar at specified historical shift as packed HHMM integer,
    matching StrategyQuant BarTime snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarTime block.
Key Capabilities:
    - FR-bar-time-value: Extract bar time in packed HHMM integer format.
Python API Usage:
    from app.extend.blocks.bar_time.bar_time import bar_time
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

bar_time_spec = BlockSpec(
    id="bar_time.bar_time",
    version="1.0.0",
    name="Bar Time",
    description="Extract time of bar at shift as packed HHMM integer",
    category="bar_time",
    tags=("time", "clock", "bar"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("time", PortType.NUMBER, "Time as packed HHMM integer"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_time_spec)
def bar_time(source: Any, shift: int = 0) -> int:
    """Extract time of bar at shift as packed HHMM integer."""
    if hasattr(source, "bar_time") and callable(source.bar_time):
        return int(source.bar_time(shift))
    ms = resolve_time_ms(source, shift)
    res = DateTime.get_hhmm(ms) if ms != -1 else -1
    return _log_val("bar_time", shift, res)
