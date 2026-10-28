"""High-performance Relative Strength Index numerical kernel."""

from __future__ import annotations

from typing import Any

import numpy as np


def rsi_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Compute Relative Strength Index (RSI) using Wilder smoothing.

    Args:
        data: 1D numerical array of price values (e.g. Close).
        period: Smoothing lookback period (>= 1).

    Returns:
        1D float64 array with calculated RSI values in [0, 100], NaN for warmup.
    """
    c = np.asarray(data, dtype=np.float64)
    n = len(c)
    out = np.full(n, np.nan, dtype=np.float64)
    if period < 1 or n <= period:
        return out

    deltas = np.diff(c)
    ups = np.maximum(deltas, 0.0)
    downs = np.maximum(-deltas, 0.0)

    ups_l = ups.tolist()
    downs_l = downs.tolist()

    cur_avg_up = float(np.mean(ups[:period]))
    cur_avg_down = float(np.mean(downs[:period]))

    if cur_avg_down != 0.0:
        out[period] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
    elif cur_avg_up != 0.0:
        out[period] = 100.0
    else:
        out[period] = 50.0

    p_minus_1 = float(period - 1)
    f_p = float(period)
    for i in range(period + 1, n):
        up = ups_l[i - 1]
        down = downs_l[i - 1]
        cur_avg_up = (cur_avg_up * p_minus_1 + up) / f_p
        cur_avg_down = (cur_avg_down * p_minus_1 + down) / f_p

        if cur_avg_down != 0.0:
            out[i] = 100.0 - 100.0 / (1.0 + cur_avg_up / cur_avg_down)
        elif cur_avg_up != 0.0:
            out[i] = 100.0
        else:
            out[i] = 50.0

    return out


__all__ = ["rsi_kernel"]
