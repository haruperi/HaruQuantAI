"""Production-ready trend-following vectorized strategy example.

This vectorized strategy preserves the uploaded running strategy concept while
using the standardized HaruQuant strategy contracts and signal schema.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from tools.strategy.base import VectorizedSignalStrategy
from tools.utils import logger
from tools.utils.validators import assert_ohlc_dataframe, ensure_signal_columns


class TrendFollowingStrategy(VectorizedSignalStrategy):
    """EMA crossover trend-following strategy with slow EMA trend filter."""

    strategy_name = "TrendFollowingStrategy"
    strategy_type = "vectorized"
    signal_schema_version = "1.0"
    action_schema_version = "1.0"

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        """Initialize EMA periods and validate strategy parameters."""
        super().__init__(params)
        self.fast_period = int(self.params.get("fast_period", 20))
        self.slow_period = int(self.params.get("slow_period", 50))
        self.filter_period = int(self.params.get("filter_period", 200))
        self.price_column = str(self.params.get("price_column", "close"))
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate EMA periods and column settings."""
        if self.fast_period <= 0 or self.slow_period <= 0 or self.filter_period <= 0:
            raise ValueError("EMA periods must be positive.")
        if not self.fast_period < self.slow_period <= self.filter_period:
            raise ValueError(
                "EMA periods must satisfy fast_period < slow_period <= filter_period."
            )
        if not self.price_column:
            raise ValueError("price_column is required.")

    def on_init(self) -> None:
        """Log strategy initialization."""
        logger.info(
            "%s initialized | symbol=%s | fast=%s | slow=%s | filter=%s",
            self.strategy_name,
            self.symbol,
            self.fast_period,
            self.slow_period,
            self.filter_period,
        )

    def on_bar(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate shifted EMA crossover signals without mutating input data.

        Signals use previous completed bar indicator values to avoid same-bar
        lookahead when the next open is used as the reference execution price.
        """
        assert_ohlc_dataframe(data, min_rows=self.filter_period + 2)
        if self.price_column not in data.columns:
            raise ValueError(f"price_column {self.price_column!r} is missing.")
        out = ensure_signal_columns(data)
        price = pd.to_numeric(out[self.price_column], errors="coerce")
        fast_col = f"ema_{self.fast_period}"
        slow_col = f"ema_{self.slow_period}"
        filter_col = f"ema_{self.filter_period}"
        out[fast_col] = (
            price.ewm(span=self.fast_period, adjust=False, min_periods=self.fast_period)
            .mean()
            .shift(1)
        )
        out[slow_col] = (
            price.ewm(span=self.slow_period, adjust=False, min_periods=self.slow_period)
            .mean()
            .shift(1)
        )
        out[filter_col] = (
            price.ewm(
                span=self.filter_period, adjust=False, min_periods=self.filter_period
            )
            .mean()
            .shift(1)
        )
        prev_fast = out[fast_col].shift(1)
        prev_slow = out[slow_col].shift(1)
        cross_up = (out[fast_col] > out[slow_col]) & (prev_fast <= prev_slow)
        cross_down = (out[fast_col] < out[slow_col]) & (prev_fast >= prev_slow)
        trend_buy = out[slow_col] > out[filter_col]
        trend_sell = out[slow_col] < out[filter_col]
        out.loc[cross_up, "exit_signal"] = -1
        out.loc[cross_down, "exit_signal"] = 1
        out.loc[cross_up & trend_buy, "entry_signal"] = 1
        out.loc[cross_down & trend_sell, "entry_signal"] = -1
        out.loc[cross_up | cross_down, "price"] = out.loc[cross_up | cross_down, "open"]
        out.loc[cross_up & trend_buy, "signal_reason"] = (
            f"EMA({self.fast_period}) crossed above EMA({self.slow_period}) "
            f"with EMA({self.filter_period}) filter"
        )
        out.loc[cross_down & trend_sell, "signal_reason"] = (
            f"EMA({self.fast_period}) crossed below EMA({self.slow_period}) "
            f"with EMA({self.filter_period}) filter"
        )
        return out
