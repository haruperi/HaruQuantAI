"""Bar Hour Is Smaller condition strategy block.

Description:
    Evaluates whether bar hour is strictly smaller than target hour at shift,
    matching StrategyQuant BarHourIsSmaller snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarHourIsSmaller block.
Key Capabilities:
    - FR-bar-time-predicate: Compare if bar hour < target hour.
Python API Usage:
    from app.extend.blocks.bar_time.bar_hour_is_smaller import bar_hour_is_smaller
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.bar_hour import bar_hour
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

bar_hour_is_smaller_spec = BlockSpec(
    id="condition.bar_hour_is_smaller",
    version="1.0.0",
    name="Bar Hour Is Smaller",
    description="Evaluate whether bar hour is smaller than target hour (0-23)",
    category="bar_time",
    tags=("condition", "hour", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("hour", PortType.NUMBER, "Target threshold hour (0-23)", default=0),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if bar hour < target"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_hour_is_smaller_spec)
def bar_hour_is_smaller(source: Any, hour: int = 0, shift: int = 0) -> bool:
    """Evaluate whether bar hour is smaller than target hour (0-23)."""
    if hasattr(source, "bar_hour_is_smaller") and callable(source.bar_hour_is_smaller):
        return bool(source.bar_hour_is_smaller(hour, shift))
    bh = bar_hour(source, shift)
    res = (bh < hour) if bh != -1 else False
    return _log_cond("bar_hour_is_smaller", hour, res)
