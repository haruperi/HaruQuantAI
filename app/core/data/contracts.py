"""Domain value objects and contracts for accounts, symbols, orders, and deals."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np

from app.core.enums import (
    AccountTradeMode,
    BookType,
    DealEntry,
    DealType,
    MarginMode,
    OrderFilling,
    OrderState,
    OrderTime,
    OrderType,
    PositionType,
    ReceiptStatus,
    StopoutMode,
    SymbolCalcMode,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    Timeframe,
    TradeAction,
)

# fmt: off

_COMMISSION_NOT_RETRIEVED = (
    '{"version":2,"source":"unknown","status":"not_retrieved","rules":null}'
)

MAX_RECORDS: int = 1000
MAX_POSITION: int = 2**31 - 1
READ_TIMEOUT: float = 60.0

def _enum_titles(enum_cls: Any) -> dict[Any, str]:
    """Build title-cased description mapping for an enum class."""
    return {item: item.name.replace("_", " ").title() for item in enum_cls}

ORDER_TYPE_DESCRIPTIONS: dict[OrderType, str] = _enum_titles(OrderType)
POSITION_TYPE_DESCRIPTIONS: dict[PositionType, str] = _enum_titles(PositionType)
ORDER_STATE_DESCRIPTIONS: dict[OrderState, str] = _enum_titles(OrderState)
DEAL_TYPE_DESCRIPTIONS: dict[DealType, str] = _enum_titles(DealType)
DEAL_ENTRY_DESCRIPTIONS: dict[DealEntry, str] = _enum_titles(DealEntry)
SYMBOL_TRADE_MODE_DESCRIPTIONS: dict[SymbolTradeMode, str] = (
    _enum_titles(SymbolTradeMode)
)
SYMBOL_TRADE_EXECUTION_DESCRIPTIONS: dict[SymbolTradeExecution, str] = (
    _enum_titles(SymbolTradeExecution)
)
SYMBOL_SWAP_MODE_DESCRIPTIONS: dict[SymbolSwapMode, str] = _enum_titles(SymbolSwapMode)
SYMBOL_CALC_MODE_DESCRIPTIONS: dict[SymbolCalcMode, str] = _enum_titles(SymbolCalcMode)
ORDER_FILLING_DESCRIPTIONS: dict[OrderFilling, str] = {
    OrderFilling.FOK: "Fill or Kill", OrderFilling.IOC: "Immediate or Cancel",
    OrderFilling.RETURN: "Return", OrderFilling.BOC: "Book or Cancel",
}
ORDER_TIME_DESCRIPTIONS: dict[OrderTime, str] = {
    OrderTime.GTC: "Good Till Cancelled", OrderTime.DAY: "Day",
    OrderTime.SPECIFIED: "Specified", OrderTime.SPECIFIED_DAY: "Specified Day",
}
BOOK_TYPE_DESCRIPTIONS: dict[BookType, str] = {
    BookType.BOOK_TYPE_SELL: "Sell", BookType.BOOK_TYPE_BUY: "Buy",
    BookType.BOOK_TYPE_SELL_MARKET: "Sell Market",
    BookType.BOOK_TYPE_BUY_MARKET: "Buy Market",
}
TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    f: f.to_seconds() for f in Timeframe if f != Timeframe.PERIOD_CURRENT
}
class BridgeError(RuntimeError):
    """Base runtime exception for broker and market data bridge operations."""
    def __init__(
        self, message: str, *, code: str = "BRIDGE_ERROR",
        command_id: str | None = None, uncertain: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.command_id = command_id
        self.uncertain = uncertain
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
    """Parsed asynchronous event dispatched from the trading bridge."""
    event_type: str
    payload: Mapping[str, Any]
    command_id: str | None = None
    request_id: int | None = None
@runtime_checkable
class TradingBackend(Protocol):
    """Async execution capability consumed by trading and market data APIs."""
    async def start(self) -> None:
        """Backend capability: start."""
    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Backend capability: wait connected."""
    async def close(self) -> None:
        """Backend capability: close."""
    def arm(self) -> None:
        """Backend capability: arm."""
    def disarm(self) -> None:
        """Backend capability: disarm."""
    def last_command_id(self) -> str | None:
        """Backend capability: last command id."""
    def receipt(self, command_id: str) -> Receipt | None:
        """Backend capability: receipt."""
    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Backend capability: next event."""
    async def await_request_event(
        self, request_id: int, timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Backend capability: await request event."""
    async def call(
        self, *, object_id: str, class_name: str, method_name: str,
        args: list[Any], requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> Any:
        """Backend capability: call."""
@dataclass(frozen=True, slots=True)
class BookInfo:
    """Market depth (DOM) book entry."""
    type: BookType
    price: float
    volume: int
    volume_real: float
    def _asdict(self) -> dict[str, Any]:
        """Convert entry to a dictionary."""
        return {**asdict(self), "type": int(self.type)}
@dataclass(frozen=True, slots=True)
class MarketBar:
    """Historical OHLC bar with its opening time in epoch seconds."""
    time: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: int = 0
    real_volume: int = 0
    def is_bullish(self) -> bool:
        """Check if candle closed higher than open."""
        return self.close > self.open
    def is_bearish(self) -> bool:
        """Check if candle closed lower than open."""
        return self.close < self.open
    def is_doji(self) -> bool:
        """Check if candle closed at open."""
        return self.close == self.open
    def range(self) -> float:
        """Calculate total bar price range (High - Low)."""
        return self.high - self.low
    def body(self) -> float:
        """Calculate candle body size abs(Close - Open)."""
        return abs(self.close - self.open)
    def volume(self) -> float:
        """Calculate primary volume (real_volume if present, else tick_volume)."""
        return float(self.real_volume or self.tick_volume)
@dataclass(frozen=True, slots=True)
class MarketTick:
    """Historical tick retaining epoch milliseconds and native flags."""
    time_msc: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 0
    flags: int = 0
    volume_real: float = 0.0
    def spread(self) -> float:
        """Calculate instantaneous spread (Ask - Bid)."""
        return self.ask - self.bid
    def mid(self) -> float:
        """Calculate midpoint price."""
        return (self.ask + self.bid) / 2.0
@dataclass(slots=True)
class AccountInfo:
    """Atomic state of account balance, margin, leverage, and trading permissions."""
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
class TerminalInfo:
    """Atomic state of terminal connectivity, paths, and platform metadata."""
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

# --- SymbolInfo data structures ---
@dataclass(slots=True)
class SymbolSpread:
    """Spread configuration and default points."""

    floating: bool = True
    default: float = 0.0
    slippage: float = 0.0


@dataclass(slots=True)
class SymbolMargin:
    """Margin calculation currencies and requirements."""

    currency_base: str = ""
    currency_profit: str = ""
    currency_margin: str = ""
    initial: float = 100_000.0
    maintenance: float = 0.0
    hedged: float = 0.0
    hedged_use_leg: bool = False
    rate: float = 0.0


@dataclass(slots=True)
class SymbolVolume:
    """Volume limits, steps, and real-time deal metrics."""

    min: float = 0.01
    max: float = 100.0
    step: float = 0.01
    limit: float = 0.0
    current: int = 0
    high: int = 0
    low: int = 0
    real: float = 0.0
    real_high: float = 0.0
    real_low: float = 0.0


@dataclass(slots=True)
class SymbolTrade:
    """Trading policy, orders, and execution parameters."""

    stops_level: int = 0
    freeze_level: int = 0
    min_distance: float = 0.0
    commission_settings: str | None = None
    mode: str = "Full access"
    execution: str = "Market"
    calculation: str = "Forex"
    gtc: str = "Good till cancelled"
    filling: list[str] = field(default_factory=lambda: ["Immediate or Cancel"])
    expiration: list[str] = field(
        default_factory=lambda: [
            "Good till cancelled",
            "Day",
            "Specified",
            "Specified day",
        ]
    )
    orders: list[str] = field(
        default_factory=lambda: [
            "Market",
            "Limit",
            "Stop",
            "Stop limit",
            "Stop Loss",
            "Take Profit",
            "Close By",
        ]
    )


@dataclass(slots=True)
class SymbolPrice:
    """Price resolution, contract dimensions, and market depth."""

    digits: int = 5
    tick_size: float = 0.00001
    tick_step: float = 0.00001
    tick_value: float = 1.0
    contract_size: float = 100_000.0
    point_value: float | None = None
    pip_size: float | None = None
    bid: float = 0.0
    ask: float = 0.0
    chart_mode: str = "Bid"


@dataclass(slots=True)
class SymbolSwap:
    """Financing swap rates and triple-swap scheduling."""

    mode: str = "Points"
    long: float = 0.0
    short: float = 0.0
    rollover3days: str = "Wednesday"
    settings: dict[str, Any] | None = None


@dataclass(slots=True)
class SymbolSessionWindow:
    """Trading session window for a day of week."""

    day_of_week: int = 0
    start_time: str = "00:00"
    end_time: str = "23:59:59"


@dataclass(slots=True)
class SymbolState:
    """Symbol visibility, selection, and customization flags."""

    custom: bool = False
    selected: bool = True
    visible: bool = True


def default_session_windows() -> list[SymbolSessionWindow]:
    """Return standard 7-day default trading session schedule as dataclass instances."""
    return [
        SymbolSessionWindow(day_of_week=d, start_time="00:00", end_time="23:59:59")
        for d in range(7)
    ]


_default_session_windows = default_session_windows


def _coerce_dataclass(cls: type[Any], val: Any) -> Any:
    if isinstance(val, dict):
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in val.items() if k in valid})
    return val


