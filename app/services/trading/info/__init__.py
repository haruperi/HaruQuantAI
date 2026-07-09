"""Read-only MQL5-compatible trading information facades."""

from __future__ import annotations

from app.services.trading.info.account import AccountInfo
from app.services.trading.info.deal import DealInfo
from app.services.trading.info.history_order import HistoryOrderInfo
from app.services.trading.info.order import OrderInfo
from app.services.trading.info.position import PositionInfo
from app.services.trading.info.symbol import SymbolInfo
from app.services.trading.info.terminal import TerminalInfo
from app.utils.logger import logger

logger.info("Loaded trading read-only info facades.")

__all__ = [
    "AccountInfo",
    "DealInfo",
    "HistoryOrderInfo",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TerminalInfo",
]
