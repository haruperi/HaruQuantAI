# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Canonical trading library composing MQL5 trading proxies and facade.

Description:
    Provide the unified asynchronous strategy-facing interface for order execution,
    account monitoring, and position management over declared broker backends.
    Compose eight stateful trading proxies (Trade, AccountInfo, SymbolInfo,
    OrderInfo, HistoryOrderInfo, PositionInfo, DealInfo, TerminalInfo) and the master
    Trading facade over a shared TradingBackend. Per-object locks serialize calls,
    while atomic snapshot dataclasses eliminate temporal skew and IPC round-trips.

Purpose:
    FEAT-LIBS-TRADING: Unified MQL5 trading proxies and master execution facade.

Key Capabilities:
    - FR-TRADING-COMPOSITION: Compose eight trading classes over backend transport.
      Associated: `Trading`, `Trading.__aenter__()`, `Trading.__aexit__()`
      Logging: DEBUG lifecycle and composition attempts through repository logger.
    - FR-TRADING-MUTATION: Route order dispatch and validation primitives.
      Associated: `Trade.OrderSend()`, `Trade.OrderCheck()`, `Trade.__call__()`
      Logging: DEBUG invocation metadata emitted via TradingClass._call().
    - FR-TRADING-ACCOUNT-SNAPSHOT: Query atomic account state.
      Associated: `AccountInfo.AccountInfo()`, `AccountInfo.__call__()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().
    - FR-TRADING-TERMINAL-SNAPSHOT: Query terminal properties and connectivity.
      Associated: `TerminalInfo.TerminalInfo()`, `TerminalInfo.__call__()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().
    - FR-TRADING-SYMBOL-SNAPSHOT: Query symbol properties, rates, and market depth.
      Associated: `SymbolInfo.SymbolInfo()`, `SymbolInfo.MarketBookGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().
    - FR-TRADING-POSITIONS: Query open positions and ticket snapshots.
      Associated: `PositionInfo.PositionInfo()`, `PositionInfo.PositionsGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().
    - FR-TRADING-ORDERS: Query active pending orders and snapshots.
      Associated: `OrderInfo.OrderInfo()`, `OrderInfo.OrdersGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().
    - FR-TRADING-CONTRACTS-MODELS: Self-contained trading models, order requests,
      receipts, and snapshots.
      Associated: `TradeRequest`, `TradeResult`, `TradeCheckResult`, `Receipt`,
        `BridgeEvent`, `AccountSnapshot`, `TerminalSnapshot`, `SymbolSnapshot`,
        `PositionSnapshot`, `OrderSnapshot`, `DealSnapshot`.
      Logging: Pure numerical and scalar state dataclasses with zero logging overhead.

Python API Usage:
    ```python
    from app.services.libs.trading import (
        OrderType,
        TradeAction,
        TradeRequest,
        Trading,
    )

    async with Trading(backend) as trading:
        await trading.wait_connected(timeout=30)
        account = await trading.account.AccountInfo()
        symbol = await trading.symbol.SymbolInfo("EURUSD")
        req = TradeRequest(
            action=TradeAction.DEAL,
            symbol="EURUSD",
            volume=0.01,
            order_type=OrderType.BUY,
            price=symbol.ask,
        )
        res = await trading.trade.OrderSend(req)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from types import TracebackType
from typing import Any, Protocol, Self, runtime_checkable

from app.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "BOOK_TYPE_DESCRIPTIONS",
    "ORDER_FILLING_DESCRIPTIONS",
    "ORDER_TIME_DESCRIPTIONS",
    "ORDER_TYPE_DESCRIPTIONS",
    "AccountInfo",
    "AccountSnapshot",
    "AccountTradeMode",
    "BaseTradingClass",
    "BookInfo",
    "BookType",
    "BridgeEvent",
    "DealInfo",
    "DealSnapshot",
    "HistoryOrderInfo",
    "HistoryOrderSnapshot",
    "MarginMode",
    "MqlBookInfo",
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
]


class ReceiptStatus(StrEnum):
    """Lifecycle status for a queued or executed bridge command."""

    CREATED = "created"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


class TradeResolution(StrEnum):
    """Resolution classification for an executed trading command."""

    DISPATCHED = "dispatched"
    FILLED = "filled"
    PLACED = "placed"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class PropertyValue:
    """Container for a typed scalar property query result or failure."""

    ok: bool
    value: Any = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Receipt:
    """Immutable audit record tracking the lifecycle of an IPC command."""

    command_id: str
    object_id: str
    class_name: str
    method_name: str
    status: ReceiptStatus
    created_at: float
    sent_at: float | None = None
    acknowledged_at: float | None = None
    resolved_at: float | None = None
    native_request_id: int | None = None
    value: Any = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BridgeEvent:
    """Parsed asynchronous event dispatched from the MetaTrader 5 terminal EA."""

    event_type: str
    payload: Mapping[str, Any]
    command_id: str | None = None
    request_id: int | None = None


