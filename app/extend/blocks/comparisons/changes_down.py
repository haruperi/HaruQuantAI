"""Changes Down 3-bar turning comparative condition strategy block.

Description:
    Evaluates 3-bar downward turn (v[s+2] < v[s+1] > v[s]), matching
    StrategyQuant turning point detection logic.
Purpose:
    FEAT-COMPARISONS-BLOCKS: StrategyQuant donor-faithful ChangesDown block.
Key Capabilities:
    - FR-comparison-turning: Detect 3-bar downward turning peaks.
Python API Usage:
    from app.extend.blocks.comparisons.changes_down import changes_down
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
    resolve_shift_value,
    round_value,
)

changes_down_spec = BlockSpec(
    id="condition.changes_down",
    version="1.0.0",
    name="Changes Down",
    description="Evaluates 3-bar downward turn (v[s+2] < v[s+1] > v[s])",
    category="comparisons",
    tags=("condition", "trend", "turn", "changes_down"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("indicator", PortType.SERIES, "Indicator series"),
        InputPort(
            "not_strict",
            PortType.BOOLEAN,
            "Allow flat left shoulder",
            default=False,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True on downward turn"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(changes_down_spec)
def changes_down(
    indicator: Any,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate 3-bar downward turn (v[s+2] < v[s+1] > v[s])."""
    p = precision if round_digits is None else round_digits
    v2 = round_value(resolve_shift_value(indicator, shift + 2), p)
    v1 = round_value(resolve_shift_value(indicator, shift + 1), p)
    v0 = round_value(resolve_shift_value(indicator, shift), p)
    if any(math.isnan(v) for v in (v2, v1, v0)):
        return _log_comparison("changes_down", False)
    res = (v2 <= v1 and v0 < v1) if not_strict else (v2 < v1 and v0 < v1)
    return _log_comparison("changes_down", res)


__all__ = ["changes_down", "changes_down_spec"]
