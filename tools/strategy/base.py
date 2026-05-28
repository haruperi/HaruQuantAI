"""Base classes for HaruQuant strategy implementations.

Classes:
    - BaseStrategy
    - VectorizedSignalStrategy
    - StatefulEventStrategy

These classes are not AI tools. They provide deterministic strategy contracts
used by strategy implementations and simulation/live workflow adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from tools.strategy.contracts import (
    SignalDict,
    StrategyContext,
    StrategyEvent,
    TradeAction,
)
from tools.utils import logger
from tools.utils.validators import ensure_signal_columns


class BaseStrategy(ABC):
    """Abstract base class for all HaruQuant trading strategies."""

    strategy_name = "BaseStrategy"
    strategy_type = "base"
    signal_schema_version = "1.0"
    action_schema_version = "1.0"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        """Initialize strategy parameters, symbol, ID, and state."""
        self.params: dict[str, Any] = dict(params or {})
        self.symbol = str(self.params.get("symbol", "UNKNOWN") or "UNKNOWN")
        self.strategy_id = str(self.params.get("strategy_id", self.__class__.__name__))
        self.state: dict[str, Any] = {}
        logger.info(
            "strategy initialized | class=%s | strategy_id=%s | symbol=%s",
            self.__class__.__name__,
            self.strategy_id,
            self.symbol,
        )

    @abstractmethod
    def on_init(self) -> None:
        """Initialize or validate strategy state before execution."""

    @abstractmethod
    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return market data with deterministic signal columns added."""

    def on_tick(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process tick data when an engine supports tick execution."""
        return data.copy(deep=True)

    def on_trade(self, event: StrategyEvent) -> None:
        """Handle trade lifecycle events when supplied by an engine."""
        return None

    def on_order_update(self, event: StrategyEvent) -> None:
        """Handle order lifecycle events when supplied by an engine."""
        return None

    def on_timer(self, event: StrategyEvent) -> None:
        """Handle timer events when supplied by an engine."""
        return None

    def on_shutdown(self, event: StrategyEvent | None = None) -> None:
        """Handle clean shutdown events when supplied by an engine."""
        return None

    def get_signal(self, data: pd.DataFrame, index: int) -> SignalDict | None:
        """Return the signal dictionary for a specific processed bar."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame.")
        if index < 0 or index >= len(data):
            raise ValueError("index is out of range.")
        row = data.iloc[index]
        entry = int(row.get("entry_signal", 0) or 0)
        exit_signal = int(row.get("exit_signal", 0) or 0)
        pending = int(row.get("pending_signal", 0) or 0)
        cancel = int(row.get("cancel_pending_signal", 0) or 0)
        pending_2 = int(row.get("pending_signal_2", 0) or 0)
        cancel_2 = int(row.get("cancel_pending_signal_2", 0) or 0)
        if all(
            value == 0
            for value in (entry, exit_signal, pending, cancel, pending_2, cancel_2)
        ):
            return None
        price = row.get("price")
        if pd.isna(price):
            price = row.get("close")
        stop_loss = row.get("stop_loss", row.get("sl"))
        take_profit = row.get("take_profit", row.get("tp"))
        return {
            "entry_signal": entry,
            "exit_signal": exit_signal,
            "pending_signal": pending,
            "cancel_pending_signal": cancel,
            "pending_signal_2": pending_2,
            "cancel_pending_signal_2": cancel_2,
            "price": float(price) if price is not None and pd.notna(price) else None,
            "price_2": _optional_float(row.get("price_2")),
            "time": data.index[index],
            "reason": str(row.get("signal_reason", "") or "Signal detected"),
            "stop_loss": _optional_float(stop_loss),
            "take_profit": _optional_float(take_profit),
            "setup_id": _optional_str(row.get("setup_id")),
            "group_id": _optional_str(row.get("group_id")),
        }

    @staticmethod
    def crossover(series1: pd.Series, series2: pd.Series) -> bool:
        """Return True when series1 crosses above series2 on the latest bar."""
        if len(series1) < 2 or len(series2) < 2:
            return False
        return bool(
            series1.iloc[-2] <= series2.iloc[-2] and series1.iloc[-1] > series2.iloc[-1]
        )

    @staticmethod
    def crossunder(series1: pd.Series, series2: pd.Series) -> bool:
        """Return True when series1 crosses below series2 on the latest bar."""
        if len(series1) < 2 or len(series2) < 2:
            return False
        return bool(
            series1.iloc[-2] >= series2.iloc[-2] and series1.iloc[-1] < series2.iloc[-1]
        )


class VectorizedSignalStrategy(BaseStrategy):
    """Base class for DataFrame-driven vectorized signal strategies."""

    strategy_type = "vectorized"

    def prepare_output(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a copied DataFrame containing canonical signal columns."""
        return ensure_signal_columns(data)


class StatefulEventStrategy(BaseStrategy):
    """Base class for event-driven strategies that propose TradeAction objects."""

    strategy_type = "stateful"

    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """Stateful strategies may return neutral signal columns for bar data."""
        return ensure_signal_columns(data)

    def on_event(self, context: StrategyContext) -> list[TradeAction]:
        """Return proposed actions for a stateful strategy event context."""
        return []


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value) or value == 0:
        return None
    return float(value)


def _optional_str(value: Any) -> str | None:
    if value is None or value == "" or pd.isna(value):
        return None
    return str(value)
