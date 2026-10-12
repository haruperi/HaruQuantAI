"""Shared broker command, event, result and error contracts.
MT5-compatible enumerations used by the shared broker API.



Description:
    Defines immutable receipts, property results, command statuses, events and
    failure metadata and immutable historical bars/ticks for broker services.
    The current MT5 transport and shared
    proxies consume these models; future backends can adopt the same records.
    These declarations perform no transport, persistence or logging setup.

    The numeric values intentionally mirror the commonly used MetaTrader 5 constants
    where practical so the MT5 backend can forward values without another translation
    layer. Simulation uses the same enums to keep semantics aligned with production.

Purpose:
    FEAT-BROKER-CONTRACTS: Establish shared broker model ownership while
    preserving the existing field, enum and exception contracts.

Key Capabilities:
    - FR-BROKER-CONTRACTS-RECORDS: Describe receipts, properties and broker events.
      Associated: `Receipt`, `PropertyValue`, `BridgeEvent`, `ReceiptStatus`,
        `TradeResolution`, `BridgeArg`, `Timeframe`, `MarketBar`, `MarketTick`
      Logging: Passive model declarations; operational logging belongs to the
        consuming transport and journal, not model construction.
    - FR-BROKER-CONTRACTS-ERRORS: Carry failure code and outcome uncertainty.
      Associated: `BridgeError`
      Logging: Consumers log operation metadata without secret-bearing messages.

Python API Usage:
    ```python
    from app.services.brokers.contracts import Receipt, ReceiptStatus, Timeframe

    status = ReceiptStatus.CREATED
    timeframe = Timeframe.PERIOD_H1
    ```

CLI Usage:
    uv run pytest tests/unit/services/test_broker_contracts.py --no-cov
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any, Protocol

BridgeArg = str | int | float | bool | None | Mapping[str, Any] | list[Any]


# ****************************************************************************
#                               HELPERS
# ****************************************************************************


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def epoch_seconds(value: datetime | None) -> int:
    if value is None:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def epoch_millis(value: datetime | None) -> int:
    if value is None:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


# ****************************************************************************
#
# ****************************************************************************


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


class BridgeError(RuntimeError):
    """Base runtime exception for MetaTrader 5 IPC bridge failures."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "BRIDGE_ERROR",
        command_id: str | None = None,
        uncertain: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.command_id = command_id
        self.uncertain = uncertain


# ****************************************************************************
#                              ENUMERATIONS
# ****************************************************************************


class Timeframe(StrEnum):
    """Chart and series timeframe enumeration."""

    PERIOD_CURRENT = "CURRENT"
    PERIOD_M1 = "M1"
    PERIOD_M2 = "M2"
    PERIOD_M3 = "M3"
    PERIOD_M4 = "M4"
    PERIOD_M5 = "M5"
    PERIOD_M6 = "M6"
    PERIOD_M10 = "M10"
    PERIOD_M12 = "M12"
    PERIOD_M15 = "M15"
    PERIOD_M20 = "M20"
    PERIOD_M30 = "M30"
    PERIOD_H1 = "H1"
    PERIOD_H2 = "H2"
    PERIOD_H3 = "H3"
    PERIOD_H4 = "H4"
    PERIOD_H6 = "H6"
    PERIOD_H8 = "H8"
    PERIOD_H12 = "H12"
    PERIOD_D1 = "D1"
    PERIOD_W1 = "W1"
    PERIOD_MN1 = "MN1"


class AccountTradeMode(IntEnum):
    DEMO = 0
    CONTEST = 1
    REAL = 2


class StopoutMode(IntEnum):
    PERCENT = 0
    MONEY = 1


class MarginMode(IntEnum):
    RETAIL_NETTING = 0
    EXCHANGE = 1
    RETAIL_HEDGING = 2


class OrderType(IntEnum):
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BUY_STOP_LIMIT = 6
    SELL_STOP_LIMIT = 7
    CLOSE_BY = 8


class PositionType(IntEnum):
    BUY = 0
    SELL = 1


class OrderFilling(IntEnum):
    FOK = 0
    IOC = 1
    RETURN = 2
    BOC = 3


class OrderTime(IntEnum):
    GTC = 0
    DAY = 1
    SPECIFIED = 2
    SPECIFIED_DAY = 3


