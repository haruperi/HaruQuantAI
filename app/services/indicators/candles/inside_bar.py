"""Inside Bar Candlestick Pattern Indicator."""

from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.base import BaseIndicator


class InsideBar(BaseIndicator):
    """Inside Bar Pattern

    Description:
    Identifies inside bars, where the current candle's range is fully contained within the previous candle's range.

    Sources:
    https://www.investopedia.com/terms/i/insidebar.asp

    Calculation:
    Inside Bar = High <= High_prev AND Low >= Low_prev

    Args:
    df (pd.DataFrame): DataFrame containing 'high' and 'low' columns.

    Returns:
    pd.DataFrame: Original DataFrame with 'candle_inside_bar' column added (1 if inside bar, 0 otherwise).
    """

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.Series:
        required_cols = ["high", "low"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")

        high_prev = df["high"].shift(1)
        low_prev = df["low"].shift(1)

        is_inside = (df["high"] <= high_prev) & (df["low"] >= low_prev)
        pattern = np.where(is_inside, 1, 0)
        pattern[0] = 0

        inside_bar = pd.Series(pattern, index=df.index, name="candle_inside_bar")
        return inside_bar
