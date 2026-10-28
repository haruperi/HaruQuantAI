"""High-performance MACD numerical kernel."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.include.numerical.ma import ema_kernel, sma_kernel


def macd_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    fast: int = 12,
    slow: int = 26,
    smooth: int = 9,
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
    """Compute MACD (main, signal, histogram)."""
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)

    main_arr = np.full(n, np.nan, dtype=np.float64)
    signal_arr = np.full(n, np.nan, dtype=np.float64)
    hist_arr = np.full(n, np.nan, dtype=np.float64)

    if fast < 1 or slow < 1 or smooth < 1 or n < max(fast, slow):
        return {
            "main": main_arr,
            "signal": signal_arr,
            "histogram": hist_arr,
        }

    fast_ema = ema_kernel(arr, fast)
    slow_ema = ema_kernel(arr, slow)

    valid_mask = ~np.isnan(fast_ema) & ~np.isnan(slow_ema)
    main_arr[valid_mask] = fast_ema[valid_mask] - slow_ema[valid_mask]

    valid_indices = np.where(valid_mask)[0]
    if len(valid_indices) >= smooth:
        first_idx = valid_indices[0]
        valid_main = main_arr[first_idx:]
        sig_part = sma_kernel(valid_main, smooth)
        signal_arr[first_idx:] = sig_part

    hist_mask = ~np.isnan(main_arr) & ~np.isnan(signal_arr)
    hist_arr[hist_mask] = main_arr[hist_mask] - signal_arr[hist_mask]

    return {
        "main": main_arr,
        "signal": signal_arr,
        "histogram": hist_arr,
    }


__all__ = ["macd_kernel"]
