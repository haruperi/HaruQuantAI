"""Trading policy and runtime helpers."""

from app.services.utils.standard import standardize_domain_exports

from .account_info import AccountInfo
from .concurrency import ConcurrencyQueue
from .deal_info import DealInfo
from .history_order_info import HistoryOrderInfo
from .idempotency import IdempotencyService
from .order_info import OrderInfo
from .permissions import (
    StrategyPermissionError,
    StrategyRuntimePermissionService,
    assert_strategy_allowed,
)
from .position_info import PositionInfo
from .rate_limiter import RateLimiter, get_rate_limiter
from .readiness import ReadinessService
from .reconciliation import ReconciliationService
from .reporting import ReportingService
from .result import (
    BrokerResponseNormalizer,
    NormalizedTradeResult,
    ResultBuilder,
)
from .stateful import (
    OrderSnapshot,
    OrderType,
    PositionSnapshot,
    PositionType,
    StatefulStrategyMixin,
    StatefulStrategyProtocol,
    StrategyContext,
    StrategyRuntimeState,
    TimeInForce,
    TradeAction,
    TradeActionType,
    TradeSide,
    TradeSnapshot,
)
from .store import InMemoryTradeStore, TradeStore, get_default_store
from .symbol_info import SymbolInfo
from .terminal_info import TerminalInfo
from .trade import Trade
from .validation import ValidationService

__all__ = [
    # Permissions exports
    "StrategyPermissionError",
    "StrategyRuntimePermissionService",
    "assert_strategy_allowed",
    # Stateful strategy contract exports
    "OrderSnapshot",
    "OrderType",
    "PositionSnapshot",
    "PositionType",
    "StatefulStrategyMixin",
    "StatefulStrategyProtocol",
    "StrategyContext",
    "StrategyRuntimeState",
    "TimeInForce",
    "TradeAction",
    "TradeActionType",
    "TradeSide",
    "TradeSnapshot",
    # Generic Trade Classes exports consolidated from trader
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

standardize_domain_exports(globals(), __all__, tool_category="trading")
