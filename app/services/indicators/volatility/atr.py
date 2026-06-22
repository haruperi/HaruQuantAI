"""Average True Range (ATR) Indicator."""

from typing import Any
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator

class ATR(BaseIndicator):
    """Average True Range (ATR)

    Description:
    A measure of volatility introduced by J. Welles Wilder Jr.

    Sources:
    https://www.investopedia.com/terms/a/atr.asp

    Calculation:
    TR = max(High - Low, abs(High - Close_prev), abs(Low - Close_prev))
    ATR = Wilder's Smoothing of TR over the specified period

    Args:
    df (pd.DataFrame): DataFrame containing 'high', 'low', and 'close' columns.
    period (int): Lookback period. Default is 14.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'atr_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")
        
        result_df = df.copy()
        
        high_low = df["high"] - df["low"]
        high_prev_close = (df["high"] - df["close"].shift(1)).abs()
        low_prev_close = (df["low"] - df["close"].shift(1)).abs()
        
        tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        atr.iloc[:period-1] = np.nan
        
        result_df[f"atr_{period}"] = atr
        return result_df
