"""Typed strategy contracts shared by HaruQuant strategy implementations.

This file contains data contracts and enums used by vectorized and stateful
strategies. It contains no official AI tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal, TypedDict

import pandas as pd


class SignalSide(int, Enum):
    """Canonical directional signal values used in strategy DataFrames."""

    BUY = 1
    SELL = -1
    NONE = 0


class TradeActionType(str, Enum):
    """Supported action intents proposed by stateful strategies."""

    OPEN = "OPEN"
    CLOSE = "CLOSE"
    REDUCE = "REDUCE"
    MODIFY_SL = "MODIFY_SL"
    MODIFY_TP = "MODIFY_TP"
    MOVE_TO_BREAKEVEN = "MOVE_TO_BREAKEVEN"
    HOLD = "HOLD"


class OrderType(str, Enum):
    """Supported order-intent types for strategy signals."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class SignalDict(TypedDict, total=False):
    """Dictionary contract returned by BaseStrategy.get_signal."""

    entry_signal: int
    exit_signal: int
    pending_signal: int
    cancel_pending_signal: int
    pending_signal_2: int
    cancel_pending_signal_2: int
    price: float | None
    price_2: float | None
    stop_loss: float | None
    take_profit: float | None
    reason: str | None
    setup_id: str | None
    group_id: str | None
    time: Any


class StrategyEvent(TypedDict, total=False):
    """Canonical strategy lifecycle or execution event payload."""

    event_id: str
    event_type: str
    symbol: str
    strategy_id: str
    event_ts: Any
    recv_ts: Any
    payload: dict[str, Any]
    run_id: str
    trace_id: str
    correlation_id: str


class SignalIntent(TypedDict, total=False):
    """Canonical strategy signal intent passed to execution boundaries."""

    action: Literal["BUY", "SELL", "EXIT", "REDUCE", "HOLD"]
    qty: float | None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    price: float | None
    time_in_force: Literal["GTC", "IOC", "FOK", "DAY"]
    strategy_id: str
    symbol: str
    reason: str | None
    features: dict[str, Any]
    confidence: float | None
    tags: list[str]
    metadata: dict[str, Any]
    timestamp: Any


@dataclass(frozen=True)
class PositionSnapshot:
    """Immutable snapshot of an open position available to a stateful strategy."""

    ticket: str
    symbol: str
    side: Literal["BUY", "SELL"]
    volume: float
    open_price: float
    opened_at: Any = None
    profit_loss: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    setup_id: str | None = None
    group_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the position snapshot to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class TradeAction:
    """
    Action intent proposed by a stateful strategy.

    TradeAction is not broker execution. It is a deterministic proposal that
    must be validated by risk and execution layers before any live action.
    """

    action_type: Literal[
        "OPEN",
        "CLOSE",
        "REDUCE",
        "MODIFY_SL",
        "MODIFY_TP",
        "MOVE_TO_BREAKEVEN",
        "HOLD",
    ]
    symbol: str
    side: Literal["BUY", "SELL"] | None = None
    volume: float | None = None
    ticket: str | None = None
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] = "MARKET"
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    setup_id: str | None = None
    group_id: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the action to a dictionary for audit or tool responses."""
        return asdict(self)


@dataclass
class StrategyContext:
    """Runtime context supplied to stateful event-driven strategies."""

    strategy_id: str
    symbol: str
    market_data: pd.DataFrame
    current_tick: dict[str, Any] = field(default_factory=dict)
    positions: list[PositionSnapshot] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def positions_for_symbol(self, symbol: str | None = None) -> list[PositionSnapshot]:
        """Return context positions filtered by symbol."""
        target = symbol or self.symbol
        return [position for position in self.positions if position.symbol == target]


class StatefulStrategyMixin:
    """Mixin declaring that a strategy can respond to event contexts."""

    def on_event(self, context: StrategyContext) -> list[TradeAction]:
        """Return proposed trade actions for the supplied strategy context."""
        return []
