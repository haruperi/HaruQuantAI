"""Naïve moving-average trend-following strategy.

The strategy operates on the main chart's fully completed bars.  It calculates
three simple moving averages: a fast 20-period average, a slow 50-period
average, and a 200-period trend filter.  A long entry is proposed only when the
fast MA crosses above the slow MA *and* the slow MA is above the 200-period
filter.  A long position is closed when the fast MA crosses below the slow MA.

A short entry is proposed only when the fast MA crosses below the slow MA *and*
the slow MA is below the 200-period filter.  A short position is closed when
the fast MA crosses above the slow MA.  The strategy makes no reversal order:
exit and opposite entry are independently resolved through the base conflict
policy.  The Risk Governor determines final quantity and accepts or rejects
all resulting intents.
"""

import pandas as pd
from app.services.strategy import MarketContext
from app.services.strategy.base import BaseStrategy


class NaiveMATrendStrategy(BaseStrategy):
    """20/50 moving-average crossover with a 200-period trend-direction filter."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Calculate entries and exits in a vectorized way on the DataFrame."""
        del context
        fast = int(self.config.parameter("fast_ma_period"))
        slow = int(self.config.parameter("slow_ma_period"))
        trend = int(self.config.parameter("filter_ma_period"))

        from app.services.indicators import sma

        df[f"sma_{fast}"] = sma.calculate(df, period=fast, column="close")
        df[f"sma_{slow}"] = sma.calculate(df, period=slow, column="close")
        df[f"sma_{trend}"] = sma.calculate(df, period=trend, column="close")

        fast_ma = df[f"sma_{fast}"]
        slow_ma = df[f"sma_{slow}"]
        trend_ma = df[f"sma_{trend}"]

        fast_prev = fast_ma.shift(1)
        slow_prev = slow_ma.shift(1)

        up_cross = (fast_ma > slow_ma) & (fast_prev <= slow_prev)
        down_cross = (fast_ma < slow_ma) & (fast_prev >= slow_prev)

        df["long_entry"] = (up_cross & (slow_ma > trend_ma)).astype(int)
        df["short_entry"] = (down_cross & (slow_ma < trend_ma)).astype(int)
        df["long_exit"] = down_cross.astype(int)
        df["short_exit"] = up_cross.astype(int)

        return df
