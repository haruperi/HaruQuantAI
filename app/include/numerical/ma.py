"""High-performance moving average numerical kernels."""

from __future__ import annotations

from typing import Any

import numpy as np


def sma_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Simple Moving Average using cumulative sum over 1D series.

    Args:
        data: 1D numerical array of price/indicator values.
        period: Rolling window length (must be >= 1).

    Returns:
        1D float64 array with NaN warmup for indices < period - 1.
    """
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period:
        return out

    # Cumulative sum prefix approach for O(N) calculation
    cumsum = np.cumsum(np.insert(arr, 0, 0.0))
    out[period - 1 :] = (cumsum[period:] - cumsum[:-period]) / float(period)
    return out
