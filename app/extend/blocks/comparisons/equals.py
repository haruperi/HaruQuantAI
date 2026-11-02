"""Equals comparative equality condition strategy block.

Description:
    Evaluates whether left operand equals right operand at shift,
    matching StrategyQuant Equals snippet.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful Equals block.
Key Capabilities:
    - FR-comparison-equality: Test numerical equality between operands.
Python API Usage:
    from app.extend.blocks.comparisons.equals import equals
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

from app.extend.blocks.base import block
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    _log_comparison,
    _pair,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

equals_spec = BlockSpec(
    id="condition.equals",
    version="1.0.0",
    name="Equals",
    description="Evaluates whether left operand equals right operand at shift",
    category="comparisons",
    tags=("condition", "comparison", "equality", "equals"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if left == right"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(equals_spec)
def equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left operand equals right operand at shift."""
    val1, val2 = _pair(
        left,
        right,
        shift,
        precision,
        s1=shift1,
        s2=shift2,
        rd=round_digits,
    )
    if math.isnan(val1) or math.isnan(val2):
        return _log_comparison("equals", False)
    res = val1 == val2
    return _log_comparison("equals", res)


__all__ = ["equals", "equals_spec"]