@dataclass(slots=True)
class SymbolInfo:
    """Atomic state of symbol specification, execution modes, rates, and spreads."""

    name: str = ""
    description: str = ""
    exchange: str = "XCCY"
    data_type: str = "Forex"
    path: str = ""
    spread: SymbolSpread = field(default_factory=SymbolSpread)
    margin: SymbolMargin = field(default_factory=SymbolMargin)
    volume: SymbolVolume = field(default_factory=SymbolVolume)
    trade: SymbolTrade = field(default_factory=SymbolTrade)
    price: SymbolPrice = field(default_factory=SymbolPrice)
    swap: SymbolSwap = field(default_factory=SymbolSwap)
    commission: float = 0.0
    session: list[SymbolSessionWindow] = field(default_factory=_default_session_windows)
    state: SymbolState = field(default_factory=SymbolState)

    def __post_init__(self) -> None:
        """Coerce dictionary inputs to typed dataclass instances."""
        if self.path:
            self.data_type = self.path.rpartition("\\")[0]
        self.spread = _coerce_dataclass(SymbolSpread, self.spread)
        self.margin = _coerce_dataclass(SymbolMargin, self.margin)
        self.volume = _coerce_dataclass(SymbolVolume, self.volume)
        self.trade = _coerce_dataclass(SymbolTrade, self.trade)
        self.price = _coerce_dataclass(SymbolPrice, self.price)
        self.swap = _coerce_dataclass(SymbolSwap, self.swap)
        self.state = _coerce_dataclass(SymbolState, self.state)
        if isinstance(self.session, list):
            self.session = [
                _coerce_dataclass(SymbolSessionWindow, w)
                for w in self.session
            ]

