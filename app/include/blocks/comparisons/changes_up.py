"""Changes Up 3-bar turning comparative condition strategy block."""

from __future__ import annotations

import math
from typing import Any

from app.include.blocks.base import block
from app.include.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    resolve_shift_value,
    round_value,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

changes_up_spec = BlockSpec(
    id="condition.changes_up",
    version="1.0.0",
    name="Changes Up",
    description="Evaluates 3-bar upward turn (v[s+2] > v[s+1] < v[s])",
    category="comparisons",
    tags=("condition", "trend", "turn", "changes_up"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Indicator series"),
        InputPort("not_strict", PortType.BOOLEAN, "Allow flat left shoulder"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True on upward turn"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(changes_up_spec)
def changes_up(
    indicator: Any,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate 3-bar upward turn (`v[s+2] > v[s+1] < v[s]`)."""
    p = precision if round_digits is None else round_digits
    v2 = round_value(resolve_shift_value(indicator, shift + 2), p)
    v1 = round_value(resolve_shift_value(indicator, shift + 1), p)
    v0 = round_value(resolve_shift_value(indicator, shift), p)
    if any(math.isnan(v) for v in (v2, v1, v0)):
        return False
    return (v2 >= v1 if not_strict else v2 > v1) and v1 < v0


__all__ = ["changes_up", "changes_up_spec"]
