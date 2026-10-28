"""Logical NOT condition inversion strategy block."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

condition_not_spec = BlockSpec(
    id="condition.condition_not",
    version="1.0.0",
    name="Logical NOT",
    description="Evaluates logical NOT on a condition expression",
    category="comparisons",
    tags=("condition", "logic", "not"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("condition", PortType.ANY, "Condition expression to negate"),),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "Inverted boolean result"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(condition_not_spec)
def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
    """Evaluate logical NOT on a condition expression."""
    val = condition() if callable(condition) else condition
    return not bool(val)


__all__ = ["condition_not", "condition_not_spec"]
