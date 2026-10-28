"""High-performance Bollinger Bands numerical kernel."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.include.numerical.ma import sma_kernel


def bollinger_bands_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
    deviation: float = 2.0,
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
    """Compute Bollinger Bands (upper, middle, lower, bandwidth, range)."""
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)

    upper_arr = np.full(n, np.nan, dtype=np.float64)
    middle_arr = sma_kernel(arr, period)
    lower_arr = np.full(n, np.nan, dtype=np.float64)
    bandwidth_arr = np.full(n, np.nan, dtype=np.float64)
    range_arr = np.full(n, np.nan, dtype=np.float64)

    if period < 1 or n < period:
        return {
            "upper": upper_arr,
            "middle": middle_arr,
            "lower": lower_arr,
            "bandwidth": bandwidth_arr,
            "range": range_arr,
        }

    windows = np.lib.stride_tricks.sliding_window_view(arr, period)
    stds = np.std(windows, axis=-1, ddof=0)
    mids = middle_arr[period - 1 :]
    dev_std = deviation * stds

    upper_arr[period - 1 :] = mids + dev_std
    lower_arr[period - 1 :] = mids - dev_std
    range_arr[period - 1 :] = 2.0 * dev_std

    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(
            upper_arr[period - 1 :] - lower_arr[period - 1 :],
            mids,
            out=bandwidth_arr[period - 1 :],
            where=mids != 0.0,
        )

    return {
        "upper": upper_arr,
        "middle": middle_arr,
        "lower": lower_arr,
        "bandwidth": bandwidth_arr,
        "range": range_arr,
    }


__all__ = ["bollinger_bands_kernel"]
