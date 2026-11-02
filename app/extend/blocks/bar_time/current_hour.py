"""Current Hour temporal value strategy block.

Description:
    Retrieves current active broker hour (0-23),
    matching StrategyQuant CurrentHour snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentHour block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current broker hour component (0-23).
Python API Usage:
    from app.extend.blocks.bar_time.current_hour import current_hour
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

current_hour_spec = BlockSpec(
    id="bar_time.current_hour",
    version="1.0.0",
    name="Current Hour",
    description="Retrieve current hour (0-23) in broker time",
    category="bar_time",
    tags=("time", "hour", "clock"),
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
    outputs=(OutputPort("hour", PortType.NUMBER, "Current hour (0-23)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_hour_spec)
def current_hour(source: Any = None) -> int:
    """Retrieve current hour (0-23) in broker time."""
    if hasattr(source, "current_hour") and callable(source.current_hour):
        return int(source.current_hour())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_hour(ms)
    return _log_val("current_hour", 0, res)
