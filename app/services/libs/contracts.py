"""Domain value objects and contracts for accounts, symbols, orders, and deals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .enums import (
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
)

__all__ = [
    "AccountInfo",
    "BookInfo",
    "DealInfo",
    "OrderInfo",
    "PositionInfo",
    "SymbolInfo",
    "TerminalInfo",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
]


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


@dataclass(slots=True)
class SymbolInfo:
    """Atomic state of symbol specification, execution modes, rates, and spreads."""

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

    def round_to_tick_size(self, price: float) -> float:
        """Round a price to the symbol's minimum tick size."""
        step = self.trade_tick_size if self.trade_tick_size > 0.0 else 0.00001
        return round(round(price / step) * step, self.digits)


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
