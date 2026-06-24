"""Simple Moving Average (SMA) Indicator."""

from typing import Any

import pandas as pd

from app.services.indicators.base import BaseIndicator


class SMA(BaseIndicator):
    """Simple Moving Average (SMA)

    Description:
    The average of the prices over a specified number of periods.

    Sources:
    https://www.investopedia.com/terms/s/sma.asp

    Calculation:
    SMA = (Price_1 + Price_2 + ... + Price_n) / n

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period for calculating SMA. Default is 10.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'sma_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 10, column: str = "close", **kwargs: Any) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        result_df = df.copy()
        result_df[f"sma_{period}"] = df[column].rolling(window=period).mean()
        return result_df