@runtime_checkable
class TradingBackend(Protocol):
    """Async execution capability consumed by trading and market data APIs."""

    async def start(self) -> None:
        """Backend capability: start."""
        ...

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109 -- backend deadline capability
        """Backend capability: wait connected."""
        ...

    async def close(self) -> None:
        """Backend capability: close."""
        ...

    def arm(self) -> None:
        """Backend capability: arm."""
        ...

    def disarm(self) -> None:
        """Backend capability: disarm."""
        ...

    def last_command_id(self) -> str | None:
        """Backend capability: last command id."""
        ...

    def receipt(self, command_id: str) -> Receipt | None:
        """Backend capability: receipt."""
        ...

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- backend deadline capability
        """Backend capability: next event."""
        ...

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> BridgeEvent:
        """Backend capability: await request event."""
        ...

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> Any:
        """Backend capability: call."""
        ...


class AccountTradeMode(IntEnum):
    """Account trading mode enumeration."""

    DEMO = 0
    CONTEST = 1
    REAL = 2


class StopoutMode(IntEnum):
    """Stopout mode calculation type enumeration."""

    PERCENT = 0
    MONEY = 1


class MarginMode(IntEnum):
    """Account margin calculation mode enumeration."""

    RETAIL_NETTING = 0
    EXCHANGE = 1
    RETAIL_HEDGING = 2


class OrderType(IntEnum):
    """Order type enumeration."""

    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BUY_STOP_LIMIT = 6
    SELL_STOP_LIMIT = 7
    CLOSE_BY = 8


class OrderFilling(IntEnum):
    """Order execution policy type enumeration."""

    FOK = 0
    IOC = 1
    RETURN = 2
    BOC = 3


class OrderTime(IntEnum):
    """Order expiration time type enumeration."""

    GTC = 0
    DAY = 1
    SPECIFIED = 2
    SPECIFIED_DAY = 3


class TradeAction(IntEnum):
    """Trade request action enumeration."""

    DEAL = 1
    PENDING = 5
    SLTP = 6
    MODIFY = 7
    REMOVE = 8
    CLOSE_BY = 10


class TradeRetcode(IntEnum):
    """Trade execution return code enumeration."""

    REQUOTE = 10004
    REJECT = 10006
    CANCEL = 10007
    PLACED = 10008
    DONE = 10009
    DONE_PARTIAL = 10010
    ERROR = 10011
    TIMEOUT = 10012
    INVALID = 10013
    INVALID_VOLUME = 10014
    INVALID_PRICE = 10015
    INVALID_STOPS = 10016
    TRADE_DISABLED = 10017
    MARKET_CLOSED = 10018
    NO_MONEY = 10019
    PRICE_CHANGED = 10020
    PRICE_OFF = 10021
    INVALID_EXPIRATION = 10022
    ORDER_CHANGED = 10023
    TOO_MANY_REQUESTS = 10024
    NO_CHANGES = 10025
    SERVER_DISABLES_AT = 10026
    CLIENT_DISABLES_AT = 10027
    LOCKED = 10028
    FROZEN = 10029
    INVALID_FILL = 10030
    CONNECTION = 10031
    ONLY_REAL = 10032
    LIMIT_ORDERS = 10033
    LIMIT_VOLUME = 10034
    INVALID_ORDER = 10035
    POSITION_CLOSED = 10036
    INVALID_CLOSE_VOLUME = 10038
    CLOSE_ORDER_EXIST = 10039
    LIMIT_POSITIONS = 10040
    REJECT_CANCEL = 10041
    LONG_ONLY = 10042
    SHORT_ONLY = 10043
    CLOSE_ONLY = 10044
    FIFO_CLOSE = 10045
    HEDGE_PROHIBITED = 10046


class BookType(IntEnum):
    """Order book entry type enumeration."""

    BOOK_TYPE_SELL = 1
    BOOK_TYPE_BUY = 2
    BOOK_TYPE_SELL_MARKET = 3
    BOOK_TYPE_BUY_MARKET = 4


ORDER_TYPE_DESCRIPTIONS: dict[OrderType, str] = {
    OrderType.BUY: "Buy",
    OrderType.SELL: "Sell",
    OrderType.BUY_LIMIT: "Buy Limit",
    OrderType.SELL_LIMIT: "Sell Limit",
    OrderType.BUY_STOP: "Buy Stop",
    OrderType.SELL_STOP: "Sell Stop",
    OrderType.BUY_STOP_LIMIT: "Buy Stop Limit",
    OrderType.SELL_STOP_LIMIT: "Sell Stop Limit",
    OrderType.CLOSE_BY: "Close By",
}

ORDER_FILLING_DESCRIPTIONS: dict[OrderFilling, str] = {
    OrderFilling.FOK: "Fill or Kill",
    OrderFilling.IOC: "Immediate or Cancel",
    OrderFilling.RETURN: "Return",
    OrderFilling.BOC: "Book or Cancel",
}

ORDER_TIME_DESCRIPTIONS: dict[OrderTime, str] = {
    OrderTime.GTC: "Good Till Cancelled",
    OrderTime.DAY: "Day",
    OrderTime.SPECIFIED: "Specified",
    OrderTime.SPECIFIED_DAY: "Specified Day",
}

