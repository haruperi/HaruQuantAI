"""Always True condition strategy block."""

from __future__ import annotations

from app.include.blocks.bar_time._common import _log_cond
from app.include.blocks.base import block
from app.include.blocks.metadata import (
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