class OrderState(IntEnum):
    STARTED = 0
    PLACED = 1
    CANCELED = 2
    PARTIAL = 3
    FILLED = 4
    REJECTED = 5
    EXPIRED = 6
    REQUEST_ADD = 7
    REQUEST_MODIFY = 8
    REQUEST_CANCEL = 9


class DealType(IntEnum):
    BUY = 0
    SELL = 1
    BALANCE = 2
    CREDIT = 3
    CHARGE = 4
    CORRECTION = 5
    BONUS = 6
    COMMISSION = 7
    COMMISSION_DAILY = 8
    COMMISSION_MONTHLY = 9
    COMMISSION_AGENT_DAILY = 10
    COMMISSION_AGENT_MONTHLY = 11
    INTEREST = 12
    BUY_CANCELED = 13
    SELL_CANCELED = 14
    DIVIDEND = 15
    DIVIDEND_FRANKED = 16
    TAX = 17


class DealEntry(IntEnum):
    IN = 0
    OUT = 1
    INOUT = 2
    OUT_BY = 3


class TradeAction(IntEnum):
    DEAL = 1
    PENDING = 5
    SLTP = 6
    MODIFY = 7
    REMOVE = 8
    CLOSE_BY = 10


class SymbolTradeMode(IntEnum):
    DISABLED = 0
    LONGONLY = 1
    SHORTONLY = 2
    CLOSEONLY = 3
    FULL = 4


class SymbolTradeExecution(IntEnum):
    REQUEST = 0
    INSTANT = 1
    MARKET = 2
    EXCHANGE = 3


class SymbolSwapMode(IntEnum):
    DISABLED = 0
    POINTS = 1
    CURRENCY_SYMBOL = 2
    CURRENCY_MARGIN = 3
    CURRENCY_DEPOSIT = 4
    INTEREST_CURRENT = 5
    INTEREST_OPEN = 6
    REOPEN_CURRENT = 7
    REOPEN_BID = 8


class SymbolCalcMode(IntEnum):
    FOREX = 0
    FOREX_NO_LEVERAGE = 1
    FUTURES = 2
    CFD = 3
    CFDINDEX = 4
    CFDLEVERAGE = 5
    EXCH_STOCKS = 32
    EXCH_FUTURES = 33


class TradeRetcode(IntEnum):
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


