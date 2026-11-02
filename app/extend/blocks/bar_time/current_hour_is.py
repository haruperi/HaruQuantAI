"""Current Hour Is condition strategy block.

Description:
    Evaluates whether current broker hour equals target hour,
    matching StrategyQuant CurrentHourIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentHourIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare current broker hour against target.
Python API Usage:
    from app.extend.blocks.bar_time.current_hour_is import current_hour_is
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
from app.extend.blocks.bar_time.current_hour import current_hour

current_hour_is_spec = BlockSpec(
    id="condition.current_hour_is",
    version="1.0.0",
    name="Current Hour Is",
    description="Evaluate whether current hour matches target hour (0-23)",
    category="bar_time",
    tags=("condition", "hour"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("hour", PortType.NUMBER, "Target hour (0-23)", default=0),
    ),
    outputs=(
        OutputPort("condition", PortType.BOOLEAN, "True if current hour matches"),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_hour_is_spec)
def current_hour_is(source: Any = None, hour: int = 0) -> bool:
    """Evaluate whether current hour matches target hour (0-23)."""
    if hasattr(source, "current_hour_is") and callable(source.current_hour_is):
        return bool(source.current_hour_is(hour))
    res = current_hour(source) == hour
    return _log_cond("current_hour_is", hour, res)
