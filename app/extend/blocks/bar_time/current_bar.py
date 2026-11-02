"""Current Bar index value strategy block.

Description:
    Retrieves current active bar counter or completed bar index offset,
    matching StrategyQuant CurrentBar snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentBar block.
Key Capabilities:
    - FR-bar-time-value: Retrieve current bar counter/index.
Python API Usage:
    from app.extend.blocks.bar_time.current_bar import current_bar
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_val, resolve_bar_count
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

current_bar_spec = BlockSpec(
    id="bar_time.current_bar",
    version="1.0.0",
    name="Current Bar",
    description="Retrieve bar index / completed bar count",
    category="bar_time",
    tags=("time", "bar", "index"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("source", PortType.ANY, "Bar time source or series"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift offset", default=0),
    ),
    outputs=(OutputPort("bar_index", PortType.NUMBER, "Current bar index"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_bar_spec)
def current_bar(source: Any, shift: int = 0) -> int:
    """Retrieve bar index / completed bar count."""
    for attr in ("current_bar", "get_current_bar", "getCurrentBar"):
        if hasattr(source, attr):
            fn = getattr(source, attr)
            if callable(fn):
                try:
                    res = int(fn(shift))
                except TypeError:
                    res = int(fn())
                return _log_val("current_bar", shift, res)
    n = resolve_bar_count(source)
    res = (n - 1 - shift) if (0 <= shift < n) else -1
    return _log_val("current_bar", shift, res)
