"""Logical AND condition composition strategy block."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

condition_and_spec = BlockSpec(
    id="condition.condition_and",
    version="1.0.0",
    name="Logical AND",
    description=(
        "Evaluates short-circuit logical AND across multiple condition expressions"
    ),
    category="comparisons",
    tags=("condition", "logic", "and"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(InputPort("conditions", PortType.ANY, "Variadic condition expressions"),),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if all conditions evaluate to true",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(condition_and_spec)
def condition_and(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical AND across multiple condition expressions."""
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if not bool(val):
            return False
    return True


__all__ = ["condition_and", "condition_and_spec"]
