"""Bar Minute Is condition strategy block.

Description:
    Evaluates whether bar minute equals target minute at shift,
    matching StrategyQuant BarMinuteIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful BarMinuteIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare bar minute against target minute.
Python API Usage:
    from app.extend.blocks.bar_time.bar_minute_is import bar_minute_is
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
from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.bar_minute import bar_minute

bar_minute_is_spec = BlockSpec(
    id="condition.bar_minute_is",
    version="1.0.0",
    name="Bar Minute Is",
    description="Evaluate whether bar minute equals target minute (0-59)",
    category="bar_time",
    tags=("condition", "minute", "bar"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("minute", PortType.NUMBER, "Target minute (0-59)", default=0),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if bar minute matches"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(bar_minute_is_spec)
def bar_minute_is(source: Any, minute: int = 0, shift: int = 0) -> bool:
    """Evaluate whether bar minute equals target minute (0-59)."""
    if hasattr(source, "bar_minute_is") and callable(source.bar_minute_is):
        return bool(source.bar_minute_is(minute, shift))
    bm = bar_minute(source, shift)
    res = (bm == minute) if bm != -1 else False
    return _log_cond("bar_minute_is", minute, res)