ORDER_TYPE_DESCRIPTIONS = {
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

POSITION_TYPE_DESCRIPTIONS = {
    PositionType.BUY: "Buy",
    PositionType.SELL: "Sell",
}

ORDER_FILLING_DESCRIPTIONS = {
    OrderFilling.FOK: "Fill or Kill",
    OrderFilling.IOC: "Immediate or Cancel",
    OrderFilling.RETURN: "Return",
    OrderFilling.BOC: "Book or Cancel",
}

ORDER_TIME_DESCRIPTIONS = {
    OrderTime.GTC: "Good Till Cancelled",
    OrderTime.DAY: "Day",
    OrderTime.SPECIFIED: "Specified",
    OrderTime.SPECIFIED_DAY: "Specified Day",
}

ORDER_STATE_DESCRIPTIONS = {
    item: item.name.replace("_", " ").title() for item in OrderState
}
DEAL_TYPE_DESCRIPTIONS = {
    item: item.name.replace("_", " ").title() for item in DealType
}
DEAL_ENTRY_DESCRIPTIONS = {
    item: item.name.replace("_", " ").title() for item in DealEntry
}


# ****************************************************************************
#                              DATA STRUCTURES
# ****************************************************************************


@dataclass(frozen=True, slots=True)
class MarketBar:
    """Historical OHLC bar with its UTC opening time in epoch seconds."""

    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


@dataclass(frozen=True, slots=True)
class MarketTick:
    """Historical tick retaining UTC epoch milliseconds and native flags."""

    time_msc: int
    bid: float
    ask: float
    last: float
    volume: int
    flags: int
    volume_real: float


@dataclass(slots=True)
class Tick:
    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float = 0.0
    volume: float = 0.0


@dataclass(slots=True)
class SymbolSpec:
    name: str
    digits: int = 5
    point: float = 0.00001
    spread: int = 0
    spread_float: bool = True
    ticks_book_depth: int = 0
    stops_level: int = 0
    freeze_level: int = 0
    trade_calc_mode: SymbolCalcMode = SymbolCalcMode.FOREX
    trade_mode: SymbolTradeMode = SymbolTradeMode.FULL
    trade_execution: SymbolTradeExecution = SymbolTradeExecution.MARKET
    swap_mode: SymbolSwapMode = SymbolSwapMode.POINTS
    swap_rollover3days: int = 3
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    margin_long: float = 1.0
    margin_short: float = 1.0
    margin_limit: float = 1.0
    margin_stop: float = 1.0
    margin_stop_limit: float = 1.0
    trade_time_flags: int = 0
    trade_fill_flags: int = 3
    tick_value: float = 1.0
    tick_value_profit: float = 1.0
    tick_value_loss: float = 1.0
    tick_size: float = 0.00001
    contract_size: float = 100_000.0
    lots_min: float = 0.01
    lots_max: float = 100.0
    lots_step: float = 0.01
    lots_limit: float = 0.0
    swap_long: float = 0.0
    swap_short: float = 0.0
    currency_base: str = ""
    currency_profit: str = "USD"
    currency_margin: str = "USD"
    bank: str = ""
    description: str = ""
    path: str = ""
    selected: bool = True
    synchronized: bool = True
    session_deals: int = 0
    session_buy_orders: int = 0
    session_sell_orders: int = 0
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


@dataclass(slots=True)
class AccountSnapshot:
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


@dataclass(slots=True)
class TerminalSnapshot:
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
class OrderRecord:
    ticket: int
    symbol: str
    order_type: OrderType
    state: OrderState
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float = 0.0
    tp: float = 0.0
    price_current: float = 0.0
    price_stop_limit: float = 0.0
    time_setup: datetime = field(default_factory=utc_now)
    time_done: datetime | None = None
    time_expiration: datetime | None = None
    type_filling: OrderFilling = OrderFilling.FOK
    type_time: OrderTime = OrderTime.GTC
    magic: int = 0
    position_id: int = 0
    comment: str = ""


@dataclass(slots=True)
class PositionRecord:
    ticket: int
    identifier: int
    symbol: str
    position_type: PositionType
    volume: float
    price_open: float
    price_current: float
    sl: float = 0.0
    tp: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    time: datetime = field(default_factory=utc_now)
    time_update: datetime = field(default_factory=utc_now)
    magic: int = 0
    comment: str = ""


@dataclass(slots=True)
class DealRecord:
    ticket: int
    order: int
    position_id: int
    symbol: str
    deal_type: DealType
    entry: DealEntry
    volume: float
    price: float
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    time: datetime = field(default_factory=utc_now)
    magic: int = 0
    comment: str = ""


@dataclass(slots=True)
class TradeRequest:
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
    retcode: int = int(TradeRetcode.DONE)
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = "Done"
    raw: Any = None


# ****************************************************************************
#           Low-level backend contract used by the eight MQL5-compatible public classes.
# ****************************************************************************


class BrokerBackend(ABC):
    """Backend contract.

    Internal synchronous snapshot-model capability used by local simulation
    handlers and the legacy adapter. Strategy code uses the separate async
    TradingBackend protocol through the canonical eight trading classes.
    """

    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def terminal(self) -> TerminalSnapshot: ...

    @abstractmethod
    def account(self) -> AccountSnapshot: ...

    @abstractmethod
    def symbol(self, name: str) -> SymbolSpec | None: ...

    @abstractmethod
    def select_symbol(self, name: str, selected: bool) -> bool: ...

    @abstractmethod
    def tick(self, name: str) -> Tick | None: ...

    @abstractmethod
    def orders(self) -> list[OrderRecord]: ...

    @abstractmethod
    def history_orders(self) -> list[OrderRecord]: ...

    @abstractmethod
    def positions(self) -> list[PositionRecord]: ...

    @abstractmethod
    def deals(self) -> list[DealRecord]: ...

    @abstractmethod
    def order_check(self, request: TradeRequest) -> TradeCheckResult: ...

    @abstractmethod
    def order_send(self, request: TradeRequest) -> TradeResult: ...

    @abstractmethod
    def order_calc_profit(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float: ...

    @abstractmethod
    def order_calc_margin(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price: float,
    ) -> float: ...

    def info_value(
        self,
        scope: str,
        property_id: int | str,
        selector: str | int | None = None,
    ) -> Any:
        """Optional generic property lookup used by Info* methods."""
        return None

    def set_clock(self, now: datetime) -> None:
        """Optional simulator clock hook."""
        del now


class TradingBackend(Protocol):
    """Async execution capability consumed by the canonical trading API."""

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