BOOK_TYPE_DESCRIPTIONS: dict[BookType, str] = {
    BookType.BOOK_TYPE_SELL: "Sell",
    BookType.BOOK_TYPE_BUY: "Buy",
    BookType.BOOK_TYPE_SELL_MARKET: "Sell Market",
    BookType.BOOK_TYPE_BUY_MARKET: "Buy Market",
}


@dataclass(frozen=True, slots=True)
class BookInfo:
    """Market depth (DOM) entry matching MQL5 MqlBookInfo."""

    type: BookType
    price: float
    volume: int
    volume_real: float

    @property
    def type_description(self) -> str:
        """Human-readable order type description."""
        return BOOK_TYPE_DESCRIPTIONS.get(self.type, "Unknown")

    def _asdict(self) -> dict[str, Any]:
        """Convert entry to a dictionary matching Python MT5 BookInfo._asdict()."""
        return {
            "type": int(self.type),
            "price": self.price,
            "volume": self.volume,
            "volume_real": self.volume_real,
        }


MqlBookInfo = BookInfo


@dataclass(slots=True)
class AccountSnapshot:
    """Atomic snapshot of account balance, margin, leverage, and trading permissions."""

    login: int = 0
    trade_mode: AccountTradeMode = AccountTradeMode.DEMO
    leverage: int = 100
    stopout_mode: StopoutMode = StopoutMode.PERCENT
    margin_mode: MarginMode = MarginMode.RETAIL_HEDGING
    trade_allowed: bool = True
    trade_expert: bool = True
    limit_orders: int = 0
    balance: float = 10_000.0
    credit: float = 0.0
    profit: float = 0.0
    equity: float = 10_000.0
    margin: float = 0.0
    free_margin: float = 10_000.0
    margin_level: float = 0.0
    margin_call: float = 50.0
    margin_stop_out: float = 20.0
    name: str = "Simulation"
    server: str = "Simulation"
    currency: str = "USD"
    company: str = "HaruQuantAI"
    currency_digits: int = 2
    fifo_close: bool = False
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    assets: float = 0.0
    liabilities: float = 0.0
    commission_blocked: float = 0.0
    trade_mode_description: str = ""
    stopout_mode_description: str = ""
    margin_mode_description: str = ""


@dataclass(slots=True)
class TerminalSnapshot:
    """Atomic snapshot of terminal state, connectivity, paths, and platform metadata."""

    build: int = 0
    connected: bool = True
    dlls_allowed: bool = False
    trade_allowed: bool = True
    email_enabled: bool = False
    ftp_enabled: bool = False
    max_bars: int = 100_000
    code_page: int = 65001
    cpu_cores: int = 1
    memory_physical: int = 0
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    is_x64: bool = True
    opencl_support: int = 0
    disk_space: int = 0
    language: str = "English"
    name: str = "HaruQuantAI Simulator"
    company: str = "HaruQuantAI"
    path: str = ""
    data_path: str = ""
    common_data_path: str = ""
    community_account: bool = False
    community_connection: bool = False
    tradeapi_disabled: bool = False
    notifications_enabled: bool = False
    mqid: bool = False
    ping_last: int = 0
    community_balance: float = 0.0
    retransmission: float = 0.0


