"""Weighted Moving Average (WMA) Indicator."""

from typing import Any

import numpy as np
import pandas as pd
from app.services.indicators.base import BaseIndicator


class WMA(BaseIndicator):
    """Weighted Moving Average (WMA)

    Description:
    A moving average that assigns linearly decreasing weights to older data points.

    Sources:
    https://www.investopedia.com/terms/w/weightedmovingaverage.asp

    Calculation:
    WMA = (Price_n * w_n + Price_{n-1} * w_{n-1} + ...) / (sum of weights)
    where w_i = i

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period for WMA. Default is 10.
    column (str): Column name to run calculation on. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'wma_{period}' added.
    """

    def calculate(
        self, df: pd.DataFrame, period: int = 10, column: str = "close", **kwargs: Any
    ) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")

        result_df = df.copy()

        weights = np.arange(1, period + 1)
        sum_weights = weights.sum()

        def linear_wma(x: np.ndarray[Any, Any]) -> Any:
            return np.dot(x, weights) / sum_weights

        result_df[f"wma_{period}"] = (
            df[column].rolling(window=period).apply(linear_wma, raw=True)
        )
        return result_df
