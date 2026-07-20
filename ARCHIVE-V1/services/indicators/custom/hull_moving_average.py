"""Hull Moving Average (HMA) Indicator."""

from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators.base import BaseIndicator


class HullMovingAverage(BaseIndicator):
    """Hull Moving Average (HMA)

    Description:
    An extremely fast and smooth moving average created by Alan Hull that almost eliminates lag.

    Sources:
    https://alanhull.com/hull-moving-average

    Calculation:
    HMA = WMA(2 * WMA(period/2) - WMA(period), sqrt(period))

    Args:
    df (pd.DataFrame): DataFrame containing the target column.
    period (int): Lookback period. Default is 9.
    column (str): Target column to calculate HMA. Default is 'close'.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'hma_{period}' added.
    """

    def _wma(self, series: pd.Series, period: int) -> pd.Series:
        weights = np.arange(1, period + 1)
        sum_weights = weights.sum()
        return series.rolling(window=period).apply(lambda x: np.dot(x, weights) / sum_weights, raw=True)

    def calculate(self, df: pd.DataFrame, period: int = 9, column: str = "close", **kwargs: Any) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if period < 2:
            raise ValueError("Period must be greater than or equal to 2.")

        result_df = df.copy()

        half_period = int(period / 2)
        sqrt_period = int(np.sqrt(period))

        wma_half = self._wma(df[column], half_period)
        wma_full = self._wma(df[column], period)

        raw_hma = 2 * wma_half - wma_full
        hma = self._wma(raw_hma, sqrt_period)

        result_df[f"hma_{period}"] = hma
        return result_df