@dataclass(slots=True)
class SymbolSnapshot:
    """Atomic snapshot of symbol specification, execution modes, rates, and spreads."""

    name: str = ""
    custom: bool = False
    chart_mode: int = 0
    select: bool = True
    visible: bool = True
    session_deals: int = 0
    session_buy_orders: int = 0
    session_sell_orders: int = 0
    volume: int = 0
    volumehigh: int = 0
    volumelow: int = 0
    time: int = 0
    digits: int = 5
    spread: int = 0
    spread_float: bool = True
    ticks_bookdepth: int = 0
    trade_calc_mode: int = 0
    trade_calc_mode_description: str = ""
    trade_mode: int = 0
    trade_mode_description: str = ""
    start_time: int = 0
    expiration_time: int = 0
    trade_stops_level: int = 0
    trade_freeze_level: int = 0
    trade_exemode: int = 0
    trade_execution_description: str = ""
    swap_mode: int = 0
    swap_mode_description: str = ""
    swap_rollover3days: int = 3
    swap_rollover3days_description: str = ""
    margin_hedged_use_leg: bool = False
    expiration_mode: int = 7
    filling_mode: int = 1
    order_mode: int = 127
    order_gtc_mode: int = 0
    option_mode: int = 0
    option_right: int = 0
    bid: float = 0.0
    bidhigh: float = 0.0
    bidlow: float = 0.0
    ask: float = 0.0
    askhigh: float = 0.0
    asklow: float = 0.0
    last: float = 0.0
    lasthigh: float = 0.0
    lastlow: float = 0.0
    volume_real: float = 0.0
    volumehigh_real: float = 0.0
    volumelow_real: float = 0.0
    option_strike: float = 0.0
    point: float = 0.00001
    trade_tick_value: float = 1.0
    trade_tick_value_profit: float = 1.0
    trade_tick_value_loss: float = 1.0
    trade_tick_size: float = 0.00001
    trade_contract_size: float = 100_000.0
    trade_accrued_interest: float = 0.0
    trade_face_value: float = 0.0
    trade_liquidity_rate: float = 0.0
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    volume_limit: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    margin_long: float = 1.0
    margin_short: float = 1.0
    margin_limit: float = 1.0
    margin_stop: float = 1.0
    margin_stop_limit: float = 1.0
    trade_time_flags: int = 0
    trade_fill_flags: int = 3
    session_volume: float = 0.0
    session_turnover: float = 0.0
    session_interest: float = 0.0
    session_buy_orders_volume: float = 0.0
    session_sell_orders_volume: float = 0.0
    session_open: float = 0.0
    session_close: float = 0.0
    session_aw: float = 0.0
    session_price_settlement: float = 0.0
    session_price_limit_min: float = 0.0
    session_price_limit_max: float = 0.0
    margin_hedged: float = 0.0
    price_change: float = 0.0
    price_volatility: float = 0.0
    price_theoretical: float = 0.0
    price_greeks_delta: float = 0.0
    price_greeks_theta: float = 0.0
    price_greeks_gamma: float = 0.0
    price_greeks_vega: float = 0.0
    price_greeks_rho: float = 0.0
    price_greeks_omega: float = 0.0
    price_sensitivity: float = 0.0
    basis: str = ""
    category: str = ""
    currency_base: str = ""
    currency_profit: str = "USD"
    currency_margin: str = "USD"
    bank: str = ""
    description: str = ""
    exchange: str = ""
    formula: str = ""
    isin: str = ""
    page: str = ""
    path: str = ""

    @property
    def lots_min(self) -> float:
        """Alias for volume_min."""
        return self.volume_min

    @property
    def lots_max(self) -> float:
        """Alias for volume_max."""
        return self.volume_max

    @property
    def lots_step(self) -> float:
        """Alias for volume_step."""
        return self.volume_step

    @property
    def lots_limit(self) -> float:
        """Alias for volume_limit."""
        return self.volume_limit

    @property
    def tick_size(self) -> float:
        """Alias for trade_tick_size."""
        return self.trade_tick_size

    @property
    def tick_value(self) -> float:
        """Alias for trade_tick_value."""
        return self.trade_tick_value

    @property
    def contract_size(self) -> float:
        """Alias for trade_contract_size."""
        return self.trade_contract_size

    @property
    def stops_level(self) -> int:
        """Alias for trade_stops_level."""
        return self.trade_stops_level

    @property
    def freeze_level(self) -> int:
        """Alias for trade_freeze_level."""
        return self.trade_freeze_level


@dataclass(slots=True)
class PositionSnapshot:
    """Atomic snapshot of an open market position."""

    ticket: int = 0
    identifier: int = 0
    symbol: str = ""
    position_type: int = 0
    type_description: str = ""
    volume: float = 0.0
    price_open: float = 0.0
    price_current: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    magic: int = 0
    comment: str = ""
    time: int = 0
    time_msc: int = 0
    time_update: int = 0
    time_update_msc: int = 0

    @property
    def stop_loss(self) -> float:
        """Alias for sl."""
        return self.sl

    @property
    def take_profit(self) -> float:
        """Alias for tp."""
        return self.tp

    @property
    def type(self) -> int:
        """Alias for position_type."""
        return self.position_type


@dataclass(slots=True)
class OrderSnapshot:
    """Atomic snapshot of a pending or historical order."""

    ticket: int = 0
    symbol: str = ""
    order_type: int = 0
    type_description: str = ""
    state: int = 0
    state_description: str = ""
    volume_initial: float = 0.0
    volume_current: float = 0.0
    price_open: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    price_current: float = 0.0
    price_stop_limit: float = 0.0
    time_setup: int = 0
    time_setup_msc: int = 0
    time_done: int = 0
    time_done_msc: int = 0
    time_expiration: int = 0
    type_filling: int = 0
    type_filling_description: str = ""
    type_time: int = 0
    type_time_description: str = ""
    magic: int = 0
    position_id: int = 0
    comment: str = ""

    @property
    def stop_loss(self) -> float:
        """Alias for sl."""
        return self.sl

    @property
    def take_profit(self) -> float:
        """Alias for tp."""
        return self.tp

    @property
    def type(self) -> int:
        """Alias for order_type."""
        return self.order_type


HistoryOrderSnapshot = OrderSnapshot


@dataclass(slots=True)
class DealSnapshot:
    """Atomic snapshot of an executed trade deal."""

    ticket: int = 0
    order: int = 0
    position_id: int = 0
    symbol: str = ""
    deal_type: int = 0
    type_description: str = ""
    entry: int = 0
    entry_description: str = ""
    volume: float = 0.0
    price: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    magic: int = 0
    comment: str = ""
    time: int = 0
    time_msc: int = 0

    @property
    def order_ticket(self) -> int:
        """Alias for order."""
        return self.order

    @property
    def type(self) -> int:
        """Alias for deal_type."""
        return self.deal_type


@dataclass(slots=True)
class TradeRequest:
    """Execution order request specification."""

    action: TradeAction
    symbol: str = ""
    volume: float = 0.0
    order_type: OrderType = OrderType.BUY
    price: float = 0.0
    stoplimit: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    deviation: int = 0
    magic: int = 0
    order: int = 0
    position: int = 0
    position_by: int = 0
    type_filling: OrderFilling = OrderFilling.FOK
    type_time: OrderTime = OrderTime.GTC
    expiration: datetime | None = None
    comment: str = ""


