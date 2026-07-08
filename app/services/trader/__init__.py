"""Generic Trade Classes module.

Provides unified, cross-platform wrappers matching the MQL5 Trade Classes
interface for account info, symbol info, terminal info, position/order details,
and trade execution.
"""

from app.services.trader.concurrency import ConcurrencyQueue
from app.services.trader.idempotency import IdempotencyService
from app.services.trader.info.account import AccountInfo
from app.services.trader.info.deal import DealInfo
from app.services.trader.info.history_order import HistoryOrderInfo
from app.services.trader.info.order import OrderInfo
from app.services.trader.info.position import PositionInfo
from app.services.trader.info.symbol import SymbolInfo
from app.services.trader.info.terminal import TerminalInfo
from app.services.trader.rate_limiter import RateLimiter, get_rate_limiter
from app.services.trader.readiness import ReadinessService
from app.services.trader.reconciliation import ReconciliationService
from app.services.trader.reporting import ReportingService
from app.services.trader.result import (
    BrokerResponseNormalizer,
    NormalizedTradeResult,
    ResultBuilder,
)
from app.services.trader.store import InMemoryTradeStore, TradeStore, get_default_store
from app.services.trader.trade import Trade
from app.services.trader.validation import ValidationService

__all__ = [
    "AccountInfo",
    "BrokerResponseNormalizer",
    "ConcurrencyQueue",
    "DealInfo",
    "HistoryOrderInfo",
    "IdempotencyService",
    "InMemoryTradeStore",
    "NormalizedTradeResult",
    "OrderInfo",
    "PositionInfo",
    "RateLimiter",
    "ReadinessService",
    "ReconciliationService",
    "ReportingService",
    "ResultBuilder",
    "SymbolInfo",
    "TerminalInfo",
    "Trade",
    "TradeStore",
    "ValidationService",
    "get_default_store",
    "get_rate_limiter",
]
