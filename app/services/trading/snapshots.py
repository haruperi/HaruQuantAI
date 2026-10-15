"""Immutable dataclass snapshots of trading accounts, symbols, and orders.

Description:
    Provides strongly typed immutable value objects and dataclasses matching MQL5
    data structures, including account, terminal, symbol, position, order, and deal
    snapshots, as well as trade request and result containers.

Purpose:
    FEAT-TRADING-SNAPSHOTS: Strongly typed market and account snapshot objects.

Key Capabilities:
    - FR-TRADING-MARKET-SNAPSHOTS: Immutable account, symbol, and order records.
      Associated: `AccountSnapshot`, `TerminalSnapshot`, `SymbolSnapshot`,
        `PositionSnapshot`, `OrderSnapshot`, `DealSnapshot`, `BookInfo`.
      Logging: Pure in-memory data structures with zero logging overhead.
    - FR-TRADING-ORDER-REQUESTS: Structured trade requests and verification results.
      Associated: `TradeRequest`, `TradeResult`, `TradeCheckResult`.
      Logging: Pure data structures with zero logging overhead.

Python API Usage:
    ```python
    from app.services.trading.snapshots import (
        AccountSnapshot,
        TradeRequest,
        TradeResult,
    )

    account = AccountSnapshot(login=12345, balance=10000.0)
    req = TradeRequest(symbol="EURUSD", volume=0.01)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.snapshots
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.host.logging import get_logger

from .enums import (
    BOOK_TYPE_DESCRIPTIONS,
    AccountTradeMode,
    BookType,
    MarginMode,
    OrderFilling,
    OrderTime,
    OrderType,
    StopoutMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    TradeAction,
    TradeRetcode,
)

__all__ = [
    "AccountSnapshot",
    "BookInfo",
    "DealSnapshot",
    "HistoryOrderSnapshot",
    "MqlBookInfo",
    "OrderSnapshot",
    "PositionSnapshot",
    "SymbolSnapshot",
    "SymbolSpec",
    "TerminalSnapshot",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
]

logger = get_logger(__name__)


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

    @property
    def selected(self) -> bool:
        """Alias for select."""
        return self.select

    @selected.setter
    def selected(self, value: bool) -> None:
        self.select = value

    @property
    def ticks_book_depth(self) -> int:
        """Alias for ticks_bookdepth."""
        return self.ticks_bookdepth

    @ticks_book_depth.setter
    def ticks_book_depth(self, value: int) -> None:
        self.ticks_bookdepth = value

    @property
    def trade_execution(self) -> SymbolTradeExecution:
        """Symbol trade execution policy enum."""
        return (
            SymbolTradeExecution(self.trade_exemode)
            if self.trade_exemode in SymbolTradeExecution._value2member_map_
            else SymbolTradeExecution.MARKET
        )

    @trade_execution.setter
    def trade_execution(self, value: SymbolTradeExecution | int) -> None:
        self.trade_exemode = int(value)


SymbolSpec = SymbolSnapshot


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


def main() -> None:
    """Demonstrate trading snapshots and request structures."""
    account = AccountSnapshot(login=12345, balance=10000.0, equity=10000.0)
    print(f"Account: login={account.login}, balance={account.balance}")
    req = TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.01)
    print(
        f"TradeRequest: action={req.action}, symbol={req.symbol}, volume={req.volume}"
    )


if __name__ == "__main__":
    main()
