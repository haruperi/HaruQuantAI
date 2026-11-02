"""Logical OR condition composition strategy block.

Description:
    Evaluates short-circuit logical OR across multiple condition expressions,
    matching StrategyQuant OR snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful OR block.
Key Capabilities:
    - FR-comparison-logic: Short-circuit logical OR reduction.
Python API Usage:
    from app.extend.blocks.comparisons.condition_or import condition_or
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

condition_or_spec = BlockSpec(
    id="condition.condition_or",
    version="1.0.0",
    name="Logical OR",
    description=(
        "Evaluates short-circuit logical OR across multiple condition expressions"
    ),
    category="comparisons",
    tags=("condition", "logic", "or"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("conditions", PortType.ANY, "Variadic condition expressions"),),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if any condition evaluates to true",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(condition_or_spec)
def condition_or(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical OR across multiple condition expressions."""
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if bool(val):
            return _log_comparison("condition_or", True)
    return _log_comparison("condition_or", False)


__all__ = ["condition_or", "condition_or_spec"]
