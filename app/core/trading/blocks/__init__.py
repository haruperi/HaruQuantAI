"""Strategy building block contracts and specifications."""

from app.core.trading.blocks.base import BaseBlock, block
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
    "BaseBlock",
    "BlockSpec",
    "ChartPane",
    "ExecutionKind",
    "InputPort",
    "OutputPort",
    "PortType",
    "_freeze_mapping",
    "block",
]
