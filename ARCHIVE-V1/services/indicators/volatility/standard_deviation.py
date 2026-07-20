"""Standard Deviation Indicator."""

from typing import Any

import pandas as pd

from app.services.indicators.base import BaseIndicator


class StandardDeviation(BaseIndicator):
    """Standard Deviation

    Description:
    A statistical measure of market volatility showing how much prices deviate from the average.

    Sources:
    https://www.investopedia.com/terms/s/standarddeviation.asp

    Calculation:
    StdDev = sqrt( sum((Price - SMA)^2) / period )

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period. Default is 20.
    column (str): Target column to measure. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'std_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 20, column: str = "close", **kwargs: Any) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        result_df = df.copy()
        result_df[f"std_{period}"] = df[column].rolling(window=period).std()
        return result_df
