"""TrendFollowing Strategy robot implementation."""

import uuid
from typing import Any, ClassVar

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.services.strategy.base import BaseStrategy
from app.services.strategy.models import (
    OrderSide,
    OrderType,
    StrategyConfig,
    StrategyContext,
    TradeIntent,
)


class TrendFollowingState(BaseModel):
    """Pydantic model representing state of TrendFollowingStrategy."""

    position: str = Field(
        default="FLAT", description="Active position state: LONG, SHORT, or FLAT"
    )


class TrendFollowingStrategy(
    BaseStrategy[StrategyConfig, TrendFollowingState]
):
    """Concrete Strategy: Trend Following.

    Buys on golden crosses filtered by trend filter (EMA 200).
    Sells on death crosses filtered by trend filter.
    """

    config_strategy: ClassVar[dict[str, Any] | None] = {
        "strategy_id": "trend_following",
        "version": "1.0.0",
        "lifecycle_status": "RESEARCH",
        "permitted_environments": ["BACKTEST", "REPLAY"],
        "risk_profile": {},
        "title": "TrendFollowingConfig",
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "default": "UNKNOWN",
                "description": "The ticker symbol to trade.",
            },
            "fast_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "step": 1,
                "default": 20,
                "description": "The period for the fast EMA.",
            },
            "slow_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 250,
                "step": 1,
                "default": 50,
                "description": "The period for the slow EMA.",
            },
            "filter_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "step": 1,
                "default": 200,
                "description": "The period for the trend filter EMA.",
            },
        },
        "required": ["symbol", "fast_period", "slow_period", "filter_period"],
    }

    def on_init(self) -> TrendFollowingState:
        """Initialize TrendFollowing state."""
        return TrendFollowingState()

    def on_bar(
        self,
        state: TrendFollowingState,
        _bar_data: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Hook for bar-based event execution."""
        symbol = self.config.parameters.get("symbol", "UNKNOWN")
        fast_period = self.config.parameters.get("fast_period", 20)
        slow_period = self.config.parameters.get("slow_period", 50)
        filter_period = self.config.parameters.get("filter_period", 200)

        # Retrieve history from market snapshot
        history = context.market_snapshot.get(symbol)
        min_required_len = filter_period + 5
        if (
            history is None
            or not isinstance(history, pd.DataFrame)
            or len(history) < min_required_len
        ):
            return state, []

        # Sort and get closes
        df = history.sort_index()
        close = df["close"]

        # Calculate EMAs using ewm
        fast_ma = close.ewm(span=fast_period, adjust=False).mean()
        slow_ma = close.ewm(span=slow_period, adjust=False).mean()
        filter_ma = close.ewm(span=filter_period, adjust=False).mean()

        # Check values at index -2 and -3 to avoid lookahead bias
        f_curr, s_curr, filt_curr = (
            fast_ma.iloc[-2],
            slow_ma.iloc[-2],
            filter_ma.iloc[-2],
        )
        f_prev, s_prev, _ = (
            fast_ma.iloc[-3],
            slow_ma.iloc[-3],
            filter_ma.iloc[-3],
        )

        # Handle NaNs
        if pd.isna(f_curr) or pd.isna(s_curr) or pd.isna(filt_curr):
            return state, []
        if pd.isna(f_prev) or pd.isna(s_prev):
            return state, []

        # Crossovers
        cross_up = f_prev <= s_prev and f_curr > s_curr
        cross_down = f_prev >= s_prev and f_curr < s_curr
        uid_str = str(uuid.uuid4())[:8]

        return self._evaluate_signals(
            state=state,
            cross_up=cross_up,
            cross_down=cross_down,
            s_curr=float(s_curr),
            filt_curr=float(filt_curr),
            symbol=symbol,
            uid_str=uid_str,
            context=context,
        )

    def _evaluate_signals(
        self,
        state: TrendFollowingState,
        cross_up: bool,
        cross_down: bool,
        s_curr: float,
        filt_curr: float,
        symbol: str,
        uid_str: str,
        context: StrategyContext,
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Evaluate crossover/filter signals to decide state transitions."""
        intents: list[TradeIntent] = []
        new_state = state.model_copy()

        if new_state.position == "FLAT":
            if cross_up and s_curr > filt_curr:
                intent = TradeIntent(
                    intent_id=f"intent_trend_buy_{uid_str}",
                    decision_id=f"dec_trend_{uid_str}",
                    idempotency_key=f"ikey_trend_buy_{uid_str}",
                    strategy_id=self.config.strategy_id,
                    strategy_version=self.config.strategy_version,
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=1.0,
                    signal_timestamp=context.current_time,
                    rationale="Fast EMA crossed slow EMA upwards above filter.",
                )
                intents.append(intent)
                new_state.position = "LONG"
            elif cross_down and s_curr < filt_curr:
                intent = TradeIntent(
                    intent_id=f"intent_trend_sell_{uid_str}",
                    decision_id=f"dec_trend_{uid_str}",
                    idempotency_key=f"ikey_trend_sell_{uid_str}",
                    strategy_id=self.config.strategy_id,
                    strategy_version=self.config.strategy_version,
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=1.0,
                    signal_timestamp=context.current_time,
                    rationale="Fast EMA crossed slow EMA downwards below filter.",
                )
                intents.append(intent)
                new_state.position = "SHORT"

        elif new_state.position == "LONG" and cross_down:
            intent = TradeIntent(
                intent_id=f"intent_trend_exit_long_{uid_str}",
                decision_id=f"dec_trend_{uid_str}",
                idempotency_key=f"ikey_trend_exit_long_{uid_str}",
                strategy_id=self.config.strategy_id,
                strategy_version=self.config.strategy_version,
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=1.0,
                signal_timestamp=context.current_time,
                rationale="Fast EMA crossed slow EMA downwards (exit long).",
            )
            intents.append(intent)
            new_state.position = "FLAT"

        elif new_state.position == "SHORT" and cross_up:
            intent = TradeIntent(
                intent_id=f"intent_trend_exit_short_{uid_str}",
                decision_id=f"dec_trend_{uid_str}",
                idempotency_key=f"ikey_trend_exit_short_{uid_str}",
                strategy_id=self.config.strategy_id,
                strategy_version=self.config.strategy_version,
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                signal_timestamp=context.current_time,
                rationale="Fast EMA crossed slow EMA upwards (exit short).",
            )
            intents.append(intent)
            new_state.position = "FLAT"

        return new_state, intents

    def on_tick(
        self,
        state: TrendFollowingState,
        tick_data: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Hook for tick-based event execution (delegates to on_bar)."""
        bar_data = {"close": tick_data.get("last", 0.0)}
        return self.on_bar(state, bar_data, context)

    def on_stop(
        self, state: TrendFollowingState, _context: StrategyContext
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Hook for strategy shutdown."""
        return state, []

    def on_exception(
        self,
        state: TrendFollowingState,
        _error: Exception,
        _context: StrategyContext,
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Hook for handling errors."""
        return state, []

    def on_timer(
        self,
        state: TrendFollowingState,
        _timer_event: dict[str, Any],
        _context: StrategyContext,
    ) -> tuple[TrendFollowingState, list[TradeIntent]]:
        """Hook for timer events."""
        return state, []

    def calculate_vectorized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch indicator and signal calculation over historical data."""
        fast_period = self.config.parameters.get("fast_period", 20)
        slow_period = self.config.parameters.get("slow_period", 50)
        filter_period = self.config.parameters.get("filter_period", 200)

        df_out = df.copy()
        f = df_out["close"].ewm(span=fast_period, adjust=False).mean()
        s = df_out["close"].ewm(span=slow_period, adjust=False).mean()
        filt = df_out["close"].ewm(span=filter_period, adjust=False).mean()

        df_out["fast_ma"] = f
        df_out["slow_ma"] = s
        df_out["filter_ma"] = filt

        cross_up = (f.shift(1) <= s.shift(1)) & (f > s)
        cross_down = (f.shift(1) >= s.shift(1)) & (f < s)

        signals, entry_signals, exit_signals, prices, reasons = (
            self._simulate_vectorized_transitions(
                df_out, cross_up, cross_down, f, s, filt
            )
        )

        n = len(df)
        setup_ids = [""] * n
        group_ids = [""] * n

        # CRITICAL: Shift by 1 to prevent lookahead bias
        df_out["signal"] = (
            pd.Series(signals, index=df.index).shift(1).fillna(0.0)
        )
        df_out["entry_signal"] = (
            pd.Series(entry_signals, index=df.index)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        df_out["exit_signal"] = (
            pd.Series(exit_signals, index=df.index)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        df_out["price"] = (
            pd.Series(prices, index=df.index).shift(1).fillna(0.0)
        )
        df_out["reason"] = (
            pd.Series(reasons, index=df.index).shift(1).fillna("")
        )
        df_out["setup_id"] = (
            pd.Series(setup_ids, index=df.index).shift(1).fillna("")
        )
        df_out["group_id"] = (
            pd.Series(group_ids, index=df.index).shift(1).fillna("")
        )

        return df_out

    def _simulate_vectorized_transitions(
        self,
        df: pd.DataFrame,
        cross_up: pd.Series,
        cross_down: pd.Series,
        f: pd.Series,
        s: pd.Series,
        filt: pd.Series,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Simulate the position transitions iteratively over the DataFrame."""
        n = len(df)
        signals = np.zeros(n)
        entry_signals = np.zeros(n, dtype=int)
        exit_signals = np.zeros(n, dtype=int)
        prices = np.zeros(n, dtype=float)
        reasons = [""] * n
        pos = "FLAT"

        for i in range(1, n):
            if pd.isna(f.iloc[i]) or pd.isna(s.iloc[i]) or pd.isna(filt.iloc[i]):
                continue

            if pos == "FLAT":
                if cross_up.iloc[i] and s.iloc[i] > filt.iloc[i]:
                    pos = "LONG"
                    signals[i] = 1.0
                    entry_signals[i] = 1
                    prices[i] = df["close"].iloc[i]
                    reasons[i] = "Fast cross up slow above filter"
                elif cross_down.iloc[i] and s.iloc[i] < filt.iloc[i]:
                    pos = "SHORT"
                    signals[i] = -1.0
                    entry_signals[i] = -1
                    prices[i] = df["close"].iloc[i]
                    reasons[i] = "Fast cross down slow below filter"
            elif pos == "LONG":
                if cross_down.iloc[i]:
                    pos = "FLAT"
                    signals[i] = 0.0
                    exit_signals[i] = 1
                    prices[i] = df["close"].iloc[i]
                    reasons[i] = "Exit long: fast cross down slow"
                else:
                    signals[i] = 1.0
            elif pos == "SHORT":
                if cross_up.iloc[i]:
                    pos = "FLAT"
                    signals[i] = 0.0
                    exit_signals[i] = 1
                    prices[i] = df["close"].iloc[i]
                    reasons[i] = "Exit short: fast cross up slow"
                else:
                    signals[i] = -1.0

        return signals, entry_signals, exit_signals, prices, reasons