@dataclass(slots=True)
class TradeResult:
    """Order dispatch execution outcome returned by Trade.OrderSend()."""

    retcode: int = int(TradeRetcode.ERROR)
    deal: int = 0
    order: int = 0
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""
    request_id: int = 0
    retcode_external: int = 0
    raw: Any = None


@dataclass(slots=True)
class TradeCheckResult:
    """Pre-trade verification outcome returned by Trade.OrderCheck()."""

    retcode: int = int(TradeRetcode.DONE)
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = "Done"
    raw: Any = None


logger = get_logger(__name__)


# ============================================================================
# Base Forwarding Proxy
# ============================================================================


class TradingClass:
    """Backend-neutral object identity and serialized async forwarding."""

    CLASS_NAME = "Base"
    TRADING_METHODS: frozenset[str] = frozenset()

    def __init__(
        self, backend: TradingBackend, *, object_id: str | None = None
    ) -> None:
        logger.debug("FR-TRADING-COMPOSITION: creating object")
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-TRADING-COMPOSITION: invoking backend",
            extra={"class_name": self.CLASS_NAME, "method_name": method},
        )
        wire_args: list[Any] = []
        for value in args:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    raise ValueError("trading datetimes must include a timezone")
                wire_args.append(int(value.timestamp()))
            else:
                wire_args.append(value)
        async with self._lock:
            return await self.backend.call(
                object_id=self.object_id,
                class_name=self.CLASS_NAME,
                method_name=method,
                args=wire_args,
                requires_arm=method in self.TRADING_METHODS,
            )

    async def _property(self, method: str, *args: Any) -> PropertyValue:
        value = await self._call(method, *args)
        if isinstance(value, dict) and {"ok", "value"} <= value.keys():
            return PropertyValue(
                ok=bool(value["ok"]),
                value=value.get("value"),
                error=value.get("error"),
            )
        return PropertyValue(ok=True, value=value)


BaseTradingClass = TradingClass


# ============================================================================
# AccountInfo Proxy
# ============================================================================


