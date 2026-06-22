"""Engulfing Candle Pattern Indicator."""

from typing import Any
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator

class Engulfing(BaseIndicator):
    """Engulfing Pattern

    Description:
    Identifies bullish or bearish engulfing candlestick patterns.

    Sources:
    https://www.investopedia.com/terms/b/bullishengulfingpattern.asp
    https://www.investopedia.com/terms/b/bearishengulfingpattern.asp

    Calculation:
    Bullish Engulfing: Close_prev < Open_prev AND Close > Open AND Close >= Open_prev AND Open <= Close_prev
    Bearish Engulfing: Close_prev > Open_prev AND Close < Open AND Close <= Open_prev AND Open >= Close_prev

    Args:
    df (pd.DataFrame): DataFrame containing 'open' and 'close' columns.

    Returns:
    pd.DataFrame: Original DataFrame with 'candle_engulfing' column added (1 for bullish, -1 for bearish, 0 otherwise).
    """

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["open", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        
        result_df = df.copy()
        
        open_val = df["open"]
        close_val = df["close"]
        open_prev = df["open"].shift(1)
        close_prev = df["close"].shift(1)
        
        # Bullish Engulfing
        bullish = (close_prev < open_prev) & (close_val > open_val) & (close_val >= open_prev) & (open_val <= close_prev)
        
        # Bearish Engulfing
        bearish = (close_prev > open_prev) & (close_val < open_val) & (close_val <= open_prev) & (open_val >= close_prev)
        
        pattern = np.where(bullish, 1, np.where(bearish, -1, 0))
        pattern[0] = 0
        
        result_df["candle_engulfing"] = pattern
        return result_df
