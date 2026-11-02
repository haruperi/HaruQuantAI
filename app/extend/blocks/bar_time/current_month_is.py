"""Current Month Is condition strategy block.

Description:
    Evaluates whether current broker month equals target month,
    matching StrategyQuant CurrentMonthIs snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful CurrentMonthIs block.
Key Capabilities:
    - FR-bar-time-predicate: Compare current broker month against target.
Python API Usage:
    from app.extend.blocks.bar_time.current_month_is import current_month_is
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
from app.extend.blocks.bar_time.current_month import current_month

current_month_is_spec = BlockSpec(
    id="condition.current_month_is",
    version="1.0.0",
    name="Current Month Is",
    description="Evaluate whether current month matches target month (1-12)",
    category="bar_time",
    tags=("condition", "month"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional temporal context",
            default=None,
        ),
        InputPort("month", PortType.NUMBER, "Target month (1-12)", default=1),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if current month matches",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(current_month_is_spec)
def current_month_is(source: Any = None, month: int = 1) -> bool:
    """Evaluate whether current month matches target month (1-12)."""
    if hasattr(source, "current_month_is") and callable(source.current_month_is):
        return bool(source.current_month_is(month))
    res = current_month(source) == month
    return _log_cond("current_month_is", month, res)