class AccountInfo(TradingClass):
    """Canonical asynchronous AccountInfo API."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot."""
        logger.debug("FR-TRADING-ACCOUNT-SNAPSHOT: querying account snapshot")
        data = await self._call("AccountInfo", *args)
        if isinstance(data, AccountSnapshot):
            return data
        if isinstance(data, dict):
            return AccountSnapshot(**data)
        raise TypeError(f"unexpected account snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot directly via call syntax."""
        return await self.AccountInfo(*args)

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.OrderProfitCheck operation."""
        return await self._call("OrderProfitCheck", *args)

    async def MarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCheck operation."""
        return await self._call("MarginCheck", *args)

    async def FreeMarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMarginCheck operation."""
        return await self._call("FreeMarginCheck", *args)

    async def MaxLotCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MaxLotCheck operation."""
        return await self._call("MaxLotCheck", *args)


# ============================================================================
# TerminalInfo Proxy
# ============================================================================


class TerminalInfo(TradingClass):
    """Canonical asynchronous TerminalInfo API."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot."""
        logger.debug("FR-TRADING-TERMINAL-SNAPSHOT: querying terminal snapshot")
        data = await self._call("TerminalInfo", *args)
        if isinstance(data, TerminalSnapshot):
            return data
        if isinstance(data, dict):
            return TerminalSnapshot(**data)
        raise TypeError(f"unexpected terminal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)


# ============================================================================
# SymbolInfo Proxy
# ============================================================================


class SymbolInfo(TradingClass):
    """Canonical asynchronous SymbolInfo API."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> SymbolSnapshot:
        """Await the backend SymbolInfo snapshot."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: querying symbol snapshot")
        data = await self._call("SymbolInfo", *args)
        if isinstance(data, SymbolSnapshot):
            return data
        if isinstance(data, dict):
            return SymbolSnapshot(**data)
        raise TypeError(f"unexpected symbol snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> SymbolSnapshot:
        """Await the backend SymbolInfo snapshot directly via call syntax."""
        return await self.SymbolInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend symbol snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, SymbolSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected symbol dictionary type: {type(data).__name__}")

    async def Refresh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Refresh operation."""
        return await self._call("Refresh", *args)

    async def RefreshRates(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.RefreshRates operation."""
        return await self._call("RefreshRates", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Name operation."""
        return await self._call("Name", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Select operation."""
        return await self._call("Select", *args)

    async def IsSynchronized(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.IsSynchronized operation."""
        return await self._call("IsSynchronized", *args)

    async def NormalizePrice(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.NormalizePrice operation."""
        return await self._call("NormalizePrice", *args)

    async def SymbolsTotal(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsTotal operation."""
        return await self._call("SymbolsTotal", *args)

    async def SymbolsGet(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsGet operation."""
        return await self._call("SymbolsGet", *args)

    async def SymbolInfoTick(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolInfoTick operation."""
        return await self._call("SymbolInfoTick", *args)

    async def SymbolSelect(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolSelect operation."""
        return await self._call("SymbolSelect", *args)

    async def MarketBookAdd(self, *args: Any) -> Any:
        """Subscribes the MetaTrader 5 terminal to Market Depth change events."""
        return await self._call("MarketBookAdd", *args)

    async def MarketBookGet(self, *args: Any) -> tuple[BookInfo, ...]:
        """Return a tuple of BookInfo featuring Market Depth entries for a symbol."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: reading market depth")
        raw = await self._call("MarketBookGet", *args)
        if not raw:
            return ()
        entries: list[BookInfo] = []
        for item in raw:
            if isinstance(item, BookInfo):
                entries.append(item)
            elif isinstance(item, dict):
                raw_vol = item.get("volume_real")
                if raw_vol is None:
                    raw_vol = item.get("volume", 0.0)
                entries.append(
                    BookInfo(
                        type=BookType(int(item.get("type", BookType.BOOK_TYPE_BUY))),
                        price=float(item.get("price", 0.0)),
                        volume=int(item.get("volume", 0)),
                        volume_real=float(raw_vol if raw_vol is not None else 0.0),
                    )
                )
        return tuple(entries)

    async def MarketBookRelease(self, *args: Any) -> Any:
        """Cancel subscription of terminal to Market Depth change events."""
        return await self._call("MarketBookRelease", *args)


# ============================================================================
# PositionInfo Proxy
# ============================================================================


class PositionInfo(TradingClass):
    """Canonical asynchronous PositionInfo API."""

    CLASS_NAME = "PositionInfo"

    async def PositionInfo(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot."""
        logger.debug("FR-TRADING-POSITIONS: querying position snapshot")
        data = await self._call("PositionInfo", *args)
        if isinstance(data, PositionSnapshot):
            return data
        if isinstance(data, dict):
            return PositionSnapshot(**data)
        raise TypeError(f"unexpected position snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, PositionSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected position dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def SelectByMagic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByMagic operation."""
        return await self._call("SelectByMagic", *args)

    async def SelectByTicket(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByTicket operation."""
        return await self._call("SelectByTicket", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def PositionsTotal(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionsTotal operation."""
        return await self._call("PositionsTotal", *args)

    async def PositionsGet(self, *args: Any, **kwargs: Any) -> list[PositionSnapshot]:
        """Await the backend PositionInfo.PositionsGet operation."""
        logger.debug("FR-TRADING-POSITIONS: querying positions collection")
        data = (
            await self._call("PositionsGet", kwargs)
            if kwargs
            else await self._call("PositionsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, PositionSnapshot) else PositionSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected PositionsGet return type: {type(data).__name__}")


# ============================================================================
# OrderInfo Proxy
# ============================================================================


class OrderInfo(TradingClass):
    """Canonical asynchronous OrderInfo API."""

    CLASS_NAME = "OrderInfo"

    async def OrderInfo(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot."""
        logger.debug("FR-TRADING-ORDERS: querying order snapshot")
        data = await self._call("OrderInfo", *args)
        if isinstance(data, OrderSnapshot):
            return data
        if isinstance(data, dict):
            return OrderSnapshot(**data)
        raise TypeError(f"unexpected order snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot directly via call syntax."""
        return await self.OrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, OrderSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected order dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend OrderInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend OrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def OrdersTotal(self, *args: Any) -> Any:
        """Await the backend OrderInfo.OrdersTotal operation."""
        return await self._call("OrdersTotal", *args)

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[OrderSnapshot]:
        """Await the backend OrderInfo.OrdersGet operation."""
        logger.debug("FR-TRADING-ORDERS: querying orders collection")
        data = (
            await self._call("OrdersGet", kwargs)
            if kwargs
            else await self._call("OrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, OrderSnapshot) else OrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected OrdersGet return type: {type(data).__name__}")


# ============================================================================
# HistoryOrderInfo Proxy
# ============================================================================


class HistoryOrderInfo(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API."""

    CLASS_NAME = "HistoryOrderInfo"

    async def HistoryOrderInfo(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying history order snapshot")
        data = await self._call("HistoryOrderInfo", *args)
        if isinstance(data, HistoryOrderSnapshot):
            return data
        if isinstance(data, dict):
            return HistoryOrderSnapshot(**data)
        raise TypeError(
            f"unexpected history order snapshot type: {type(data).__name__}"
        )

    async def __call__(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, HistoryOrderSnapshot):
            return asdict(data)
        raise TypeError(
            f"unexpected history order dictionary type: {type(data).__name__}"
        )

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryOrdersTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend HistoryOrderInfo.HistoryOrdersTotal operation."""
        if kwargs:
            return await self._call("HistoryOrdersTotal", kwargs)
        return await self._call("HistoryOrdersTotal", *args)

    async def HistoryOrdersGet(
        self, *args: Any, **kwargs: Any
    ) -> list[HistoryOrderSnapshot]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history orders collection")
        data = (
            await self._call("HistoryOrdersGet", kwargs)
            if kwargs
            else await self._call("HistoryOrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, HistoryOrderSnapshot)
                else HistoryOrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryOrdersGet return type: {type(data).__name__}"
        )


# ============================================================================
# DealInfo Proxy
# ============================================================================


class DealInfo(TradingClass):
    """Canonical asynchronous DealInfo API."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying deal snapshot")
        data = await self._call("DealInfo", *args)
        if isinstance(data, DealSnapshot):
            return data
        if isinstance(data, dict):
            return DealSnapshot(**data)
        raise TypeError(f"unexpected deal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, DealSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected deal dictionary type: {type(data).__name__}")

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryDealsTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend DealInfo.HistoryDealsTotal operation."""
        if kwargs:
            return await self._call("HistoryDealsTotal", kwargs)
        return await self._call("HistoryDealsTotal", *args)

    async def HistoryDealsGet(self, *args: Any, **kwargs: Any) -> list[DealSnapshot]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history deals collection")
        data = (
            await self._call("HistoryDealsGet", kwargs)
            if kwargs
            else await self._call("HistoryDealsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, DealSnapshot) else DealSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryDealsGet return type: {type(data).__name__}"
        )


# ============================================================================
# Trade Execution Proxy & Request/Result Builders
# ============================================================================


def _serialize_dict_request(req: dict[str, Any]) -> dict[str, Any]:
    data = dict(req)
    for key in ("action", "order_type", "type_filling", "type_time"):
        if key in data and hasattr(data[key], "value"):
            data[key] = int(data[key].value)
    exp = data.get("expiration")
    if isinstance(exp, datetime):
        if exp.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        data["expiration"] = int(exp.timestamp())
    return data


def _serialize_request(req: TradeRequest | dict[str, Any]) -> dict[str, Any]:
    """Serialize a TradeRequest or dictionary to wire-compatible dictionary."""
    if isinstance(req, TradeRequest):
        data: dict[str, Any] = {
            "action": int(req.action),
            "symbol": req.symbol,
            "volume": float(req.volume),
            "order_type": int(req.order_type),
            "price": float(req.price),
            "stoplimit": float(req.stoplimit),
            "sl": float(req.sl),
            "tp": float(req.tp),
            "deviation": req.deviation,
            "magic": req.magic,
            "order": req.order,
            "position": req.position,
            "position_by": req.position_by,
            "type_filling": int(req.type_filling),
            "type_time": int(req.type_time),
            "comment": req.comment,
        }
        if req.expiration is not None:
            if req.expiration.tzinfo is None:
                raise ValueError("trading datetimes must include a timezone")
            data["expiration"] = int(req.expiration.timestamp())
        return data
    return _serialize_dict_request(req)


def _build_trade_request(data: dict[str, Any]) -> TradeRequest:
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        action_val
        if isinstance(action_val, TradeAction)
        else TradeAction(int(action_val))
    )
    order_type_val = data.get("type", data.get("order_type", OrderType.BUY))
    order_type = (
        order_type_val
        if isinstance(order_type_val, OrderType)
        else OrderType(int(order_type_val))
    )
    filling_val = data.get("type_filling", OrderFilling.FOK)
    filling = (
        filling_val
        if isinstance(filling_val, OrderFilling)
        else OrderFilling(int(filling_val))
    )
    time_val = data.get("type_time", OrderTime.GTC)
    type_time = (
        time_val if isinstance(time_val, OrderTime) else OrderTime(int(time_val))
    )

    exp_val = data.get("expiration")
    expiration: datetime | None = None
    if isinstance(exp_val, datetime):
        expiration = exp_val
    elif isinstance(exp_val, (int, float)) and exp_val > 0:
        expiration = datetime.fromtimestamp(exp_val, tz=UTC)

    return TradeRequest(
        action=action,
        magic=int(data.get("magic", 0)),
        order=int(data.get("order", 0)),
        symbol=str(data.get("symbol", "")),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=int(data.get("deviation", 0)),
        order_type=order_type,
        type_filling=filling,
        type_time=type_time,
        expiration=expiration,
        comment=str(data.get("comment", "")),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
    )


def _build_trade_result(data: dict[str, Any]) -> TradeResult:
    return TradeResult(
        retcode=int(data.get("retcode", int(TradeRetcode.ERROR))),
        deal=int(data.get("deal", 0)),
        order=int(data.get("order", 0)),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        bid=float(data.get("bid", 0.0)),
        ask=float(data.get("ask", 0.0)),
        comment=str(data.get("comment", "")),
        request_id=int(data.get("request_id", 0)),
        retcode_external=int(data.get("retcode_external", 0)),
        raw=data.get("raw", data),
    )


def _build_trade_check_result(data: dict[str, Any]) -> TradeCheckResult:
    return TradeCheckResult(
        retcode=int(data.get("retcode", int(TradeRetcode.DONE))),
        balance=float(data.get("balance", 0.0)),
        equity=float(data.get("equity", 0.0)),
        profit=float(data.get("profit", 0.0)),
        margin=float(data.get("margin", 0.0)),
        margin_free=float(data.get("margin_free", 0.0)),
        margin_level=float(data.get("margin_level", 0.0)),
        comment=str(data.get("comment", "")),
        raw=data.get("raw", data),
    )


class Trade(TradingClass):
    """Canonical asynchronous Trade API conforming to standard MQL5 CTrade."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset({"OrderSend"})

    async def LogLevel(self, log_level: int) -> bool:
        """Set logging verbosity on the trade execution context."""
        return bool(await self._call("LogLevel", log_level))

    async def SetExpertMagicNumber(self, magic: int) -> None:
        """Set default magic number for subsequent orders."""
        await self._call("SetExpertMagicNumber", magic)

    async def SetDeviationInPoints(self, deviation: int) -> None:
        """Set default slippage deviation in points for market orders."""
        await self._call("SetDeviationInPoints", deviation)

    async def SetTypeFilling(self, filling: OrderFilling | int) -> None:
        """Set default order filling execution policy."""
        val = filling.value if isinstance(filling, OrderFilling) else filling
        await self._call("SetTypeFilling", val)

    async def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        """Resolve and set the most appropriate filling mode supported by symbol."""
        return bool(await self._call("SetTypeFillingBySymbol", symbol))

    async def SetAsyncMode(self, mode: bool) -> None:
        """Enable or disable asynchronous order sending mode."""
        await self._call("SetAsyncMode", mode)

    async def SetMarginMode(self) -> None:
        """Recalculate margin mode based on account and connected broker terminal."""
        await self._call("SetMarginMode")

    async def OrderSend(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Send a trade request to the broker terminal."""
        logger.debug("FR-TRADING-MUTATION: executing OrderSend")
        wire_payload = _serialize_request(request)
        raw = await self._call("OrderSend", wire_payload)
        data = raw if isinstance(raw, dict) else {}
        res = _build_trade_result(data)
        if result is not None:
            for k, v in asdict(res).items():
                if hasattr(result, k):
                    setattr(result, k, v)
        return res

    async def OrderCheck(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeCheckResult | None = None,
    ) -> TradeCheckResult:
        """Validate an order request and calculate required margin and profit."""
        logger.debug("FR-TRADING-MUTATION: executing OrderCheck")
        wire_payload = _serialize_request(request)
        raw = await self._call("OrderCheck", wire_payload)
        data = raw if isinstance(raw, dict) else {}
        res = _build_trade_check_result(data)
        if result is not None:
            for k, v in asdict(res).items():
                if hasattr(result, k):
                    setattr(result, k, v)
        return res

    async def __call__(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Forward directly to OrderSend."""
        return await self.OrderSend(request, result)

    async def Request(self) -> TradeRequest:
        """Fetch the last trade request snapshot."""
        raw = await self._call("Request")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_request(data)

    async def Result(self) -> TradeResult:
        """Fetch the last trade result snapshot."""
        raw = await self._call("Result")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_result(data)

    async def CheckResult(self) -> TradeCheckResult:
        """Fetch the last trade check result snapshot."""
        raw = await self._call("CheckResult")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_check_result(data)

    async def PrintRequest(self) -> bool:
        """Log the last trade request metadata."""
        return bool(await self._call("PrintRequest"))

    async def PrintResult(self) -> bool:
        """Log the last trade result metadata."""
        return bool(await self._call("PrintResult"))

    async def FormatRequest(self) -> str:
        """Format the last trade request as a text string."""
        return str(await self._call("FormatRequest"))

    async def FormatRequestResult(self) -> str:
        """Format the last trade request and result as a text string."""
        return str(await self._call("FormatRequestResult"))


# ============================================================================
# Master Trading Facade
# ============================================================================


class Trading:
    """The unified eight-class composition for every async trading backend."""

    def __init__(self, backend: TradingBackend) -> None:
        logger.debug("FR-TRADING-COMPOSITION: composing trading classes")
        self.backend = backend
        self.trade = Trade(backend)
        self.account = AccountInfo(backend)
        self.symbol = SymbolInfo(backend)
        self.order = OrderInfo(backend)
        self.history_order = HistoryOrderInfo(backend)
        self.position = PositionInfo(backend)
        self.deal = DealInfo(backend)
        self.terminal = TerminalInfo(backend)

    async def start(self) -> None:
        """Start the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: starting backend")
        await self.backend.start()

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Wait for backend readiness."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for backend")
        await self.backend.wait_connected(timeout)

    def arm(self) -> None:
        """Permit mutation operations on the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: arming backend")
        self.backend.arm()

    def disarm(self) -> None:
        """Revoke mutation permission."""
        logger.debug("FR-TRADING-COMPOSITION: disarming backend")
        self.backend.disarm()

    async def close(self) -> None:
        """Close the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: closing backend")
        await self.backend.close()

    def last_command_id(self) -> str | None:
        """Read the current task's last backend command identifier."""
        logger.debug("FR-TRADING-COMPOSITION: reading command identity")
        return self.backend.last_command_id()

    def receipt(self, command_id: str) -> Receipt | None:
        """Read a backend command receipt."""
        logger.debug("FR-TRADING-COMPOSITION: reading receipt")
        return self.backend.receipt(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Wait for a backend event within the requested timeout."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for event")
        return await self.backend.next_event(timeout)

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Delegate supported request correlation, or surface capability failure."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for correlated event")
        return await self.backend.await_request_event(request_id, timeout)

    async def __aenter__(self) -> Self:
        """Start the selected backend on context entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the selected backend on context exit."""
        await self.close()
