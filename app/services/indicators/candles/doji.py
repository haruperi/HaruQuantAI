"""Doji Candlestick Pattern Indicator."""

from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.base import BaseIndicator


class Doji(BaseIndicator):
    """Doji Pattern

    Description:
    Identifies Doji candlesticks, representing market indecision where open and close are very close.

    Sources:
    https://www.investopedia.com/terms/d/doji.asp

    Calculation:
    Body = abs(Close - Open)
    Range = High - Low
    Doji = Body <= 0.1 * Range (with Range > 0)

    Args:
    df (pd.DataFrame): DataFrame containing 'open', 'high', 'low', and 'close' columns.
    threshold (float): Percentage threshold of the range to define body size. Default is 0.1.

    Returns:
    pd.DataFrame: Original DataFrame with 'candle_doji' column added (1 if Doji, 0 otherwise).
    """

    def calculate(
        self, df: pd.DataFrame, threshold: float = 0.1, **kwargs: Any
    ) -> pd.Series:
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if threshold <= 0:
            raise ValueError("Threshold must be positive.")

        h_range = df["high"] - df["low"]
        body = (df["close"] - df["open"]).abs()

        is_doji = (body <= threshold * h_range) & (h_range > 0)
        pattern = np.where(is_doji, 1, 0)

        doji = pd.Series(pattern, index=df.index, name="candle_doji")
        return doji
