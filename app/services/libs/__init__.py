# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Core library modules for trading, simulation, and time arithmetic."""

from __future__ import annotations

from typing import Any

from .bar_time import (
    BarTime,
    DateTimeSeries,
    TimeConditions,
    format_timestamp,
    normalize_timestamps,
)
from .generators import RandomGenerator
from .time import HQTime

_TRADING_SYMBOLS = {
    "AccountInfo",
    "AccountSnapshot",
    "AccountTradeMode",
    "BaseTradingClass",
    "BookInfo",
    "BookType",
    "DealInfo",
    "DealSnapshot",
    "HistoryOrderInfo",
    "HistoryOrderSnapshot",
    "MarginMode",
    "OrderFilling",
    "OrderInfo",
    "OrderSnapshot",
    "OrderTime",
    "OrderType",
    "PositionInfo",
    "PositionSnapshot",
    "PropertyValue",
    "Receipt",
    "ReceiptStatus",
    "StopoutMode",
    "SymbolInfo",
    "SymbolSnapshot",
    "TerminalInfo",
    "TerminalSnapshot",
    "Trade",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResolution",
    "TradeResult",
    "TradeRetcode",
    "Trading",
    "TradingBackend",
    "TradingClass",
}


def __getattr__(name: str) -> Any:
    """Lazily import trading symbols on demand."""
    if name in _TRADING_SYMBOLS:
        from app.services.libs import trading

        return getattr(trading, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AccountInfo",
    "AccountSnapshot",
    "BarTime",
    "BaseTradingClass",
    "BookInfo",
    "BookType",
    "DateTimeSeries",
    "DealInfo",
    "DealSnapshot",
    "HQTime",
    "HistoryOrderInfo",
    "HistoryOrderSnapshot",
    "OrderFilling",
    "OrderInfo",
    "OrderSnapshot",
    "OrderTime",
    "OrderType",
    "PositionInfo",
    "PositionSnapshot",
    "RandomGenerator",
    "SymbolInfo",
    "SymbolSnapshot",
    "TerminalInfo",
    "TerminalSnapshot",
    "TimeConditions",
    "Trade",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "Trading",
    "TradingBackend",
    "TradingClass",
    "format_timestamp",
    "normalize_timestamps",
]
