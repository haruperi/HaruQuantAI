"""Crosses Above comparative crossover condition strategy block.

Description:
    Evaluates whether left operand crossed above right operand between
    historical shift + 1 and shift, matching StrategyQuant CrossesAbove.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful CrossesAbove block.
Key Capabilities:
    - FR-comparison-crossover: Detect upward crossover between operands.
Python API Usage:
    from app.extend.blocks.comparisons.crosses_above import crosses_above
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
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
from app.extend.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    _log_comparison,
    _pair,
)

crosses_above_spec = BlockSpec(
    id="condition.crosses_above",
    version="1.0.0",
    name="Crosses Above",
    description=(
        "Evaluates whether left operand crossed above right operand from shift+1"
        " to shift"
    ),
    category="comparisons",
    tags=("condition", "comparison", "crossover", "crosses_above"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("left", PortType.ANY, "Left operand (series or value)"),
        InputPort("right", PortType.ANY, "Right operand (series or value)"),
    ),
    outputs=(
        OutputPort(
            "condition",
            PortType.BOOLEAN,
            "True if left crossed above right",
        ),
    ),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(crosses_above_spec)
def crosses_above(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left crossed above right between shift + 1 and shift."""
    val11, val21 = _pair(left, right, shift + 1, precision, rd=round_digits)
    val10, val20 = _pair(left, right, shift, precision, rd=round_digits)
    if any(math.isnan(v) for v in (val11, val21, val10, val20)):
        return _log_comparison("crosses_above", False)
    res = val11 < val21 and val10 > val20
    return _log_comparison("crosses_above", res)


__all__ = ["crosses_above", "crosses_above_spec"]
