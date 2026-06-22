"""Base Strategy abstract class and structural contracts (Protocols)."""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

import pandas as pd

from app.services.strategy.models import StrategyConfig, StrategyContext, TradeIntent

TConfig = TypeVar("TConfig", bound=StrategyConfig)
TState = TypeVar("TState")


class BaseStrategy(ABC, Generic[TConfig, TState]):  # noqa: UP046
    """Abstract base class for all strategy implementations.

    All strategies (batch/vectorized and event-driven/stateful) should
    inherit from this class to ensure contract compliance.
    """

    def __init__(self, config: TConfig) -> None:
        """Initialize the strategy with its configuration.

        Args:
            config: Pydantic model containing strategy parameters.
        """
        self.config: TConfig = config

    @abstractmethod
    def on_init(self) -> TState:
        """Lifecycle hook to initialize the strategy's internal state.

        Returns:
            TState: The initial state of the strategy.
        """

    @abstractmethod
    def on_bar(
        self, state: TState, bar_data: dict[str, Any], context: StrategyContext
    ) -> tuple[TState, list[TradeIntent]]:
        """Lifecycle hook for bar-based event-driven execution.

        Args:
            state: The current strategy state.
            bar_data: Dictionary representing the latest bar data.
            context: The runtime environment context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Updated state and emitted intents.
        """

    @abstractmethod
    def on_tick(
        self, state: TState, tick_data: dict[str, Any], context: StrategyContext
    ) -> tuple[TState, list[TradeIntent]]:
        """Lifecycle hook for tick-based event-driven execution.

        Args:
            state: The current strategy state.
            tick_data: Dictionary representing the latest tick data.
            context: The runtime environment context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Updated state and emitted intents.
        """

    @abstractmethod
    def on_stop(
        self, state: TState, context: StrategyContext
    ) -> tuple[TState, list[TradeIntent]]:
        """Lifecycle hook for cleanup and shutdown logic.

        Args:
            state: The current strategy state.
            context: The runtime environment context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Final state and cleanup intents.
        """

    @abstractmethod
    def on_exception(
        self, state: TState, error: Exception, context: StrategyContext
    ) -> tuple[TState, list[TradeIntent]]:
        """Lifecycle hook for error handling and recovery logic.

        Args:
            state: The current strategy state.
            error: The raised exception object.
            context: The runtime environment context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Recovered state and recovery
              intents.
        """

    @abstractmethod
    def on_timer(
        self,
        state: TState,
        timer_event: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Lifecycle hook for time-based trigger logic.

        Args:
            state: The current strategy state.
            timer_event: Dictionary describing the timer event.
            context: The runtime environment context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Updated state and emitted intents.
        """

    @abstractmethod
    def calculate_vectorized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch indicator and signal calculation over historical data.

        Calculates signal series across DataFrames in a strictly vectorized
        manner (no iterative row-by-row logic).

        Args:
            df: Historical price data (OHLCV).

        Returns:
            pd.DataFrame: DataFrame containing indicator values and a 'signal'
              column (e.g. +1 for BUY, -1 for SELL, 0 for FLAT).
        """


@runtime_checkable
class StrategyProtocol(Protocol):
    """Structural contract ensuring compliance of strategy implementations."""

    @property
    def config(self) -> StrategyConfig:
        """The configuration of the strategy."""
        ...

    def on_init(self) -> object:
        """Initialize the state."""
        ...

    def on_bar(
        self, state: object, bar_data: dict[str, Any], context: StrategyContext
    ) -> tuple[object, list[TradeIntent]]:
        """Handle bar event."""
        ...

    def on_tick(
        self, state: object, tick_data: dict[str, Any], context: StrategyContext
    ) -> tuple[object, list[TradeIntent]]:
        """Handle tick event."""
        ...

    def on_stop(
        self, state: object, context: StrategyContext
    ) -> tuple[object, list[TradeIntent]]:
        """Handle strategy shutdown."""
        ...

    def on_exception(
        self, state: object, error: Exception, context: StrategyContext
    ) -> tuple[object, list[TradeIntent]]:
        """Handle strategy exception."""
        ...

    def on_timer(
        self, state: object, timer_event: dict[str, Any], context: StrategyContext
    ) -> tuple[object, list[TradeIntent]]:
        """Handle strategy timer event."""
        ...

    def calculate_vectorized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals from historical DataFrame."""
        ...
