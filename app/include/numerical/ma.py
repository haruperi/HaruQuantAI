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
    cumsum = np.empty(n + 1, dtype=np.float64)
    cumsum[0] = 0.0
    np.cumsum(arr, out=cumsum[1:])
    window_means = out[period - 1 :]
    np.subtract(cumsum[period:], cumsum[:-period], out=window_means)
    window_means /= float(period)
    return out


def ema_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Exponential Moving Average (EMA).

    Args:
        data: 1D numerical array of price/indicator values.
        period: Smoothing lookback period (must be >= 1).

    Returns:
        1D float64 array with NaN warmup for indices < period - 1.
    """
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period:
        return out

    arr_l = arr.tolist()
    alpha = 2.0 / (period + 1.0)
    one_minus_alpha = 1.0 - alpha
    val = float(np.mean(arr[:period]))
    out[period - 1] = val
    for i in range(period, n):
        val = alpha * arr_l[i] + one_minus_alpha * val
        out[i] = val
    return out


def smma_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Smoothed Moving Average (SMMA / Wilder's MA).

    Args:
        data: 1D numerical array of price/indicator values.
        period: Smoothing lookback period (must be >= 1).

    Returns:
        1D float64 array with NaN warmup for indices < period - 1.
    """
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period:
        return out

    arr_l = arr.tolist()
    val = float(np.mean(arr[:period]))
    out[period - 1] = val
    f_p = float(period)
    p_minus_1 = float(period - 1)
    for i in range(period, n):
        val = (val * p_minus_1 + arr_l[i]) / f_p
        out[i] = val
    return out


def lwma_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Linear Weighted Moving Average (LWMA).

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

    weights = np.arange(1, period + 1, dtype=np.float64)
    denom = float(weights.sum())

    for i in range(period - 1, n):
        window = arr[i - period + 1 : i + 1]
        out[i] = np.dot(window, weights) / denom
    return out


def tema_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Triple Exponential Moving Average (TEMA: 3*EMA1 - 3*EMA2 + EMA3).

    Args:
        data: 1D numerical array of price/indicator values.
        period: Smoothing lookback period (must be >= 1).

    Returns:
        1D float64 array with NaN warmup.
    """
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n < period:
        return out

    ema1 = ema_kernel(arr, period)
    valid1 = np.where(~np.isnan(ema1))[0]
    if len(valid1) < period:
        return out
    ema2 = np.full(n, np.nan, dtype=np.float64)
    ema2[valid1[0] :] = ema_kernel(ema1[valid1[0] :], period)

    valid2 = np.where(~np.isnan(ema2))[0]
    if len(valid2) < period:
        return out
    ema3 = np.full(n, np.nan, dtype=np.float64)
    ema3[valid2[0] :] = ema_kernel(ema2[valid2[0] :], period)

    valid3 = ~np.isnan(ema3)
    out[valid3] = 3.0 * ema1[valid3] - 3.0 * ema2[valid3] + ema3[valid3]
    return out


__all__ = [
    "ema_kernel",
    "lwma_kernel",
    "sma_kernel",
    "smma_kernel",
    "tema_kernel",
]
