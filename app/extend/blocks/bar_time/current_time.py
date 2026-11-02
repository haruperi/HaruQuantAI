"""Current Time temporal value strategy block.

Description:
    Retrieves current active broker time as packed HHMM integer,
    matching StrategyQuant CurrentTime snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentTime block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current broker time in packed HHMM format.
Python API Usage:
    from app.extend.blocks.bar_time.current_time import current_time
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

current_time_spec = BlockSpec(
    id="bar_time.current_time",
    version="1.0.0",
    name="Current Time",
    description="Retrieve current time as packed HHMM in broker time",
    category="bar_time",
    tags=("time", "clock"),
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
    outputs=(OutputPort("time", PortType.NUMBER, "Current time as packed HHMM"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_time_spec)
def current_time(source: Any = None) -> int:
    """Retrieve current time as packed HHMM in broker time."""
    if hasattr(source, "current_time") and callable(source.current_time):
        return int(source.current_time())
    ms = resolve_current_time_ms(source)
    res = DateTime.get_hhmm(ms)
    return _log_val("current_time", 0, res)
