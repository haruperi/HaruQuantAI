"""Broker-neutral domain models, capability flags, and unified interface contracts.

Description:
    Provides canonical domain data models, bitmask capability flags, unified
    order and timeframe enumerations, and the `BaseBroker` abstract base class
    for quantitative execution and market data plugins across HaruQuantAI.
    Heterogeneous broker APIs (MetaTrader 5, cTrader, Dukascopy, Darwinex,
    Yahoo Finance, and StrategyQuant Parquet stores) have fundamentally different
    transport models, data types, and capabilities. This module normalizes those
    differences into immutable, strongly typed dataclasses and contracts.
    Externally, strategies, execution engines, and host services consume these
    contracts without platform-specific coupling. Internally, `BaseBroker`
    provides default unsupported capability rejection responses and routing
    infrastructure, ensuring that data-only brokers safely reject order
    requests while full-featured execution brokers implement verified trades.

Purpose:
    FEAT-BROKER-CONTRACTS: Broker-Neutral Contracts and Base Architecture.
    Defines canonical trading data models, capability bitmasks, standard
    timeframes, and base broker abstractions across all execution plugins.

Key Capabilities:
    - FR-BROKER-CAPABILITY-FLAGS: Capability Bitmask Inspection
      Associated: `[BrokerCapability]`, `[BaseBroker.has_capability()]`
      Logging: Emits DEBUG log when querying capability flags, and WARNING
      log on unsupported operation invocations via `BaseBroker._unsupported()`.
    - FR-BROKER-DOMAIN-MODELS: Canonical Trading Entity Instantiation
      Associated: `[AccountInfo]`, `[SymbolInfo]`, `[Tick]`, `[Bar]`,
      `[PositionInfo]`, `[OrderInfo]`, `[TradeRequest]`, `[TradeResult]`
      Logging: Emits INFO or DEBUG log via enclosing host response envelopes
      upon entity validation and serialization.
    - FR-BROKER-BASE-INTERFACE: Default Unsupported Capability Rejection
      Associated: `[BaseBroker]`, `[BaseBroker._unsupported()]`
      Logging: Emits WARNING log with operation name and broker plugin
      identifier when an unhandled capability is invoked.

Python API Usage:
    ```python
    from app.plugins.brokers.contracts import (
        BaseBroker,
        BrokerCapability,
        StandardResponse,
        TimeFrame,
    )


    class CustomBroker(BaseBroker):
        def __init__(self) -> None:
            super().__init__(
                name="Custom",
                capabilities=(BrokerCapability.CONNECT | BrokerCapability.MARKET_DATA),
            )


    broker = CustomBroker()
    assert broker.has_capability(BrokerCapability.MARKET_DATA)
    response = broker.connect()
    assert response.is_success
    ```

CLI Usage:
    ```bash
    uv run pytest tests/plugin/broker/test_contracts.py -v --no-cov
    ```
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, Flag, auto
from typing import Any, TypeVar

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse

logger = get_logger(__name__)

__all__ = [
    "AccountInfo",
    "Bar",
    "BaseBroker",
    "BookItem",
    "BrokerCapability",
    "DealInfo",
    "OrderAction",
    "OrderCheckResult",
    "OrderFilling",
    "OrderInfo",
    "OrderTime",
    "OrderType",
    "PositionInfo",
    "StandardError",
    "StandardResponse",
    "SymbolInfo",
    "TerminalInfo",
    "Tick",
    "TimeFrame",
    "TradeRequest",
    "TradeResult",
]

T = TypeVar("T")


# ============================================================================
# Enums
# ============================================================================


class BrokerCapability(Flag):
    """Flags representing distinct capabilities supported by a broker plugin."""

    NONE = 0
    CONNECT = auto()
    TERMINAL_INFO = auto()
    ACCOUNT_INFO = auto()
    SYMBOLS = auto()
    MARKET_DATA = auto()
    MARKET_DEPTH = auto()
    POSITIONS = auto()
    ORDERS = auto()
    HISTORY = auto()
    CALCULATIONS = auto()
    TRADING = auto()
    TRADE = TRADING
    ALL = (
        CONNECT
        | TERMINAL_INFO
        | ACCOUNT_INFO
        | SYMBOLS
        | MARKET_DATA
        | MARKET_DEPTH
        | POSITIONS
        | ORDERS
        | HISTORY
        | CALCULATIONS
        | TRADING
    )


class TimeFrame(str, Enum):
    """Standard timeframes across all brokers."""

    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


class OrderType(str, Enum):
    """Standard order types across brokers."""

    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    BUY_STOP_LIMIT = "BUY_STOP_LIMIT"
    SELL_STOP_LIMIT = "SELL_STOP_LIMIT"
    CLOSE = "CLOSE"


class OrderAction(str, Enum):
    """Trade action types."""

    DEAL = "DEAL"
    PENDING = "PENDING"
    SLTP = "SLTP"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"
    CLOSE = "CLOSE"


class OrderFilling(str, Enum):
    """Order execution filling policies."""

    FOK = "FOK"  # Fill or Kill
    IOC = "IOC"  # Immediate or Cancel
    RETURN = "RETURN"  # Return remainder to book


class OrderTime(str, Enum):
    """Order expiration policies."""

    GTC = "GTC"  # Good Till Cancelled
    DAY = "DAY"  # Good Till Day
    SPECIFIED = "SPECIFIED"  # Specified time
    SPECIFIED_DAY = "SPECIFIED_DAY"  # Specified day


# ============================================================================
# Core Data Models
# ============================================================================


@dataclass
class TerminalInfo:
    """Terminal/platform environment information."""

    # Identity & Paths
    name: str = ""
    company: str = ""
    language: str = ""
    path: str = ""
    data_path: str = ""
    commondata_path: str = ""
    version: str = ""

    # Connectivity & Permissions
    connected: bool = False
    trade_allowed: bool = False
    tradeapi_disabled: bool = False
    dlls_allowed: bool = False
    email_enabled: bool = False
    ftp_enabled: bool = False
    notifications_enabled: bool = False
    mqid: bool = False
    community_account: bool = False
    community_connection: bool = False

    # Metrics & System
    build: int = 0
    maxbars: int = 0
    codepage: int = 0
    ping_last: int = 0
    community_balance: float = 0.0
    retransmission: float = 0.0

    raw: Any = None


@dataclass
class AccountInfo:
    """Trading account status and balance metrics."""

    # Account Identity & Server
    login: int = 0
    name: str = ""
    server: str = ""
    currency: str = "USD"
    company: str = ""
    trade_mode: int = 0
    leverage: int = 0
    limit_orders: int = 0
    currency_digits: int = 2

    # Permissions & Modes
    trade_allowed: bool = False
    trade_expert: bool = False
    fifo_close: bool = False
    margin_mode: int = 0
    margin_so_mode: int = 0

    # Balances & Equity
    balance: float = 0.0
    credit: float = 0.0
    profit: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    margin_so_call: float = 0.0
    margin_so_so: float = 0.0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    assets: float = 0.0
    liabilities: float = 0.0
    commission_blocked: float = 0.0

    raw: Any = None


@dataclass
class SymbolInfo:
    """Instrument specifications and trading terms."""

    name: str

    # Visibility & Selection
    custom: bool = False
    chart_mode: int = 0
    select: bool = True
    visible: bool = True

    # Pricing & Precision
    digits: int = 5
    point: float = 0.00001
    spread: int = 0
    spread_float: bool = True
    ticks_bookdepth: int = 10

    # Quotes & Volumes
    bid: float = 0.0
    bidhigh: float = 0.0
    bidlow: float = 0.0
    ask: float = 0.0
    askhigh: float = 0.0
    asklow: float = 0.0
    last: float = 0.0
    lasthigh: float = 0.0
    lastlow: float = 0.0
    volume: int = 0
    volumehigh: int = 0
    volumelow: int = 0
    volume_real: float = 0.0
    volumehigh_real: float = 0.0
    volumelow_real: float = 0.0
    time: int = 0

    # Trade Specifications & Calculation Modes
    trade_calc_mode: int = 0
    trade_mode: int = 0
    start_time: int = 0
    expiration_time: int = 0
    trade_stops_level: int = 0
    trade_freeze_level: int = 0
    trade_exemode: int = 0
    swap_mode: int = 0
    swap_rollover3days: int = 3
    margin_hedged_use_leg: bool = False
    expiration_mode: int = 0
    filling_mode: int = 0
    order_mode: int = 0
    order_gtc_mode: int = 0
    option_mode: int = 0
    option_right: int = 0
    option_strike: float = 0.0

    # Tick & Contract Values
    trade_tick_value: float = 0.0
    trade_tick_value_profit: float = 0.0
    trade_tick_value_loss: float = 0.0
    trade_tick_size: float = 0.0
    trade_contract_size: float = 100000.0
    trade_accrued_interest: float = 0.0
    trade_face_value: float = 0.0
    trade_liquidity_rate: float = 0.0

    # Order Volume Limits
    volume_min: float = 0.01
    volume_max: float = 500.0
    volume_step: float = 0.01
    volume_limit: float = 0.0

    # Swaps & Margins
    swap_long: float = 0.0
    swap_short: float = 0.0
    margin_initial: float = 0.0
    margin_maintenance: float = 0.0
    margin_hedged: float = 100000.0

    # Session Statistics
    session_deals: int = 0
    session_buy_orders: int = 0
    session_sell_orders: int = 0
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

    # Pricing & Volatility Metrics
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

    # Instrument Metadata & Classification
    basis: str = ""
    category: str = ""
    currency_base: str = ""
    currency_profit: str = ""
    currency_margin: str = ""
    bank: str = ""
    description: str = ""
    exchange: str = ""
    formula: str = ""
    isin: str = ""
    page: str = ""
    path: str = ""

    raw: Any = None


@dataclass
class Tick:
    """Real-time symbol price snapshot."""

    time: datetime
    bid: float
    ask: float
    last: float = 0.0
    volume: float = 0.0
    flags: int = 0
    raw: Any = None


@dataclass
class Bar:
    """Historical candlestick bar."""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: int = 0
    real_volume: int = 0


@dataclass
class BookItem:
    """Market depth (Level 2) order book entry."""

    type: str  # BUY/SELL or BID/ASK
    price: float
    volume: float
    volume_dbl: float = 0.0


@dataclass
class PositionInfo:
    """Active open position."""

    ticket: int
    symbol: str
    type: str  # BUY or SELL
    volume: float
    price_open: float
    price_current: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    profit: float = 0.0
    swap: float = 0.0
    time: datetime | None = None
    comment: str = ""
    magic: int = 0
    raw: Any = None


@dataclass
class OrderInfo:
    """Active pending order or order in system."""

    ticket: int
    symbol: str
    type: str
    volume_initial: float
    volume_current: float = 0.0
    price_open: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    state: str = ""
    time_setup: datetime | None = None
    comment: str = ""
    magic: int = 0
    raw: Any = None


@dataclass
class DealInfo:
    """Executed trade deal transaction."""

    ticket: int
    order: int
    position_id: int = 0
    symbol: str = ""
    type: str = ""
    entry: str = ""
    volume: float = 0.0
    price: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    fee: float = 0.0
    time: datetime | None = None
    comment: str = ""
    magic: int = 0
    raw: Any = None


@dataclass
class TradeRequest:
    """Broker-neutral request structure for sending, modifying, or closing trades."""

    action: OrderAction | str = OrderAction.DEAL
    symbol: str = ""
    volume: float = 0.01
    type: OrderType | str = OrderType.BUY
    price: float | None = None
    sl: float | None = 0.0
    tp: float | None = 0.0
    deviation: int = 20
    magic: int = 0
    comment: str = ""
    position: int | None = 0
    order: int | None = 0
    type_time: OrderTime | str = OrderTime.GTC
    type_filling: OrderFilling | str | None = None
    expiration: datetime | None = None


@dataclass
class TradeResult:
    """Result returned after trade execution."""

    retcode: int
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


@dataclass
class OrderCheckResult:
    """Result returned from pre-flight order check."""

    retcode: int
    balance: float = 0.0
    equity: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    comment: str = ""
    raw: Any = None


# ============================================================================
# Base Broker Interface
# ============================================================================


class BaseBroker(ABC):
    """Abstract base class that all broker plugins must inherit from.

    Provides the 27 standard neutral method signatures. Methods with capability
    constraints will by default return an unsupported capability response if the
    subclass broker does not implement or support them.
    """

    def __init__(
        self,
        name: str,
        capabilities: BrokerCapability = BrokerCapability.ALL,
    ) -> None:
        """Initialize base broker.

        Args:
            name: Descriptive broker name (e.g. "MetaTrader5", "cTrader", "Yahoo").
            capabilities: Bitwise flags indicating supported capabilities.
        """
        self.name = name
        self.capabilities = capabilities
        self.logger = get_logger(f"app.plugins.brokers.{self.name}")

    def has_capability(self, capability: BrokerCapability) -> bool:
        """Check if broker supports the specified capability flag."""
        return bool(self.capabilities & capability)

    def _unsupported(self, feature_name: str) -> StandardResponse[Any]:
        """Helper generating standardized unsupported capability responses."""
        msg = f"{self.name} doesn't have {feature_name} capabilities"
        self.logger.warning(msg)
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code="CAPABILITY_NOT_SUPPORTED", message=msg),
            extensions={"broker": self.name},
        )

    # ------------------------------------------------------------------------
    # 1. Connection & Session
    # ------------------------------------------------------------------------

    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Establish connection to the broker terminal/API."""
        if not (self.capabilities & BrokerCapability.CONNECT):
            return self._unsupported("connection")
        return StandardResponse.success(data=True, extensions={"broker": self.name})

    def disconnect(self) -> StandardResponse[bool]:
        """Gracefully disconnect and terminate session."""
        if not (self.capabilities & BrokerCapability.CONNECT):
            return self._unsupported("connection")
        return StandardResponse.success(data=True, extensions={"broker": self.name})

    def is_connected(self) -> StandardResponse[bool]:
        """Check whether the client is currently connected to the broker."""
        if not (self.capabilities & BrokerCapability.CONNECT):
            return self._unsupported("connection")
        return StandardResponse.success(data=False, extensions={"broker": self.name})

    def get_last_error(self) -> StandardResponse[Any]:
        """Retrieve the last error code and message from the broker API."""
        return StandardResponse.success(
            data=(0, "No error"), extensions={"broker": self.name}
        )

    # ------------------------------------------------------------------------
    # 2. Terminal & Account Information
    # ------------------------------------------------------------------------

    def get_terminal_info(self) -> StandardResponse[TerminalInfo]:
        """Retrieve broker terminal/application info."""
        if not (self.capabilities & BrokerCapability.TERMINAL_INFO):
            return self._unsupported("terminal info")
        return StandardResponse.success(
            data=TerminalInfo(name=self.name), extensions={"broker": self.name}
        )

    def get_account_info(self) -> StandardResponse[AccountInfo]:
        """Retrieve trading account details and balance."""
        if not (self.capabilities & BrokerCapability.ACCOUNT_INFO):
            return self._unsupported("account info")
        return StandardResponse.success(
            data=AccountInfo(), extensions={"broker": self.name}
        )

    # ------------------------------------------------------------------------
    # 3. Symbols & Market Instruments
    # ------------------------------------------------------------------------

    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve specifications and details for a given symbol."""
        if not (self.capabilities & BrokerCapability.SYMBOLS):
            return self._unsupported("symbol info")
        return self._unsupported("symbol info")

    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Get the total count of symbols available."""
        if not (self.capabilities & BrokerCapability.SYMBOLS):
            return self._unsupported("symbol listing")
        return StandardResponse.success(data=0, extensions={"broker": self.name})

    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve symbol list, optionally filtered by group or mask."""
        if not (self.capabilities & BrokerCapability.SYMBOLS):
            return self._unsupported("symbol listing")
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    def enable_symbol(self, symbol: str, enable: bool = True) -> StandardResponse[bool]:
        """Enable or disable symbol in Market Watch / subscription."""
        if not (self.capabilities & BrokerCapability.SYMBOLS):
            return self._unsupported("symbol selection")
        return StandardResponse.success(data=True, extensions={"broker": self.name})

    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Get the latest real-time tick for a symbol."""
        if not (self.capabilities & BrokerCapability.MARKET_DATA):
            return self._unsupported("market data")
        return self._unsupported("tick retrieval")

    # ------------------------------------------------------------------------
    # 4. Market Depth (Level 2)
    # ------------------------------------------------------------------------

    def subscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Subscribe to Depth of Market (DOM) book for a symbol."""
        if not (self.capabilities & BrokerCapability.MARKET_DEPTH):
            return self._unsupported("market depth")
        return self._unsupported("market depth subscription")

    def get_market_depth(self, symbol: str) -> StandardResponse[list[BookItem]]:
        """Get current Depth of Market (DOM) order book entries."""
        if not (self.capabilities & BrokerCapability.MARKET_DEPTH):
            return self._unsupported("market depth")
        return self._unsupported("market depth snapshot")

    def unsubscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Unsubscribe from Depth of Market (DOM) book."""
        if not (self.capabilities & BrokerCapability.MARKET_DEPTH):
            return self._unsupported("market depth")
        return self._unsupported("market depth unsubscription")

    # ------------------------------------------------------------------------
    # 5. Bars & Ticks (Historical Data)
    # ------------------------------------------------------------------------

    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars."""
        if not (self.capabilities & BrokerCapability.MARKET_DATA):
            return self._unsupported("market data")
        return self._unsupported("bar history")

    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve historical tick data."""
        if not (self.capabilities & BrokerCapability.MARKET_DATA):
            return self._unsupported("market data")
        return self._unsupported("tick history")

    # ------------------------------------------------------------------------
    # 6. Positions
    # ------------------------------------------------------------------------

    def get_position_info(
        self, symbol: str | None = None, ticket: int | None = None
    ) -> StandardResponse[list[PositionInfo]]:
        """Retrieve open positions, optionally filtered by symbol or ticket."""
        if not (self.capabilities & BrokerCapability.POSITIONS):
            return self._unsupported("position")
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    def get_num_positions(self) -> StandardResponse[int]:
        """Get the total number of currently open positions."""
        if not (self.capabilities & BrokerCapability.POSITIONS):
            return self._unsupported("position")
        return StandardResponse.success(data=0, extensions={"broker": self.name})

    # ------------------------------------------------------------------------
    # 7. Orders
    # ------------------------------------------------------------------------

    def get_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[OrderInfo]]:
        """Retrieve active pending orders."""
        if not (self.capabilities & BrokerCapability.ORDERS):
            return self._unsupported("orders")
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    def get_num_orders(self) -> StandardResponse[int]:
        """Get the total number of active pending orders."""
        if not (self.capabilities & BrokerCapability.ORDERS):
            return self._unsupported("orders")
        return StandardResponse.success(data=0, extensions={"broker": self.name})

    # ------------------------------------------------------------------------
    # 8. Trade History (Orders & Deals)
    # ------------------------------------------------------------------------

    def get_history_order_info(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket: int | None = None,
        position: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[OrderInfo]]:
        """Retrieve historical order records."""
        if not (self.capabilities & BrokerCapability.HISTORY):
            return self._unsupported("history")
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    def get_num_history_orders(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> StandardResponse[int]:
        """Get the total count of historical orders within time range."""
        if not (self.capabilities & BrokerCapability.HISTORY):
            return self._unsupported("history")
        return StandardResponse.success(data=0, extensions={"broker": self.name})

    def get_history_deal_info(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket: int | None = None,
        position: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[DealInfo]]:
        """Retrieve historical deal/transaction records."""
        if not (self.capabilities & BrokerCapability.HISTORY):
            return self._unsupported("history")
        return StandardResponse.success(data=[], extensions={"broker": self.name})

    def get_num_history_deals(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> StandardResponse[int]:
        """Get the total count of historical deals within time range."""
        if not (self.capabilities & BrokerCapability.HISTORY):
            return self._unsupported("history")
        return StandardResponse.success(data=0, extensions={"broker": self.name})

    # ------------------------------------------------------------------------
    # 9. Margin & Profit Calculations
    # ------------------------------------------------------------------------

    def calculate_margin(
        self,
        action: OrderType | str | int,
        symbol: str,
        volume: float,
        price: float,
    ) -> StandardResponse[float]:
        """Calculate required margin for an order in the account currency."""
        if not (self.capabilities & BrokerCapability.CALCULATIONS):
            return self._unsupported("margin calculation")
        return self._unsupported("margin calculation")

    def calculate_profit(
        self,
        action: OrderType | str | int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> StandardResponse[float]:
        """Calculate potential profit/loss for a position."""
        if not (self.capabilities & BrokerCapability.CALCULATIONS):
            return self._unsupported("profit calculation")
        return self._unsupported("profit calculation")

    # ------------------------------------------------------------------------
    # 10. Pre-check & Trade Execution
    # ------------------------------------------------------------------------

    def check_order(self, request: TradeRequest) -> StandardResponse[OrderCheckResult]:
        """Perform pre-flight verification of a trade request before sending."""
        if not (self.capabilities & BrokerCapability.TRADING):
            return self._unsupported("trading")
        return self._unsupported("order check")

    def trade(self, request: TradeRequest) -> StandardResponse[TradeResult]:
        """Execute a trade order (deal, pending order, modify, or close)."""
        if not (self.capabilities & BrokerCapability.TRADING):
            return self._unsupported("trading")
        return self._unsupported("trading")
