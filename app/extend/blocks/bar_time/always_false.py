"""Always False condition strategy block."""

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

always_false_spec = BlockSpec(
    id="condition.always_false",
    version="1.0.0",
    name="Always False",
    description="Constant False condition predicate",
    category="bar_time",
    tags=("condition", "boolean", "constant"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "Always False"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(always_false_spec)
def always_false() -> bool:
    """Evaluate constant False condition predicate."""
    return _log_cond("always_false", 0, False)
