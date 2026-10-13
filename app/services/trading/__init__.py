"""Shared native broker proxy classes."""

from app.services.brokers.contracts import (
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)

from .account_info import AccountInfo
from .deal_info import DealInfo
from .facade import Trading
from .history_order_info import HistoryOrderInfo
from .market_data import get_historical_bars, get_ticks
from .order_info import OrderInfo
from .position_info import PositionInfo
from .symbol_info import SymbolInfo
from .terminal_info import TerminalInfo
from .trade import Trade

__all__ = [
    "AccountInfo",
    "DealInfo",
    "HistoryOrderInfo",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TerminalInfo",
    "Trade",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "Trading",
    "get_historical_bars",
    "get_ticks",
]
