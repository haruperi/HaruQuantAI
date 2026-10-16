"""Domain value objects and contracts for accounts, symbols, orders, and deals."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .enums import (
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

__all__ = [
    "BOOK_TYPE_DESCRIPTIONS",
    "DEAL_ENTRY_DESCRIPTIONS",
    "DEAL_TYPE_DESCRIPTIONS",
    "MAX_POSITION",
    "MAX_RECORDS",
    "ORDER_FILLING_DESCRIPTIONS",
    "ORDER_STATE_DESCRIPTIONS",
    "ORDER_TIME_DESCRIPTIONS",
    "ORDER_TYPE_DESCRIPTIONS",
    "POSITION_TYPE_DESCRIPTIONS",
    "READ_TIMEOUT",
    "SYMBOL_CALC_MODE_DESCRIPTIONS",
    "SYMBOL_SWAP_MODE_DESCRIPTIONS",
    "SYMBOL_TRADE_EXECUTION_DESCRIPTIONS",
    "SYMBOL_TRADE_MODE_DESCRIPTIONS",
    "TIMEFRAME_SECONDS",
    "AccountInfo",
    "BookInfo",
    "BridgeEvent",
    "ChartDef",
    "DataInfo",
    "DealInfo",
    "MarketBar",
    "MarketTick",
    "OrderInfo",
    "PositionInfo",
    "PropertyValue",
    "Receipt",
    "SymbolAliasRecord",
    "SymbolInfo",
    "TerminalInfo",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
]

MAX_RECORDS: int = 1000
MAX_POSITION: int = 2**31 - 1
READ_TIMEOUT: float = 60.0

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

POSITION_TYPE_DESCRIPTIONS: dict[PositionType, str] = {
    PositionType.BUY: "Buy",
    PositionType.SELL: "Sell",
}

ORDER_STATE_DESCRIPTIONS: dict[OrderState, str] = {
    item: item.name.replace("_", " ").title() for item in OrderState
}

DEAL_TYPE_DESCRIPTIONS: dict[DealType, str] = {
    item: item.name.replace("_", " ").title() for item in DealType
}

DEAL_ENTRY_DESCRIPTIONS: dict[DealEntry, str] = {
    item: item.name.replace("_", " ").title() for item in DealEntry
}

SYMBOL_TRADE_MODE_DESCRIPTIONS: dict[SymbolTradeMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolTradeMode
}

SYMBOL_TRADE_EXECUTION_DESCRIPTIONS: dict[SymbolTradeExecution, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolTradeExecution
}

SYMBOL_SWAP_MODE_DESCRIPTIONS: dict[SymbolSwapMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolSwapMode
}

SYMBOL_CALC_MODE_DESCRIPTIONS: dict[SymbolCalcMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolCalcMode
}

TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    frame: frame.to_seconds()
    for frame in Timeframe
    if frame != Timeframe.PERIOD_CURRENT
}


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


@dataclass(frozen=True, slots=True)
class BookInfo:
    """Market depth (DOM) book entry."""

    type: BookType
    price: float
    volume: int
    volume_real: float

    def _asdict(self) -> dict[str, Any]:
        """Convert entry to a dictionary."""
        return {
            "type": int(self.type),
            "price": self.price,
            "volume": self.volume,
            "volume_real": self.volume_real,
        }


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


_DEFAULT_DIGITS: int = 5
_DEFAULT_TICK_SIZE: float = 0.00001
_DEFAULT_CONTRACT_SIZE: float = 100_000.0
_DEFAULT_TICK_VALUE: float = 1.0
_DEFAULT_TICK_VALUE_IN_MONEY: float = 10.0
_DEFAULT_VOLUME_MIN: float = 0.01
_DEFAULT_VOLUME_MAX: float = 100.0
_DEFAULT_VOLUME_STEP: float = 0.01
_DEFAULT_SWAP_ROLLOVER_DAYS: int = 3


@dataclass(slots=True)
class SymbolInfo:
    """Atomic state of symbol specification, execution modes, rates, and spreads."""

    name: str = ""
    symbol: str = ""
    id: int | None = None
    connection: str = ""
    broker_id: int = 0
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
    trade_mode: int = int(SymbolTradeMode.FULL)
    trade_mode_description: str = "Full Access"
    start_time: int = 0
    expiration_time: int = 0
    trade_stops_level: int = 0
    trade_freeze_level: int = 0
    trade_exemode: int = int(SymbolTradeExecution.MARKET)
    trade_execution_description: str = "Market"
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
    default_spread: float = 0.0
    default_slippage: float = 0.0
    commissions: str = "0.0"
    alias: str = ""
    country: str = ""
    sector: str = ""
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0
    cot: str | None = None
    created_at_utc: str = ""
    updated_at_utc: str = ""
    decimals: int = 5
    tick_size: float = 0.00001
    tick_step: float = 0.00001
    point_value: float = 100_000.0
    tick_value_in_money: float = 1.0
    min_volume: float = 0.01
    max_volume: float = 100.0
    lot_step: float = 0.01
    margin_rate: float = 0.0
    data_type: str = ""
    min_distance: float = 0.0
    swap_3day_day: int = 3

    def __post_init__(self) -> None:
        """Synchronize name/symbol and dual-named instrument attributes."""
        self._sync_identifiers()
        self._sync_digits_and_ticks()
        self._sync_contracts_and_values()
        self._sync_volumes_and_swaps()

    def _sync_identifiers(self) -> None:
        """Synchronize name/symbol and category/data_type."""
        if not self.name and self.symbol:
            self.name = self.symbol
        elif not self.symbol and self.name:
            self.symbol = self.name

        if not self.category and self.data_type:
            self.category = self.data_type
        elif not self.data_type and self.category:
            self.data_type = self.category

    def _sync_digits_and_ticks(self) -> None:
        """Synchronize digits, tick_size, and tick_step."""
        if self.digits != _DEFAULT_DIGITS and self.decimals == _DEFAULT_DIGITS:
            self.decimals = self.digits
        elif self.decimals != _DEFAULT_DIGITS and self.digits == _DEFAULT_DIGITS:
            self.digits = self.decimals

        if (
            self.trade_tick_size != _DEFAULT_TICK_SIZE
            and self.tick_size == _DEFAULT_TICK_SIZE
        ):
            self.tick_size = self.trade_tick_size
        elif (
            self.tick_size != _DEFAULT_TICK_SIZE
            and self.trade_tick_size == _DEFAULT_TICK_SIZE
        ):
            self.trade_tick_size = self.tick_size

        if (
            self.tick_step == _DEFAULT_TICK_SIZE
            and self.tick_size != _DEFAULT_TICK_SIZE
        ):
            self.tick_step = self.tick_size
        elif (
            self.tick_size == _DEFAULT_TICK_SIZE
            and self.tick_step != _DEFAULT_TICK_SIZE
        ):
            self.tick_size = self.tick_step

    def _sync_contracts_and_values(self) -> None:
        """Synchronize contract size and tick value."""
        if (
            self.trade_contract_size != _DEFAULT_CONTRACT_SIZE
            and self.point_value == _DEFAULT_CONTRACT_SIZE
        ):
            self.point_value = self.trade_contract_size
        elif (
            self.point_value != _DEFAULT_CONTRACT_SIZE
            and self.trade_contract_size == _DEFAULT_CONTRACT_SIZE
        ):
            self.trade_contract_size = self.point_value

        if (
            self.trade_tick_value != _DEFAULT_TICK_VALUE
            and self.tick_value_in_money == _DEFAULT_TICK_VALUE_IN_MONEY
        ):
            self.tick_value_in_money = self.trade_tick_value
        elif (
            self.tick_value_in_money != _DEFAULT_TICK_VALUE_IN_MONEY
            and self.trade_tick_value == _DEFAULT_TICK_VALUE
        ):
            self.trade_tick_value = self.tick_value_in_money

    def _sync_volumes_and_swaps(self) -> None:
        """Synchronize volume and swap parameters."""
        if (
            self.volume_min != _DEFAULT_VOLUME_MIN
            and self.min_volume == _DEFAULT_VOLUME_MIN
        ):
            self.min_volume = self.volume_min
        elif (
            self.min_volume != _DEFAULT_VOLUME_MIN
            and self.volume_min == _DEFAULT_VOLUME_MIN
        ):
            self.volume_min = self.min_volume

        if (
            self.volume_max != _DEFAULT_VOLUME_MAX
            and self.max_volume == _DEFAULT_VOLUME_MAX
        ):
            self.max_volume = self.volume_max
        elif (
            self.max_volume != _DEFAULT_VOLUME_MAX
            and self.volume_max == _DEFAULT_VOLUME_MAX
        ):
            self.volume_max = self.max_volume

        if (
            self.volume_step != _DEFAULT_VOLUME_STEP
            and self.lot_step == _DEFAULT_VOLUME_STEP
        ):
            self.lot_step = self.volume_step
        elif (
            self.lot_step != _DEFAULT_VOLUME_STEP
            and self.volume_step == _DEFAULT_VOLUME_STEP
        ):
            self.volume_step = self.lot_step

        if (
            self.swap_rollover3days != _DEFAULT_SWAP_ROLLOVER_DAYS
            and self.swap_3day_day == _DEFAULT_SWAP_ROLLOVER_DAYS
        ):
            self.swap_3day_day = self.swap_rollover3days
        elif (
            self.swap_3day_day != _DEFAULT_SWAP_ROLLOVER_DAYS
            and self.swap_rollover3days == _DEFAULT_SWAP_ROLLOVER_DAYS
        ):
            self.swap_rollover3days = self.swap_3day_day

    def round_to_tick_size(self, price: float) -> float:
        """Round a price to the symbol's minimum tick size."""
        step = (
            self.trade_tick_size
            if self.trade_tick_size > 0.0
            else (self.tick_size if self.tick_size > 0.0 else 0.00001)
        )
        digits = self.digits if self.digits > 0 else self.decimals
        return round(round(price / step) * step, digits)

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary representation."""
        return {
            "id": self.id,
            "symbol": self.symbol or self.name,
            "connection": self.connection,
            "broker_id": self.broker_id,
            "description": self.description,
            "tick_size": self.tick_size,
            "tick_step": self.tick_step or self.tick_size,
            "tick_value_in_money": self.tick_value_in_money,
            "point_value": self.point_value,
            "decimals": self.decimals,
            "default_spread": self.default_spread,
            "default_slippage": self.default_slippage,
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "lot_step": self.lot_step,
            "margin_rate": self.margin_rate,
            "swap_long": self.swap_long,
            "swap_short": self.swap_short,
            "swap_3day_day": self.swap_3day_day or self.swap_rollover3days,
            "commissions": self.commissions,
            "data_type": self.data_type or self.category or "Forex",
            "alias": self.alias,
            "exchange": self.exchange,
            "country": self.country,
            "sector": self.sector,
            "min_distance": self.min_distance or float(self.trade_stops_level),
            "order_size_multiplier": self.order_size_multiplier,
            "order_size_step": self.order_size_step,
            "cot": self.cot,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SymbolInfo:
        """Construct SymbolInfo from dictionary data."""
        sym = str(data.get("symbol") or data.get("name") or "")
        digits = int(data.get("decimals") or data.get("digits") or 5)
        tick_sz = float(data.get("tick_size") or data.get("trade_tick_size") or 0.00001)
        tick_st = float(data.get("tick_step") or tick_sz)
        point_val = float(
            data.get("point_value") or data.get("trade_contract_size") or 100000.0
        )
        tick_val = float(
            data.get("tick_value_in_money") or data.get("trade_tick_value") or 10.0
        )
        v_min = float(data.get("min_volume") or data.get("volume_min") or 0.01)
        v_max = float(data.get("max_volume") or data.get("volume_max") or 100.0)
        v_step = float(data.get("lot_step") or data.get("volume_step") or 0.01)
        m_rate = float(data.get("margin_rate") or data.get("margin_initial") or 0.05)
        sw_long = float(data.get("swap_long") or 0.0)
        sw_short = float(data.get("swap_short") or 0.0)
        sw_3day = int(data.get("swap_3day_day") or data.get("swap_rollover3days") or 3)
        cat = str(data.get("data_type") or data.get("category") or "Forex")
        min_dist = float(
            data.get("min_distance") or data.get("trade_stops_level") or 0.0
        )
        return cls(
            id=data.get("id"),
            name=sym,
            symbol=sym,
            digits=digits,
            decimals=digits,
            point=tick_sz,
            trade_tick_size=tick_sz,
            tick_size=tick_sz,
            tick_step=tick_st,
            trade_tick_value=tick_val,
            tick_value_in_money=tick_val,
            trade_contract_size=point_val,
            point_value=point_val,
            volume_min=v_min,
            min_volume=v_min,
            volume_max=v_max,
            max_volume=v_max,
            volume_step=v_step,
            lot_step=v_step,
            margin_initial=m_rate,
            margin_rate=m_rate,
            swap_long=sw_long,
            swap_short=sw_short,
            swap_rollover3days=sw_3day,
            swap_3day_day=sw_3day,
            trade_stops_level=int(min_dist),
            min_distance=min_dist,
            category=cat,
            data_type=cat,
            connection=str(data.get("connection", "")),
            broker_id=int(data.get("broker_id", 0)),
            description=str(data.get("description", "")),
            default_spread=float(data.get("default_spread", 0.0)),
            default_slippage=float(data.get("default_slippage", 0.0)),
            commissions=str(data.get("commissions", "0.0")),
            alias=str(data.get("alias", "")),
            exchange=str(data.get("exchange", "")),
            country=str(data.get("country", "")),
            sector=str(data.get("sector", "")),
            order_size_multiplier=float(data.get("order_size_multiplier", 1.0)),
            order_size_step=float(data.get("order_size_step", 0.0)),
            cot=str(data["cot"]) if data.get("cot") is not None else None,
            created_at_utc=str(data.get("created_at_utc", "")),
            updated_at_utc=str(data.get("updated_at_utc", "")),
        )

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> SymbolInfo:
        """Construct SymbolInfo from database row mapping."""
        return cls.from_dict(row)


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
        tf_str = str(self.timeframe).strip().upper()
        if tf_str in ("TICK", "TICKS"):
            return 0
        try:
            return Timeframe.from_string(tf_str).to_seconds()
        except ValueError:
            pass
        if tf_str.startswith("S") and tf_str[1:].isdigit():
            return int(tf_str[1:])
        return 0

    def is_symbol_recognized(self) -> bool:
        """Check if symbol is valid/recognized."""
        return bool(self.symbol and len(self.symbol.strip()) > 0)

    def is_smaller_than(self, other: ChartDef) -> bool:
        """Evaluate if this chart's timeframe is strictly smaller than other's."""
        return self.timeframe_seconds() < other.timeframe_seconds()

    def can_be_computed_from(self, other: ChartDef) -> bool:
        """Evaluate if this chart can be resampled/computed from another chart."""
        if self.symbol.strip().upper() != other.symbol.strip().upper():
            return False

        if (
            self.session
            and other.session
            and self.session != "Default"
            and other.session not in ("Default", self.session)
        ):
            return False

        other_sec = other.timeframe_seconds()
        self_sec = self.timeframe_seconds()

        if other_sec > self_sec:
            return False

        if other_sec > 0 and self_sec % other_sec != 0:
            return False

        has_from_mismatch = (
            self.history_from > 0
            and other.history_from > 0
            and other.history_from > self.history_from
        )
        has_to_mismatch = (
            self.history_to > 0
            and other.history_to > 0
            and other.history_to < self.history_to
        )
        return not (has_from_mismatch or has_to_mismatch)

    def is_same_connection_symbol(self, other: ChartDef) -> bool:
        """Check if both charts share identical connection name and symbol."""
        return (
            self.symbol.strip().upper() == other.symbol.strip().upper()
            and self.connection_name.strip().upper()
            == other.connection_name.strip().upper()
        )

    def get_charts_hash(self) -> str:
        """Compute unique identifier hash string for chart."""
        return f"{self.connection_name}_{self.symbol}_{self.timeframe}_{self.session}"

    def clone(
        self,
        symbol: str | None = None,
        history_from: int | None = None,
        history_to: int | None = None,
    ) -> ChartDef:
        """Clone this ChartDef, optionally overriding symbol or date ranges."""
        overrides: dict[str, Any] = {}
        if symbol is not None:
            overrides["symbol"] = symbol
            overrides["symbol_hash"] = abs(hash(symbol))
        if history_from is not None:
            overrides["history_from"] = history_from
        if history_to is not None:
            overrides["history_to"] = history_to
        return replace(self, **overrides)

    def to_dict(self) -> dict[str, Any]:
        """Serialize ChartDef to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartDef:
        """Construct ChartDef from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


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
        self._sync_paths_and_counts()
        self._sync_dates()
        self._sync_identifiers()

    def _sync_paths_and_counts(self) -> None:
        """Synchronize file paths and row counts."""
        if not self.path and self.filename:
            self.path = self.filename
        elif not self.filename and self.path:
            self.filename = self.path
        if not self.bars and self.rows:
            self.bars = self.rows
        elif not self.rows and self.bars:
            self.rows = self.bars
        if not self.total_records and (self.bars or self.rows):
            self.total_records = self.bars or self.rows
        elif not self.bars and self.total_records:
            self.bars = self.total_records
            self.rows = self.total_records

    def _sync_dates(self) -> None:
        """Synchronize start and end dates."""
        if not self.date_from_str and isinstance(self.date_from, str):
            self.date_from_str = self.date_from
        elif not self.date_from and self.date_from_str:
            self.date_from = self.date_from_str
        if not self.date_to_str and isinstance(self.date_to, str):
            self.date_to_str = self.date_to
        elif not self.date_to and self.date_to_str:
            self.date_to = self.date_to_str

    def _sync_identifiers(self) -> None:
        """Synchronize source, broker, and underlying symbol identifiers."""
        if not self.connection and isinstance(self.source, str) and self.source:
            self.connection = self.source
        elif (self.source == 0 or not self.source) and self.connection:
            self.source = self.connection
        if not self.underlying and self.symbol:
            self.underlying = self.symbol
        if not self.broker_name and self.broker:
            self.broker_name = self.broker
        elif not self.broker and self.broker_name:
            self.broker = self.broker_name
        if self.data_type and (not self.category or self.category == "Forex"):
            self.category = self.data_type
        elif self.category and not self.data_type:
            self.data_type = self.category

    def clone(self) -> DataInfo:
        """Clone this DataInfo record."""
        return replace(self)

    def to_chart_def(self) -> ChartDef:
        """Convert catalog metadata record into an operational ChartDef."""
        h_from = self.date_from if isinstance(self.date_from, int) else 0
        h_to = self.date_to if isinstance(self.date_to, int) else 0
        conn_name = str(self.connection or self.source or "")
        return ChartDef(
            symbol=self.symbol,
            timeframe=str(self.timeframe),
            instrument=self.instrument,
            connection_name=conn_name,
            history_from=h_from,
            history_to=h_to,
            bar_time_type=self.bar_time_type,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DataInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataInfo:
        """Construct DataInfo from a dictionary."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> DataInfo:
        """Construct DataInfo from database row or mapping."""
        d_from = str(row.get("date_from", ""))
        d_to = str(row.get("date_to", ""))
        bar_count = int(row.get("bars", 0))
        f_path = str(row.get("path", ""))
        src = str(row.get("source", "file"))
        cat = str(row.get("category", "Forex"))
        return cls(
            id=str(row.get("id", "")),
            source=src,
            symbol=str(row.get("symbol", "")),
            underlying=str(row.get("underlying", "")),
            instrument=str(row.get("instrument", "")),
            timeframe=str(row.get("timeframe", "M1")),
            broker=str(row.get("broker", "Default")),
            broker_name=str(row.get("broker_name", "Default")),
            timezone=str(row.get("timezone", "UTC")),
            category=cat,
            date_from=d_from,
            date_to=d_to,
            date_from_str=d_from,
            date_to_str=d_to,
            bars=bar_count,
            rows=bar_count,
            total_records=bar_count,
            data_type=cat,
            bar_type=str(row.get("bar_type", "start")),
            updated_at_utc=str(row.get("updated_at", row.get("updated_at_utc", ""))),
            path=f_path,
            filename=f_path,
            data_kind=str(row.get("data_kind", "bars")),
            quality_score=float(row.get("quality_score", 1.0)),
            connection=src,
        )


@dataclass(slots=True)
class SymbolAliasRecord:
    """Represents a symbol alias mapping."""

    alias: str
    symbol: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert alias record to dictionary representation."""
        return {
            "alias": self.alias,
            "symbol": self.symbol,
            "description": self.description,
        }
