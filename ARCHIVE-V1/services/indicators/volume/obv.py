"""On-Balance Volume (OBV) Indicator."""

from typing import Any

import numpy as np
import pandas as pd
from app.services.indicators.base import BaseIndicator


class OBV(BaseIndicator):
    """On-Balance Volume (OBV)

    Description:
    A cumulative momentum indicator that uses volume flow to predict changes in stock price.

    Sources:
    https://www.investopedia.com/terms/o/onbalancevolume.asp

    Calculation:
    If close > close_prev: OBV = OBV_prev + volume
    If close < close_prev: OBV = OBV_prev - volume
    If close == close_prev: OBV = OBV_prev

    Args:
    df (pd.DataFrame): DataFrame containing 'close' and 'volume' columns.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'obv' added.
    """

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")

        result_df = df.copy()

        close_diff = df["close"].diff()
        volume_direction = np.where(
            close_diff > 0, df["volume"], np.where(close_diff < 0, -df["volume"], 0)
        )
        # Initialize first element to 0
        volume_direction[0] = 0

        result_df["obv"] = volume_direction.cumsum()
        return result_df
