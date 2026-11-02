"""Always True condition strategy block.

Description:
    Evaluates constant True condition predicate for trading rule logic.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful AlwaysTrue block.
Key Capabilities:
    - FR-bar-time-predicate: Always returns boolean True condition.
Python API Usage:
    from app.extend.blocks.bar_time.always_true import always_true
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    OutputPort,
    PortType,
)

always_true_spec = BlockSpec(
    id="condition.always_true",
    version="1.0.0",
    name="Always True",
    description="Constant True condition predicate",
    category="bar_time",
    tags=("condition", "boolean", "constant"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "Always True"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(always_true_spec)
def always_true() -> bool:
    """Evaluate constant True condition predicate."""
    return _log_cond("always_true", 0, True)
