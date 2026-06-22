"""Price Volume Distribution (PVD) / Volume-by-Price Indicator."""

from typing import Any
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator

class PriceVolumeDistribution(BaseIndicator):
    """Price Volume Distribution (PVD)

    Description:
    Identifies major price levels of support and resistance based on volume concentration over a rolling period.
    Also known as Volume-by-Price or Volume Profile.

    Sources:
    https://www.investopedia.com/terms/v/volume-by-price.asp

    Calculation:
    For each candle, look at the last N candles (period). Divide the range between min(low) and max(high) into B bins.
    Sum the volume in each bin based on where the close price falls.
    Return the center price of the bin with the maximum volume as the Point of Control (POC).

    Args:
    df (pd.DataFrame): DataFrame containing 'high', 'low', 'close', and 'volume' columns.
    period (int): Lookback period. Default is 20.
    bins (int): Number of price levels/bins. Default is 10.

    Returns:
    pd.DataFrame: Original DataFrame with the new column 'pvd_poc_{period}' added.
    """

    def calculate(self, df: pd.DataFrame, period: int = 20, bins: int = 10, **kwargs: Any) -> pd.DataFrame:
        required_cols = ["high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
        if period < 1:
            raise ValueError("Period must be greater than or equal to 1.")
        if bins < 1:
            raise ValueError("Bins must be greater than or equal to 1.")
        
        result_df = df.copy()
        poc_series = []
        
        close_arr = df["close"].values
        high_arr = df["high"].values
        low_arr = df["low"].values
        volume_arr = df["volume"].values
        n = len(df)
        
        for i in range(n):
            if i < period - 1:
                poc_series.append(np.nan)
                continue
                
            start = i - period + 1
            end = i + 1
            
            w_high = high_arr[start:end]
            w_low = low_arr[start:end]
            w_close = close_arr[start:end]
            w_volume = volume_arr[start:end]
            
            min_p = w_low.min()
            max_p = w_high.max()
            
            if max_p == min_p:
                poc_series.append(max_p)
                continue
                
            bin_edges = np.linspace(min_p, max_p, bins + 1)
            bin_volumes = np.zeros(bins)
            
            for c_val, v_val in zip(w_close, w_volume):
                bin_idx = np.searchsorted(bin_edges, c_val) - 1
                bin_idx = max(0, min(bin_idx, bins - 1))
                bin_volumes[bin_idx] += v_val
                
            max_bin_idx = np.argmax(bin_volumes)
            poc_price = (bin_edges[max_bin_idx] + bin_edges[max_bin_idx + 1]) / 2
            poc_series.append(poc_price)
            
        result_df[f"pvd_poc_{period}"] = poc_series
        return result_df
