"""Inside Bar Candlestick Pattern Indicator."""

from typing import Any
import pandas as pd
import numpy as np
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

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["high", "low"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        
        result_df = df.copy()
        
        high_prev = df["high"].shift(1)
        low_prev = df["low"].shift(1)
        
        is_inside = (df["high"] <= high_prev) & (df["low"] >= low_prev)
        pattern = np.where(is_inside, 1, 0)
        pattern[0] = 0
        
        result_df["candle_inside_bar"] = pattern
        return result_df
