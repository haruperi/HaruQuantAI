"""Shared asynchronous trading API for live and simulated execution.

Description:
    Exports the canonical Trading facade, execution proxies (Trade, AccountProxy,
    OrderProxy, PositionProxy, DealProxy, HistoryOrderProxy, SymbolProxy,
    TerminalProxy), base classes, and dynamic exit policy definitions.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and exit manager.
Key Capabilities:
    - FR-trading-facade-composition: Provide unified Trading facade and proxies.
    - FR-trading-exit-manager: Provide ExitManager, ExitPlan, and exit policies.
Python API Usage:
    from app.workspace.trading import Trading, Trade, ExitManager, ExitPlan
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

from .account import AccountProxy
from .api import Trading
from .base import TradingClass
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
from .history import DealProxy, HistoryOrderProxy
from .orders import OrderProxy
from .positions import PositionProxy
from .symbol import SymbolProxy
from .terminal import TerminalProxy
from .trade import Trade

__all__ = [
    "AccountProxy",
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
    "Trading",
    "TradingClass",
    "TrailingStop",
]
