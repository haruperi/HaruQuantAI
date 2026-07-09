"""Shared contracts and base classes for HaruQuant strategies."""

from app.services.contracts.strategies import (
    AccountSnapshot,
    Bar,
    Direction,
    EntryType,
    IntentAction,
    MarketContext,
    PendingOrderSnapshot,
    PositionSnapshot,
    ProtectionRequest,
    QuoteSnapshot,
    RuntimeMode,
    SignalSet,
    StrategyDecision,
    TradeIntent,
)
from app.services.strategy.base import BaseStrategy, StrategyPermissionError
from app.services.strategy.config import (
    ConfigurationError,
    StrategyConfig,
    load_strategy_config,
    validate_strategy_config,
)
from app.services.strategy.state import StrategyState

__all__ = [
    "AccountSnapshot",
    "Bar",
    "BaseStrategy",
    "ConfigurationError",
    "Direction",
    "EntryType",
    "IntentAction",
    "MarketContext",
    "PendingOrderSnapshot",
    "PositionSnapshot",
    "ProtectionRequest",
    "QuoteSnapshot",
    "RuntimeMode",
    "SignalSet",
    "StrategyConfig",
    "StrategyDecision",
    "StrategyPermissionError",
    "StrategyState",
    "TradeIntent",
    "load_strategy_config",
    "validate_strategy_config",
]