# --- End of SymbolInfo data structures ---

@dataclass(slots=True)
class PositionInfo:
    """Atomic state of an open market position."""
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
@dataclass(slots=True)
class OrderInfo:
    """Atomic state of an active or historical trade order."""
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
    position_by_id: int = 0
    comment: str = ""
    reason: int = 0
@dataclass(slots=True)
class DealInfo:
    """Atomic state of an executed trade deal."""
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
    fee: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    magic: int = 0
    reason: int = 0
    comment: str = ""
    time: int = 0
    time_msc: int = 0
@dataclass(slots=True)
class TradeRequest:
    """Strongly typed trading operation parameters."""
    action: TradeAction = TradeAction.DEAL
    magic: int = 0
    order: int = 0
    symbol: str = ""
    volume: float = 0.0
    price: float = 0.0
    stoplimit: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    deviation: int = 0
    order_type: OrderType = OrderType.BUY
    type_filling: OrderFilling = OrderFilling.FOK
    type_time: OrderTime = OrderTime.GTC
    expiration: datetime | None = None
    comment: str = ""
    position: int = 0
    position_by: int = 0
@dataclass(slots=True)
class TradeResult:
    """Strongly typed result of a sent trade operation."""
    retcode: int = 0
    deal: int = 0
    order: int = 0
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""
    request_id: int = 0
    retcode_external: int = 0
    retcode_description: str = ""
    raw: Any = None
