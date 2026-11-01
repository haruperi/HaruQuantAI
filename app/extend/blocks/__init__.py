"""Unified strategy blocks package."""

from app.extend.blocks.base import BaseBlock, block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
    block_registry,
)
from app.extend.blocks.series import (
    BarData,
    IndicatorSeries,
    resolve_shift_value,
    round_value,
)

__all__ = [
    "BarData",
    "BaseBlock",
    "BlockDescriptor",
    "BlockRegistry",
    "BlockRegistryError",
    "BlockSpec",
    "CatalogSnapshot",
    "ChartPane",
    "ExecutionKind",
    "IndicatorSeries",
    "InputPort",
    "OutputPort",
    "PortType",
    "block",
    "block_registry",
    "resolve_shift_value",
    "round_value",
]
