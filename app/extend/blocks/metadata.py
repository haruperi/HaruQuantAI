"""Temporary migration bridge to app.core.trading.blocks.metadata."""

from __future__ import annotations

import sys

from app.core.trading.blocks import metadata as _implementation
from app.core.trading.blocks.metadata import *  # noqa: F403
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
    _freeze_mapping,
)

__all__ = [
    "BlockSpec",
    "ChartPane",
    "ExecutionKind",
    "InputPort",
    "OutputPort",
    "PortType",
    "_freeze_mapping",
]

sys.modules[__name__] = _implementation
