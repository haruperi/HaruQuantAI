"""Exponential Moving Average (EMA) Indicator."""

from typing import Any
import pandas as pd
from app.services.indicators.base import BaseIndicator

class EMA(BaseIndicator):
    """Exponential Moving Average (EMA)

    Description:
    A weighted moving average that gives more weight to recent price data.

    Sources:
    https://www.investopedia.com/terms/e/ema.asp

    Calculation:
    EMA_today = (Close_today * multiplier) + (EMA_yesterday * (1 - multiplier))
    where multiplier = 2 / (period + 1)

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period for calculating EMA. Default is 10.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'ema_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 10, column: str = "close", **kwargs: Any) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")
        
        result_df = df.copy()
        result_df[f"ema_{period}"] = df[column].ewm(span=period, adjust=False).mean()
        return result_df
