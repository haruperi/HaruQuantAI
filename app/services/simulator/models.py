"""Typed models for the deterministic bar-by-bar backtest engine.

The backtester is intentionally compact and broker-neutral.  It uses canonical
OHLCV bars, applies strategy ``TradeIntent`` objects, and produces a complete
ledger of fills, closed trades, equity observations, and diagnostics.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.strategy import Direction, EntryType


class IntrabarConflictPolicy(StrEnum):
    """Resolution when the same OHLC bar reaches both SL and TP."""

    STOP_FIRST = "STOP_FIRST"
    TARGET_FIRST = "TARGET_FIRST"


class FillReason(StrEnum):
    """Reason a position or pending order was executed."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    SIGNAL_CLOSE = "SIGNAL_CLOSE"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    STOP_LOSS = "STOP_LOSS"
    PROFIT_TARGET = "PROFIT_TARGET"
    END_OF_TEST = "END_OF_TEST"
    TIME_EXIT = "TIME_EXIT"


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    """Global deterministic assumptions for a single-symbol bar backtest.

    ``point_size`` and ``contract_size`` must describe the supplied instrument.
    For FX, a realistic production simulation should later source these values
    from normalized symbol metadata; this simple module keeps them explicit.
    """

    initial_balance: float = 10_000.0
    point_size: float = 0.00001
    spread_points: float = 10.0
    slippage_points: float = 0.0
    commission_per_unit: float = 0.0
    contract_size: float = 1.0
    default_quantity: float = 1.0
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    intrabar_conflict_policy: IntrabarConflictPolicy = IntrabarConflictPolicy.STOP_FIRST
    close_open_positions_at_end: bool = True
    emit_execution_events: bool = True
    reset_strategy_state: bool = True

    def __post_init__(self) -> None:
        if self.initial_balance < 0:
            raise ValueError("initial_balance cannot be negative.")
        if self.point_size <= 0:
            raise ValueError("point_size must be positive.")
        if self.spread_points < 0 or self.slippage_points < 0:
            raise ValueError("spread_points and slippage_points cannot be negative.")
        if self.contract_size <= 0 or self.default_quantity <= 0:
            raise ValueError("contract_size and default_quantity must be positive.")
        if self.volume_min <= 0 or self.volume_max < self.volume_min or self.volume_step <= 0:
            raise ValueError("Invalid volume constraints.")

    @property
    def spread_price(self) -> float:
        """Return full bid/ask spread in price units."""
        return self.spread_points * self.point_size

    @property
    def slippage_price(self) -> float:
        """Return adverse slippage in price units."""
        return self.slippage_points * self.point_size


@dataclass(slots=True)
class SimPosition:
    """Mutable simulated position owned by the backtest engine."""

    position_id: str
    strategy_id: str
    symbol: str
    direction: Direction
    quantity: float
    entry_price: float
    opened_at: datetime
    opened_bar_index: int
    magic_number: int
    comment: str
    stop_loss_price: float | None = None
    profit_target_price: float | None = None
    trailing_distance: float | None = None
    trailing_activation_distance: float | None = None
    time_exit_bars: int | None = None
    entry_commission: float = 0.0


@dataclass(slots=True)
class SimPendingOrder:
    """Mutable simulated stop/limit order awaiting a bar-path trigger."""

    order_id: str
    strategy_id: str
    symbol: str
    direction: Direction
    entry_type: EntryType
    quantity: float
    requested_price: float
    placed_at: datetime
    activation_bar_index: int
    magic_number: int
    comment: str
    stop_loss_price: float | None = None
    profit_target_price: float | None = None
    stop_loss_distance: float | None = None
    profit_target_distance: float | None = None
    trailing_distance: float | None = None
    trailing_activation_distance: float | None = None
    time_exit_bars: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    """One fully or partially realized position segment."""

    trade_id: str
    position_id: str
    strategy_id: str
    symbol: str
    direction: Direction
    quantity: float
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    gross_pnl: float
    net_pnl: float
    entry_commission: float
    exit_commission: float
    reason: FillReason
    magic_number: int
    comment: str


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Marked-to-market account value after a completed bar."""

    time: datetime
    balance: float
    equity: float
    unrealized_pnl: float
    open_position_count: int
    pending_order_count: int


@dataclass(frozen=True, slots=True)
class BacktestEvent:
    """Auditable simulation event, including fills and ignored intents."""

    time: datetime
    event_type: str
    message: str
    intent_id: str | None = None
    entity_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    """Small result summary intended for first-pass research comparisons."""

    initial_balance: float
    final_balance: float
    net_profit: float
    return_pct: float
    total_closed_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    gross_profit: float
    gross_loss: float
    profit_factor: float | None
    max_drawdown: float
    max_drawdown_pct: float


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Immutable backtest output with enough detail for audit and analytics."""

    strategy_id: str
    symbol: str
    timeframe: str
    started_at: datetime
    ended_at: datetime
    config: BacktestConfig
    closed_trades: tuple[ClosedTrade, ...]
    equity_curve: tuple[EquityPoint, ...]
    events: tuple[BacktestEvent, ...]
    open_positions: tuple[SimPosition, ...]
    pending_orders: tuple[SimPendingOrder, ...]
    metrics: BacktestMetrics
    diagnostics: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly summary without serializing every ledger row."""
        metrics = self.metrics
        return {
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "metrics": {
                "initial_balance": metrics.initial_balance,
                "final_balance": metrics.final_balance,
                "net_profit": metrics.net_profit,
                "return_pct": metrics.return_pct,
                "total_closed_trades": metrics.total_closed_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "win_rate_pct": metrics.win_rate_pct,
                "gross_profit": metrics.gross_profit,
                "gross_loss": metrics.gross_loss,
                "profit_factor": metrics.profit_factor,
                "max_drawdown": metrics.max_drawdown,
                "max_drawdown_pct": metrics.max_drawdown_pct,
            },
            "open_position_count": len(self.open_positions),
            "pending_order_count": len(self.pending_orders),
            "event_count": len(self.events),
            "diagnostics": list(self.diagnostics),
        }
