"""Relative Strength Index (RSI) Indicator."""

from typing import Any

import pandas as pd
from app.services.indicators.base import BaseIndicator


class RSI(BaseIndicator):
    """Relative Strength Index (RSI)

    Description:
    A momentum oscillator that measures the speed and change of price movements.

    Sources:
    https://www.investopedia.com/terms/r/rsi.asp

    Calculation:
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over the period

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period for calculating RSI. Default is 14.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'rsi_{period}' added.
    """

    def calculate(
        self, df: pd.DataFrame, period: int = 14, column: str = "close", **kwargs: Any
    ) -> pd.Series:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        delta = df[column].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Wilder's smoothing technique
        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi.name = f"rsi_{period}"
        return rsi
