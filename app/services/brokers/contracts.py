# ruff: noqa: D101, D102, D103 -- public enum, dataclass, and abstract method contracts.
"""Shared broker execution, state, and symbol specification contracts.

Description:
    Defines low-level broker execution contracts, symbol specifications,
    and broker backend abstraction (BrokerBackend). All public trading
    snapshots, execution requests, and trading enums are owned by
    app.services.libs.trading.

Purpose:
    FEAT-BROKER-CONTRACTS: Low-level broker backend models and records.

Key Capabilities:
    - FR-BROKER-CONTRACTS-RECORDS: Low-level broker order, deal, and position records.
      Associated: `SymbolSpec`, `Tick`, `OrderRecord`, `PositionRecord`, `DealRecord`,
        `BrokerBackend`.
      Logging: Passive model declarations; operational logging belongs to the
        consuming transport and journal, not model construction.

Python API Usage:
    ```python
    from app.services.brokers.contracts import BrokerBackend, SymbolSpec, Tick

    spec = SymbolSpec(name="EURUSD")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading.py --no-cov
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

from app.services.libs.trading import (
    AccountSnapshot,
    OrderFilling,
    OrderTime,
    OrderType,
    TerminalSnapshot,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)

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
#                              ENUMERATIONS
# ****************************************************************************


class PositionType(IntEnum):
    BUY = 0
    SELL = 1


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


POSITION_TYPE_DESCRIPTIONS = {
    PositionType.BUY: "Buy",
    PositionType.SELL: "Sell",
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
    custom: bool = False
    chart_mode: int = 0
    visible: bool = True
    start_time: int = 0
    expiration_time: int = 0
    margin_hedged_use_leg: bool = False
    expiration_mode: int = 7
    filling_mode: int = 1
    order_mode: int = 127
    order_gtc_mode: int = 0
    option_mode: int = 0
    option_right: int = 0
    volume_real: float = 0.0
    volumehigh_real: float = 0.0
    volumelow_real: float = 0.0
    option_strike: float = 0.0
    trade_accrued_interest: float = 0.0
    trade_face_value: float = 0.0
    trade_liquidity_rate: float = 0.0
    session_volume: float = 0.0
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
    exchange: str = ""
    formula: str = ""
    isin: str = ""
    page: str = ""


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

    def symbols(self) -> list[SymbolSpec]:
        """Optional symbol catalog enumeration used by market information lookups."""
        return []

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
