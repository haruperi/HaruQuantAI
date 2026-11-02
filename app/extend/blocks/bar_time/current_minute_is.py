"""Current Minute Is condition strategy block.

Description:
    Evaluates whether current broker minute equals target minute,
    matching StrategyQuant CurrentMinuteIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentMinuteIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare current broker minute against target.
Python API Usage:
    from app.extend.blocks.bar_time.current_minute_is import current_minute_is
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.bar_time.current_minute import current_minute
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_minute_is_spec = BlockSpec(
    id="condition.current_minute_is",
    version="1.0.0",
    name="Current Minute Is",
    description="Evaluate whether current minute matches target minute (0-59)",
    category="bar_time",
    tags=("condition", "minute"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("minute", PortType.NUMBER, "Target minute (0-59)", default=0),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if current minute matches",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_minute_is_spec)
def current_minute_is(source: Any = None, minute: int = 0) -> bool:
    """Evaluate whether current minute matches target minute (0-59)."""
    if hasattr(source, "current_minute_is") and callable(source.current_minute_is):
        return bool(source.current_minute_is(minute))
    res = current_minute(source) == minute
    return _log_cond("current_minute_is", minute, res)
