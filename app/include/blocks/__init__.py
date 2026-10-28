"""Unified strategy blocks package."""

from app.include.blocks.base import BaseBlock, block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
    block_registry,
)
from app.include.blocks.series import (
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
