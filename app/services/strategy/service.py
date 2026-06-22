"""Strategy service orchestrating stateful and vectorized execution."""

from datetime import datetime
from typing import Any, TypeVar

import pandas as pd
from loguru import logger

from app.services.strategy.base import BaseStrategy
from app.services.strategy.models import (
    OrderSide,
    OrderType,
    StrategyConfig,
    StrategyContext,
    TradeIntent,
)

TState = TypeVar("TState")


class TradeIntentInspector:
    """Inspector to mathematically and logically validate TradeIntents.

    Specifically inspects intents for forward-looking lookahead risks and
    checks for stale data usage. Also implements perturbation check to verify
    lack of lookahead bias in vectorized strategy calculations.
    """

    def __init__(self, stale_threshold_seconds: float = 60.0) -> None:
        """Initialize the inspector.

        Args:
            stale_threshold_seconds: Max age of signal timestamp in seconds.
        """
        self.stale_threshold_seconds = stale_threshold_seconds

    def inspect_intent(
        self, intent: TradeIntent, market_time: datetime
    ) -> list[str]:
        """Inspects a single TradeIntent for timing issues.

        Args:
            intent: The TradeIntent to validate.
            market_time: The current market time.

        Returns:
            List[str]: Found warning or error messages.
        """
        issues: list[str] = []

        # 1. Lookahead check: signal in the future
        if intent.signal_timestamp > market_time:
            issues.append(
                f"Lookahead Risk: signal_timestamp {intent.signal_timestamp} "
                f"is in the future relative to market time {market_time}."
            )

        # 2. Stale data check: signal is too old
        time_diff = (market_time - intent.signal_timestamp).total_seconds()
        if time_diff > self.stale_threshold_seconds:
            issues.append(
                f"Stale Data: signal timestamp is {time_diff} seconds old "
                f"(threshold: {self.stale_threshold_seconds}s)."
            )

        return issues

    def check_lookahead_bias(
        self,
        strategy: BaseStrategy[Any, Any],
        df: pd.DataFrame,
        perturb_index: int = -1,
    ) -> bool:
        """Verify if perturbing future data alters historical signals.

        Args:
            strategy: The strategy to test.
            df: Historical price data.
            perturb_index: Row index at which to perturb future prices.

        Returns:
            bool: True if lookahead bias is detected, False otherwise.
        """
        min_perturb_len = 5
        if len(df) < min_perturb_len:
            return False

        idx = perturb_index if perturb_index != -1 else len(df) // 2

        # 1. Baseline calculation
        df_base = df.copy()
        try:
            base_signals = strategy.calculate_vectorized_signals(df_base)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error calculating base signals: {e}")
            return True

        # 2. Perturb future data (multiply close by 10)
        df_perturbed = df.copy()
        price_cols = [
            c for c in ["close", "high", "low", "open"] if c in df.columns
        ]

        # Apply multiplier to prices from the perturb index onwards
        for col in price_cols:
            df_perturbed.loc[df_perturbed.index[idx:], col] *= 10.0

        try:
            perturbed_signals = strategy.calculate_vectorized_signals(
                df_perturbed
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error calculating perturbed signals: {e}")
            return True

        # 3. Check for differences before perturb_index
        signal_cols = [
            c
            for c in base_signals.columns
            if "signal" in c or c not in df.columns
        ]
        for col in signal_cols:
            if col not in perturbed_signals.columns:
                continue
            base_slice = base_signals.loc[: base_signals.index[idx - 1], col]
            perturbed_slice = perturbed_signals.loc[
                : perturbed_signals.index[idx - 1], col
            ]
            if not base_slice.equals(perturbed_slice):
                logger.warning(
                    f"Lookahead bias detected in column '{col}'. "
                    f"Perturbation at index {idx} changed signal "
                    f"at earlier index."
                )
                return True

        return False


class StrategyService:
    """Orchestrates strategy execution.

    Designed with side-effect-free (pure) transitions. It takes the current
    strategy state, processes events, and returns updated state and trade
    intents.
    """

    def __init__(self, inspector: TradeIntentInspector | None = None) -> None:
        """Initialize the StrategyService.

        Args:
            inspector: Optional TradeIntentInspector.
        """
        self.inspector = inspector or TradeIntentInspector()

    def process_bar(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        state: TState,
        bar_data: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Process a bar event and return the next state and trade intents.

        Args:
            strategy: The strategy instance.
            state: The current strategy state.
            bar_data: Dict containing the current bar details.
            context: The execution context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Next state and emitted intents.
        """
        next_state, intents = strategy.on_bar(state, bar_data, context)
        self._validate_intents(intents, context.current_time)
        return next_state, intents

    def process_tick(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        state: TState,
        tick_data: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Process a tick event and return the next state and trade intents.

        Args:
            strategy: The strategy instance.
            state: The current strategy state.
            tick_data: Dict containing the current tick details.
            context: The execution context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Next state and emitted intents.
        """
        next_state, intents = strategy.on_tick(state, tick_data, context)
        self._validate_intents(intents, context.current_time)
        return next_state, intents

    def process_stop(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        state: TState,
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Process a strategy shutdown hook.

        Args:
            strategy: The strategy instance.
            state: The current strategy state.
            context: The execution context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Final state and cleanup intents.
        """
        next_state, intents = strategy.on_stop(state, context)
        self._validate_intents(intents, context.current_time)
        return next_state, intents

    def process_exception(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        state: TState,
        error: Exception,
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Process an error raised in execution.

        Args:
            strategy: The strategy instance.
            state: The current strategy state.
            error: The Exception that occurred.
            context: The execution context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Next state and recovery intents.
        """
        next_state, intents = strategy.on_exception(state, error, context)
        self._validate_intents(intents, context.current_time)
        return next_state, intents

    def process_timer(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        state: TState,
        timer_event: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TState, list[TradeIntent]]:
        """Process a timer trigger event.

        Args:
            strategy: The strategy instance.
            state: The current strategy state.
            timer_event: Dict detailing the timer event.
            context: The execution context.

        Returns:
            Tuple[TState, List[TradeIntent]]: Next state and emitted intents.
        """
        next_state, intents = strategy.on_timer(state, timer_event, context)
        self._validate_intents(intents, context.current_time)
        return next_state, intents

    def process_vectorized(
        self,
        strategy: BaseStrategy[StrategyConfig, TState],
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[TradeIntent]]:
        """Orchestrate a vectorized historical run.

        Checks for lookahead bias and extracts generated signals as TradeIntents.

        Args:
            strategy: The strategy instance.
            df: Historical price DataFrame (OHLCV).

        Returns:
            Tuple[pd.DataFrame, List[TradeIntent]]: Result DataFrame and
              emitted TradeIntents.
        """
        if self.inspector.check_lookahead_bias(strategy, df):
            logger.warning("Strategy has potential lookahead bias!")

        df_signals = strategy.calculate_vectorized_signals(df)

        # Ensure standard required columns exist in the DataFrame
        standard_cols: dict[str, Any] = {
            "entry_signal": 0,
            "exit_signal": 0,
            "price": 0.0,
            "reason": "",
            "setup_id": "",
            "group_id": "",
        }
        for col, default_val in standard_cols.items():
            if col not in df_signals.columns:
                df_signals[col] = default_val

        intents = self._parse_vectorized_signals(
            df_signals,
            strategy.config.strategy_id,
            strategy.config.strategy_version,
        )
        return df_signals, intents

    def _validate_intents(
        self, intents: list[TradeIntent], market_time: datetime
    ) -> None:
        """Helper to run timing validation on a list of intents."""
        for intent in intents:
            issues = self.inspector.inspect_intent(intent, market_time)
            for issue in issues:
                logger.warning(issue)

    def _parse_vectorized_signals(
        self,
        df: pd.DataFrame,
        strategy_id: str,
        strategy_version: str,
    ) -> list[TradeIntent]:
        """Parse signal transitions in a DataFrame into TradeIntents."""
        intents: list[TradeIntent] = []
        if "signal" not in df.columns:
            return intents

        sig = df["signal"].fillna(0.0)
        prev_sig = sig.shift(1).fillna(0.0)

        # Detect changes in signal values
        change_mask = sig != prev_sig
        change_indices = df.index[change_mask]

        for i, idx in enumerate(change_indices):
            current_sig = sig.loc[idx]
            prev_sig_val = prev_sig.loc[idx]

            # Resolve datetime
            if isinstance(idx, datetime):
                timestamp = idx
            else:
                timestamp = pd.to_datetime(idx).to_pydatetime()

            if current_sig == 1.0:
                side = OrderSide.BUY
                qty = 1.0
            elif current_sig == -1.0:
                side = OrderSide.SELL
                qty = 1.0
            else:
                # Signal turned to flat. Flip the previous signal to close it.
                side = OrderSide.SELL if prev_sig_val > 0.0 else OrderSide.BUY
                qty = 1.0

            intent_id = f"intent_{strategy_id}_{timestamp.strftime('%Y%m%d%H%M%S')}_{i}"
            decision_id = f"dec_{strategy_id}_{timestamp.strftime('%Y%m%d%H%M%S')}_{i}"

            intent = TradeIntent(
                intent_id=intent_id,
                decision_id=decision_id,
                idempotency_key=f"ikey_{intent_id}",
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                symbol=df["symbol"].iloc[0] if "symbol" in df.columns else "UNKNOWN",
                side=side,
                order_type=OrderType.MARKET,
                quantity=qty,
                signal_timestamp=timestamp,
                rationale=(
                    f"Vectorized signal transition: {prev_sig_val} -> "
                    f"{current_sig}"
                ),
            )
            intents.append(intent)

        return intents
