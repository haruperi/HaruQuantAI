"""Strategy blocks package for strategy rules, conditions, and actions.

Description:
    Root package for StrategyQuant-faithful building blocks organized by
    category: actions, bar_time, comparisons, functions, indicators, order,
    price, strategy_control, and types.
Purpose:
    FEAT-BLOCK-FRAMEWORK: StrategyQuant donor-faithful blocks package.
Key Capabilities:
    - FR-BLOCKS-EXPORTS: Canonical block exports and registry interface.
Python API Usage:
    from app.extend.blocks.price import Close, High, Low, Open
    from app.extend.blocks.strategy_control import StrategyControl
CLI Usage:
    uv run pytest tests/extend/blocks/ --no-cov
"""

from __future__ import annotations

from app.core.trading.blocks.base import BaseBlock, block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
    block_registry,
)
from app.core.trading.blocks.series import (
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
