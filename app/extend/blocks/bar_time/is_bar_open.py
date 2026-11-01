"""Is Bar Open event condition strategy block."""

from __future__ import annotations

from typing import Any

from app.extend.blocks.bar_time._common import _log_cond
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

is_bar_open_spec = BlockSpec(
    id="condition.is_bar_open",
    version="1.0.0",
    name="Is Bar Open",
    description="Evaluate whether current execution is at bar open event",
    category="bar_time",
    tags=("condition", "bar_open", "event"),
    execution_kind=ExecutionKind.CONDITION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort(
            "source",
            PortType.ANY,
            "Optional TimeConditions context",
            default=None,
        ),
        InputPort(
            "is_open",
            PortType.BOOLEAN,
            "Override boolean state",
            default=None,
        ),
    ),
    outputs=(OutputPort("condition", PortType.BOOLEAN, "True if at bar open"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(is_bar_open_spec)
def is_bar_open(source: Any = None, is_open: bool | None = None) -> bool:
    """Evaluate whether current execution is at bar open event."""
    if hasattr(source, "is_bar_open") and callable(source.is_bar_open):
        return bool(source.is_bar_open(is_open=is_open))
    res = True if is_open is None else bool(is_open)
    return _log_cond("is_bar_open", int(res), res)
