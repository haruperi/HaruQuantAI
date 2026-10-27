"""Shared asynchronous trading API for live and simulated execution."""

from .account import AccountProxy
from .api import Trading
from .base import TradeFilter, TradingClass
from .exits import (
    ExitAfterBars,
    ExitManager,
    ExitOutcome,
    ExitPlan,
    MoveSL2BE,
    ProfitTarget,
    StopLoss,
    TrailingStop,
)
from .history import ClosedTrade, DealProxy, HistoryOrderProxy
from .orders import OrderProxy
from .positions import PositionProxy
from .symbol import SymbolProxy
from .terminal import TerminalProxy
from .trade import Trade

__all__ = [
    "AccountProxy",
    "ClosedTrade",
    "DealProxy",
    "ExitAfterBars",
    "ExitManager",
    "ExitOutcome",
    "ExitPlan",
    "HistoryOrderProxy",
    "MoveSL2BE",
    "OrderProxy",
    "PositionProxy",
    "ProfitTarget",
    "StopLoss",
    "SymbolProxy",
    "TerminalProxy",
    "Trade",
    "TradeFilter",
    "Trading",
    "TradingClass",
    "TrailingStop",
]
