"""Working SQX-style breakout strategy built on the common template."""

from __future__ import annotations

import pandas as pd

from app.services.strategy import (
    Direction,
    MarketContext,
    ProtectionRequest,
)
from app.services.strategy.base import BaseStrategy


class SQXBreakoutAtrTrailingStrategy(BaseStrategy):
    """Opening breakout with ATR stop-loss and trailing-stop proposals."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate SQX-style entry signals in a vectorized way."""
        del context
        lookback = int(self.config.parameter("breakout_lookback"))

        # Channel breakout values
        highest_signal = df["high"].shift(1).rolling(window=lookback).max()
        lowest_signal = df["low"].shift(1).rolling(window=lookback).min()
        highest_prior = df["high"].shift(2).rolling(window=lookback).max()
        lowest_prior = df["low"].shift(2).rolling(window=lookback).min()

        df["long_entry"] = (df["open"] > highest_signal) & (
            df["open"].shift(1) <= highest_prior
        )
        df["short_entry"] = (df["open"] < lowest_signal) & (
            df["open"].shift(1) >= lowest_prior
        )
        df["long_exit"] = False
        df["short_exit"] = False

        # Precalculate ATR columns for trailing SL distance in build_protection_request
        from app.services.indicators import ATR

        atr_stop_period = int(self.config.parameter("atr_stop_period"))
        trailing_stop_atr_period = int(
            self.config.parameter("trailing_stop_atr_period")
        )
        trailing_activation_atr_period = int(
            self.config.parameter("trailing_activation_atr_period")
        )

        df = ATR().calculate(df, period=atr_stop_period)
        df = ATR().calculate(df, period=trailing_stop_atr_period)
        df = ATR().calculate(df, period=trailing_activation_atr_period)

        return df

    def build_protection_request(
        self, context: MarketContext, direction: Direction
    ) -> ProtectionRequest:
        """Build distances from the configured ATR formulas for either direction."""
        del direction
        return ProtectionRequest(
            stop_loss_distance=self._atr_multiple(
                context,
                period_parameter="atr_stop_period",
                multiplier_parameter="stop_loss_atr_multiple",
            ),
            trailing_distance=self._atr_multiple(
                context,
                period_parameter="trailing_stop_atr_period",
                multiplier_parameter="trailing_stop_atr_multiple",
            ),
            trailing_activation_distance=self._atr_multiple(
                context,
                period_parameter="trailing_activation_atr_period",
                multiplier_parameter="trailing_activation_atr_multiple",
            ),
        )

    def _atr_multiple(
        self,
        context: MarketContext,
        period_parameter: str,
        multiplier_parameter: str,
    ) -> float:
        period = int(self.config.parameter(period_parameter))
        multiplier = float(self.config.parameter(multiplier_parameter))

        current_idx = len(context.bars) - 1
        if self.df_signals is not None and 0 <= current_idx < len(self.df_signals):
            val = self.df_signals.iloc[current_idx][f"atr_{period}"]
            if pd.isna(val):
                msg = f"ATR({period}) has insufficient completed bars."
                raise ValueError(msg)
            return float(val) * multiplier
        msg = f"ATR({period}) has insufficient completed bars."
        raise ValueError(msg)