@dataclass(slots=True)
class TradeCheckResult:
    """Strongly typed result of pre-trade checks."""
    retcode: int = 0
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = ""
    raw: Any = None
@dataclass
class ChartDef:
    """Market data request specification and resample compatibility abstraction."""
    symbol: str
    timeframe: str | Timeframe = "M1"
    instrument: str = "Forex"
    session: str = "Default"
    connection_name: str = ""
    connection_hash: int = 0
    symbol_hash: int = 0
    history_from: int = 0
    history_to: int = 0
    loaded_history_from: int = 0
    spread: float = 0.0
    real_spread: bool = False
    bar_time_type: int = 0
    min_distance: float = 0.0
    is_backtest_data_def: bool = False
    backload_type: int = 0
    backload_number: int = 0
    registered: bool = False
    def __post_init__(self) -> None:
        """Normalize timeframe string and initialize deterministic hashes."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = self.timeframe.value
        if not self.connection_hash and self.connection_name:
            self.connection_hash = abs(hash(self.connection_name))
        if not self.symbol_hash and self.symbol:
            self.symbol_hash = abs(hash(self.symbol))
    def timeframe_seconds(self) -> int:
        """Timeframe duration in seconds."""
        if isinstance(self.timeframe, Timeframe):
            return self.timeframe.to_seconds()
        tf_str = self.timeframe.strip().upper()
        if tf_str in ("TICK", "TICKS"):
            return 0
        try:
            return Timeframe.from_string(tf_str).to_seconds()
        except ValueError:
            is_s = tf_str.startswith("S") and tf_str[1:].isdigit()
            return int(tf_str[1:]) if is_s else 0
    def is_symbol_recognized(self) -> bool:
        """Check if symbol is valid/recognized."""
        return bool(self.symbol and self.symbol.strip())
    def is_smaller_than(self, other: ChartDef) -> bool:
        """Evaluate if this chart's timeframe is strictly smaller than other's."""
        return self.timeframe_seconds() < other.timeframe_seconds()
    def can_be_computed_from(self, other: ChartDef) -> bool:
        """Evaluate if this chart can be resampled/computed from another chart."""
        if self.symbol.strip().upper() != other.symbol.strip().upper():
            return False
        if self.session not in ("", "Default") and other.session not in (
            "", "Default", self.session
        ):
            return False
        o_sec, s_sec = other.timeframe_seconds(), self.timeframe_seconds()
        if o_sec > s_sec or (o_sec > 0 and s_sec % o_sec != 0):
            return False
        return not (
            0 < self.history_from < other.history_from
            or 0 < other.history_to < self.history_to
        )
    def is_same_connection_symbol(self, other: ChartDef) -> bool:
        """Check if both charts share identical connection name and symbol."""
        s_sym, o_sym = self.symbol.strip().upper(), other.symbol.strip().upper()
        s_con = self.connection_name.strip().upper()
        o_con = other.connection_name.strip().upper()
        return s_sym == o_sym and s_con == o_con
    def get_charts_hash(self) -> str:
        """Compute unique identifier hash string for chart."""
        return f"{self.connection_name}_{self.symbol}_{self.timeframe}_{self.session}"
    def clone(
        self, symbol: str | None = None,
        history_from: int | None = None, history_to: int | None = None,
    ) -> ChartDef:
        """Clone this ChartDef, optionally overriding symbol or date ranges."""
        ov: dict[str, Any] = {}
        if symbol is not None:
            ov.update(symbol=symbol, symbol_hash=abs(hash(symbol)))
        if history_from is not None:
            ov["history_from"] = history_from
        if history_to is not None:
            ov["history_to"] = history_to
        return replace(self, **ov)
    def to_dict(self) -> dict[str, Any]:
        """Serialize ChartDef to a dictionary."""
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartDef:
        """Construct ChartDef from a dictionary."""
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})


def _sync_default_pair(
    obj: Any, attr_a: str, attr_b: str, default_a: Any, default_b: Any | None = None
) -> None:
    """Synchronize two paired attributes when one diverges from its default."""
    def_b = default_a if default_b is None else default_b
    val_a, val_b = getattr(obj, attr_a), getattr(obj, attr_b)
    if val_a != default_a and val_b == def_b:
        setattr(obj, attr_b, val_a)
    elif val_b != def_b and val_a == default_a:
        setattr(obj, attr_a, val_b)


@dataclass
class DataInfo:
    """Historical market dataset catalog metadata record."""
    id: str | int = 0
    symbol: str = ""
    timeframe: str | Timeframe = "M1"
    instrument: str = "Forex"
    connection: str = ""
    timezone: str = "UTC"
    decimals: int = 4
    date_from: str | int = 0
    date_from_str: str = ""
    date_to: str | int = 0
    date_to_str: str = ""
    rows: int = 0
    total_days: int = 0
    filename: str = ""
    file_hash: int = 0
    bar_time_type: int = 0
    remove_weekends: bool = True
    show: bool = True
    source: str | int = 0
    source_data_id: int = 0
    basket_id: int = 0
    broker_id: int = 0
    original_symbol: str = ""
    seconds_records: int = 0
    u_symbol: str = ""
    u_symbol_name: str = ""
    underlying: str = ""
    broker: str = "Default"
    broker_name: str = "Default"
    category: str = "Forex"
    bars: int = 0
    bar_type: str = "start"
    updated_at_utc: str = ""
    path: str = ""
    data_kind: str = "bars"
    quality_score: float = 1.0
    total_records: int = 0
    data_type: str = ""
    def __post_init__(self) -> None:
        """Harmonize aliases, default fields, and normalized types."""
        if isinstance(self.timeframe, Timeframe):
            self.timeframe = self.timeframe.value
        _sync_default_pair(self, "path", "filename", "")
        _sync_default_pair(self, "bars", "rows", 0)
        _sync_default_pair(self, "bars", "total_records", 0)
        _sync_default_pair(self, "bars", "rows", 0)
        _sync_default_pair(self, "broker_name", "broker", "Default")
        _sync_default_pair(self, "data_type", "category", "", "Forex")
        self.data_type = self.data_type or self.category
        self.underlying = self.underlying or self.symbol
        if isinstance(self.date_from, str):
            _sync_default_pair(self, "date_from", "date_from_str", "")
        elif not self.date_from and self.date_from_str:
            self.date_from = self.date_from_str
        if isinstance(self.date_to, str):
            _sync_default_pair(self, "date_to", "date_to_str", "")
        elif not self.date_to and self.date_to_str:
            self.date_to = self.date_to_str
        if isinstance(self.source, str):
            _sync_default_pair(self, "connection", "source", "")
        elif not self.source and self.connection:
            self.source = self.connection
    def clone(self) -> DataInfo:
        """Clone this DataInfo record."""
        return replace(self)
    def to_chart_def(self) -> ChartDef:
        """Convert catalog metadata record into an operational ChartDef."""
        return ChartDef(
            symbol=self.symbol, timeframe=str(self.timeframe),
            instrument=self.instrument, bar_time_type=self.bar_time_type,
            connection_name=str(self.connection or self.source or ""),
            history_from=self.date_from if isinstance(self.date_from, int) else 0,
            history_to=self.date_to if isinstance(self.date_to, int) else 0,
        )
    def to_dict(self) -> dict[str, Any]:
        """Serialize DataInfo to a dictionary."""
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataInfo:
        """Construct DataInfo from a dictionary."""
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})
    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> DataInfo:
        """Construct DataInfo from database row or mapping."""
        return cls(
            id=str(row.get("id", "")), source=str(row.get("source", "file")),
            symbol=str(row.get("symbol", "")),
            underlying=str(row.get("underlying", "")),
            instrument=str(row.get("instrument", "")),
            timeframe=str(row.get("timeframe", "M1")),
            broker=str(row.get("broker", "Default")),
            broker_name=str(row.get("broker_name", "Default")),
            timezone=str(row.get("timezone", "UTC")),
            category=str(row.get("category", "Forex")),
            date_from=str(row.get("date_from", "")),
            date_to=str(row.get("date_to", "")),
            bars=int(row.get("bars", 0)), bar_type=str(row.get("bar_type", "start")),
            updated_at_utc=str(row.get("updated_at", row.get("updated_at_utc", ""))),
            path=str(row.get("path", "")), data_kind=str(row.get("data_kind", "bars")),
            quality_score=float(row.get("quality_score", 1.0)),
        )
@dataclass(slots=True)
class SymbolAliasRecord:
    """Represents a symbol alias mapping."""
    alias: str
    symbol: str
    description: str = ""
    def to_dict(self) -> dict[str, Any]:
        """Convert alias record to dictionary representation."""
        return asdict(self)
_DAY_NAMES = (
    "mon", "monday", "tue", "tuesday", "wed", "wednesday",
    "thu", "thursday", "fri", "friday", "sat", "saturday", "sun", "sunday",
)
_DAY_NAME_TO_INT: dict[str, int] = {
    name: idx // 2 for idx, name in enumerate(_DAY_NAMES)
}
@dataclass(frozen=True)
class SessionWindow:
    """Represents a continuous trading interval on specific days of week."""
    day_from: str = "Mon"
    day_to: str = "Mon"
    start_time: str = "00:00"
    end_time: str = "23:59"
    eod: bool = False
    session_type: str = "Regular"
    day_of_week: int | None = None
    def to_dict(self) -> dict[str, Any]:
        """Convert session window to dictionary representation."""
        return asdict(self)
@dataclass(frozen=True)
class TradingHoliday:
    """Represents a date when markets are closed."""
    date_str: str
    description: str = ""
    def to_dict(self) -> dict[str, Any]:
        """Convert holiday to dictionary representation."""
        return asdict(self)
def _window_intervals(w: SessionWindow) -> list[tuple[int, int]]:
    """Derive list of (start_minute, end_minute) weekly intervals for window."""
    try:
        start_day = _DAY_NAME_TO_INT.get(w.day_from.lower(), w.day_of_week or 0)
        end_day = _DAY_NAME_TO_INT.get(w.day_to.lower(), start_day)
        sh, sm = (int(x) for x in w.start_time.split(":")[:2])
        eh, em = (int(x) for x in w.end_time.split(":")[:2])
        s_min, e_min = sh * 60 + sm, eh * 60 + em
        if (end_day - start_day) % 7 == 1 and s_min > e_min:
            return [(start_day * 1440 + s_min, end_day * 1440 + e_min)]
        if start_day == end_day and s_min > e_min:
            return [(start_day * 1440 + s_min, ((start_day + 1) % 7) * 1440 + e_min)]
        days: list[int] = []
        curr = start_day
        for _ in range(7):
            days.append(curr)
            if curr == end_day:
                break
            curr = (curr + 1) % 7
        return [
            (d * 1440 + s_min, (d if s_min <= e_min else (d + 1) % 7) * 1440 + e_min)
            for d in days
        ]
    except ValueError, TypeError, AttributeError:
        return []
def _is_window_active(w: SessionWindow, minute_of_week: int) -> bool:
    """Check if session window covers the specified minute of week (0..10079)."""
    return any(
        (s <= e and s <= minute_of_week <= e)
        or (s > e and (minute_of_week >= s or minute_of_week <= e))
        for s, e in _window_intervals(w)
    )
def _parse_json_list(raw: Any) -> list[Any]:
    """Parse JSON list string or return list as-is."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            res = json.loads(raw)
            return res if isinstance(res, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []
def _session_day(window: Mapping[str, Any]) -> str:
    days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    return days[int(window.get("day_of_week") or 0) % len(days)]

@dataclass
class TradingSession:
    """Represents an authoritative trading session calendar."""
    id: int | None = None
    name: str = ""
    broker_id: int = -1
    broker_name: str = "Default"
    description: str = ""
    timezone: str = "UTC"
    windows: list[SessionWindow] = field(default_factory=list)
    holidays: list[TradingHoliday] = field(default_factory=list)
    is_default: bool = False
    def is_within_session(self, dt: datetime) -> bool:
        """Evaluate if datetime falls within active trading schedule."""
        try:
            target_tz = ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            target_tz = ZoneInfo("UTC")
        base_dt = dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
        dt_tz = base_dt.astimezone(target_tz)
        date_iso = dt_tz.strftime("%Y-%m-%d")
        if any(h.date_str == date_iso for h in self.holidays) or not self.windows:
            return False
        minute_of_week = dt_tz.weekday() * 1440 + dt_tz.hour * 60 + dt_tz.minute
        return any(_is_window_active(w, minute_of_week) for w in self.windows)
    def to_dict(self) -> dict[str, Any]:
        """Convert trading session to dictionary representation."""
        return asdict(self)
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TradingSession:
        """Construct TradingSession from dictionary or database row."""
        windows = [
            w if isinstance(w, SessionWindow) else SessionWindow(
                day_from=str(w.get("day_from", _session_day(w))),
                day_to=str(w.get("day_to", w.get("day_from", _session_day(w)))),
                start_time=str(w.get("start_time", w.get("open_time", "00:00"))),
                end_time=str(w.get("end_time", w.get("close_time", "23:59"))),
                eod=bool(w.get("eod", False)),
                session_type=str(w.get("session_type", "Regular")),
                day_of_week=w.get("day_of_week"),
            )
            for w in _parse_json_list(data.get("windows_json", "[]"))
            if isinstance(w, (SessionWindow, dict))
        ]
        holidays = [
            h if isinstance(h, TradingHoliday) else TradingHoliday(
                date_str=str(h.get("date_str", "")),
                description=str(h.get("description", "")),
            )
            for h in _parse_json_list(data.get("holidays_json", "[]"))
            if isinstance(h, (TradingHoliday, dict))
        ]
        return cls(
            id=data.get("id"), name=str(data.get("name", "")),
            broker_id=int(data.get("broker_id", -1)),
            broker_name=str(data.get("broker_name", "Default")),
            description=str(data.get("description", "")),
            timezone=str(data.get("timezone", "UTC")),
            windows=windows, holidays=holidays,
            is_default=bool(data.get("is_default", 0)),
        )
class DataframeSeries:
    """Numerical time series wrapper with shift-based quantitative indexing."""

    def __init__(self, values: np.ndarray | Sequence[float], name: str = "") -> None:
        """Initialize an IndicatorSeries.

        Args:
            values: 1D array or sequence of float values.
            name: Optional descriptive series name.
        """
        if isinstance(values, np.ndarray):
            self._values: np.ndarray = values.astype(np.float64)
        else:
            self._values = np.array(values, dtype=np.float64)
        self._name = name


    @property
    def name(self) -> str:
        """Return the series name."""
        return self._name

    @property
    def values(self) -> np.ndarray:
        """Return the underlying numeric values as a numpy array."""
        return self._values

    def __len__(self) -> int:
        """Return the number of elements in the series."""
        return len(self._values)

    def get(self, shift: int = 0) -> float:
        """Get series value at the specified historical bar shift."""
        if shift < 0 or shift >= len(self._values):
            return float("nan")
        return float(self._values[-(1 + shift)])

# fmt: on
