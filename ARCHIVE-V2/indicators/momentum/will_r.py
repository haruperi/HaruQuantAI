"""Williams %R Indicator."""

from typing import Any

import pandas as pd

from app.services.indicators.base import BaseIndicator


class WilliamsR(BaseIndicator):
    """Williams %R

    Description:
    A momentum indicator that measures overbought and oversold levels, oscillating between 0 and -100.

    Sources:
    https://www.investopedia.com/terms/w/williamsr.asp

    Calculation:
    %R = (Highest High - Close) / (Highest High - Lowest Low) * -100

    Args:
    df (pd.DataFrame): DataFrame containing 'high', 'low', and 'close' columns.
    period (int): Lookback period for highest high and lowest low. Default is 14.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'will_r_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 14, **kwargs: Any) -> pd.Series:
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        highest_high = df["high"].rolling(window=period).max()
        lowest_low = df["low"].rolling(window=period).min()

        denom = highest_high - lowest_low
        will_r = (highest_high - df["close"]) / denom.replace(0, 1e-10) * -100
        will_r.name = f"will_r_{period}"
        return will_r
