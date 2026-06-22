"""Strategy Module public API.

Exports the core models, base strategy classes, execution services,
inspectors, and reference implementations.
"""

from app.services.strategy.base import BaseStrategy, StrategyProtocol
from app.services.strategy.models import (
    OrderSide,
    OrderType,
    PortfolioState,
    StrategyConfig,
    StrategyContext,
    StrategyManifest,
    StrategyResult,
    TradeIntent,
)
from app.services.strategy.pybots import (
    TrendFollowingState,
    TrendFollowingStrategy,
)
from app.services.strategy.service import StrategyService, TradeIntentInspector

__all__ = [
    "BaseStrategy",
    "OrderSide",
    "OrderType",
    "PortfolioState",
    "StrategyConfig",
    "StrategyContext",
    "StrategyManifest",
    "StrategyProtocol",
    "StrategyResult",
    "StrategyService",
    "TradeIntent",
    "TradeIntentInspector",
    "TrendFollowingState",
    "TrendFollowingStrategy",
]
