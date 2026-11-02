"""Is Bar Open event condition strategy block.

Description:
    Evaluates whether execution trigger matches bar opening event,
    matching StrategyQuant IsBarOpen snippet.
Purpose:
    FEAT-BAR-TIME-BLOCKS: StrategyQuant donor-faithful IsBarOpen block.
Key Capabilities:
    - FR-bar-time-predicate: Test if bar open update event triggered.
Python API Usage:
    from app.extend.blocks.bar_time.is_bar_open import is_bar_open
CLI Usage:
    uv run pytest tests/extend/blocks/test_bar_time.py --no-cov
"""

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
    if is_open is not None:
        res = bool(is_open)
    elif hasattr(source, "is_bar_open") and isinstance(source.is_bar_open, bool):
        res = bool(source.is_bar_open)
    elif hasattr(source, "update_event_type"):
        res = source.update_event_type in ("BarOpen", 1)
    elif hasattr(source, "UpdateEventType"):
        res = source.UpdateEventType in ("BarOpen", 1)
    else:
        res = True
    return _log_cond("is_bar_open", int(res), res)
