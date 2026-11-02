"""Strategy building block contracts, registry, and metadata specifications."""

from __future__ import annotations

from app.core.trading.blocks.base import BaseBlock, block
from app.core.trading.blocks.indicator import BaseIndicator
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
    _freeze_mapping,
)
from app.core.trading.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
    block_registry,
)
from app.core.trading.blocks.runtime import (
    AccountSource,
    DealSource,
    OrderExecution,
    OrderSource,
    PositionSource,
    SymbolSource,
    TradingRuntime,
)
from app.core.trading.blocks.series import (
    COMPUTED_PRICE_INPUTS,
    BarData,
    IndicatorSeries,
    computed_price,
    resolve_shift_value,
    round_value,
)

__all__ = [
    "COMPUTED_PRICE_INPUTS",
    "AccountSource",
    "BarData",
    "BaseBlock",
    "BaseIndicator",
    "BlockDescriptor",
    "BlockRegistry",
    "BlockRegistryError",
    "BlockSpec",
    "CatalogSnapshot",
    "ChartPane",
    "DealSource",
    "ExecutionKind",
    "IndicatorSeries",
    "InputPort",
    "OrderExecution",
    "OrderSource",
    "OutputPort",
    "PortType",
    "PositionSource",
    "SymbolSource",
    "TradingRuntime",
    "_freeze_mapping",
    "block",
    "block_registry",
    "computed_price",
    "resolve_shift_value",
    "round_value",
]
