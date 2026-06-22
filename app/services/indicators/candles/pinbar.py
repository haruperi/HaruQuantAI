"""Pinbar Candlestick Pattern Indicator."""

from typing import Any
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator

class Pinbar(BaseIndicator):
    """Pinbar Pattern

    Description:
    Identifies bullish or bearish pinbar candles characterized by a long shadow/wick on one side and a small body on the other.

    Sources:
    https://www.investopedia.com/terms/p/pinbar.asp

    Calculation:
    Range = High - Low
    Body = abs(Close - Open)
    Bullish Pinbar: Lower Shadow > 0.6 * Range AND Body < 0.3 * Range
    Bearish Pinbar: Upper Shadow > 0.6 * Range AND Body < 0.3 * Range

    Args:
    df (pd.DataFrame): DataFrame containing 'open', 'high', 'low', and 'close' columns.

    Returns:
    pd.DataFrame: Original DataFrame with 'candle_pinbar' column added (1 for bullish, -1 for bearish, 0 otherwise).
    """

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        
        result_df = df.copy()
        
        h_range = df["high"] - df["low"]
        body = (df["close"] - df["open"]).abs()
        
        lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]
        upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
        
        bullish = (lower_shadow > 0.6 * h_range) & (body < 0.3 * h_range) & (h_range > 0)
        bearish = (upper_shadow > 0.6 * h_range) & (body < 0.3 * h_range) & (h_range > 0)
        
        pattern = np.where(bullish, 1, np.where(bearish, -1, 0))
        
        result_df["candle_pinbar"] = pattern
        return result_df
