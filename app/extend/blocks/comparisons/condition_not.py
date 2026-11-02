"""Logical NOT condition inversion strategy block.

Description:
    Evaluates logical negation on a single condition expression,
    matching StrategyQuant Not snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful Not block.
Key Capabilities:
    - FR-comparison-logic: Logical NOT negation.
Python API Usage:
    from app.extend.blocks.comparisons.condition_not import condition_not
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

from collections.abc import Callable
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
from app.extend.blocks.comparisons._common import _log_comparison

condition_not_spec = BlockSpec(
    id="condition.condition_not",
    version="1.0.0",
    name="Logical NOT",
    description="Evaluates logical negation on condition expression",
    category="comparisons",
    tags=("condition", "logic", "not"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("condition", PortType.ANY, "Condition expression to negate"),),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "Inverted condition truth value",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(condition_not_spec)
def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
    """Evaluate logical NOT on condition expression."""
    val = condition() if callable(condition) else condition
    res = not bool(val)
    return _log_comparison("condition_not", res)


__all__ = ["condition_not", "condition_not_spec"]
