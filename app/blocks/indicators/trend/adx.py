"""Average Directional Movement Index (ADX) indicator family.

Description:
    Computes ADX (Main ADX, +DI, and -DI) according to StrategyQuant X
    specification using Wilder's directional movement smoothing. Consolidates
    calculations and all directional trend strength and DI cross conditions
    into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-ADX: Average Directional Movement Index and conditions.

Key Capabilities:
    - FR-BLOCKS-ADX-CALCULATE: Compute +DI, -DI, DX, and smoothed ADX series.
      Associated: `ADX.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-ADX-CONDITIONS: Evaluate trend strength thresholds and DI crossovers.
      Associated: `ADX.di_plus_crosses_above_di_minus()`, `ADX.is_trending()`
      Logging: DEBUG on evaluation of ADX conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.adx import ADX

    high = np.array([12.0, 12.5, 12.8, 12.2, 13.0, 12.9, 13.2])
    low = np.array([11.2, 11.5, 12.0, 11.8, 12.1, 12.0, 12.5])
    close = np.array([11.8, 12.2, 12.1, 12.0, 12.8, 12.6, 13.0])

    adx_dict = ADX.calculate(high, low, close, period=14)
    adx_line = adx_dict["main"]
    di_plus = adx_dict["di_plus"]
    di_minus = adx_dict["di_minus"]
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "test_adx" --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.indicators.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.volatility.atr import ATR
from app.host.logging import get_logger

logger = get_logger(__name__)


class ADX(BaseIndicator):
    """ADX family consolidating Main ADX, +DI, -DI lines and conditions."""

    name = "(ADX) Average Directional Movement Index"
    category = "Indicators"

    @classmethod
    def _compute_directional_moves(
        cls, high_arr: np.ndarray, low_arr: np.ndarray, n: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute raw positive and negative directional movement."""
        dm_plus = np.zeros(n, dtype=np.float64)
        dm_minus = np.zeros(n, dtype=np.float64)

        for i in range(1, n):
            up_move = high_arr[i] - high_arr[i - 1]
            down_move = low_arr[i - 1] - low_arr[i]

            if up_move > down_move and up_move > 0:
                dm_plus[i] = up_move
            if down_move > up_move and down_move > 0:
                dm_minus[i] = down_move

        return dm_plus, dm_minus

    @classmethod
    def _smooth_adx(cls, dx_arr: np.ndarray, period: int, n: int) -> np.ndarray:
        """Compute Wilder smoothed ADX line from raw DX values."""
        main_arr = np.full(n, np.nan, dtype=np.float64)
        valid_dx_idx = np.where(~np.isnan(dx_arr))[0]
        if len(valid_dx_idx) >= period:
            start = valid_dx_idx[0] + period - 1
            main_arr[start] = float(np.mean(dx_arr[valid_dx_idx[0] : start + 1]))
            for i in range(start + 1, n):
                main_arr[i] = (main_arr[i - 1] * (period - 1) + dx_arr[i]) / period
        return main_arr

    @classmethod
    @override
    def calculate(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute the ADX Main, +DI, and -DI series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Smoothing period (default 14).

        Returns:
            Dictionary with 'main', 'di_plus', and 'di_minus' series (0 to 100).
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-ADX-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        main_arr = np.full(n, np.nan, dtype=np.float64)
        di_plus_arr = np.full(n, np.nan, dtype=np.float64)
        di_minus_arr = np.full(n, np.nan, dtype=np.float64)

        if n <= period:
            return {
                "main": IndicatorSeries(main_arr, name="ADX.Main"),
                "di_plus": IndicatorSeries(di_plus_arr, name="ADX.DIPlus"),
                "di_minus": IndicatorSeries(di_minus_arr, name="ADX.DIMinus"),
            }

        tr = ATR.true_range(high_arr, low_arr, close_arr)
        dm_plus, dm_minus = cls._compute_directional_moves(high_arr, low_arr, n)

        sum_tr = float(np.sum(tr[1 : period + 1]))
        sum_plus = float(np.sum(dm_plus[1 : period + 1]))
        sum_minus = float(np.sum(dm_minus[1 : period + 1]))

        dx_arr = np.full(n, np.nan, dtype=np.float64)

        for i in range(period, n):
            if i > period:
                sum_tr = sum_tr - (sum_tr / period) + tr[i]
                sum_plus = sum_plus - (sum_plus / period) + dm_plus[i]
                sum_minus = sum_minus - (sum_minus / period) + dm_minus[i]

            if sum_tr != 0.0:
                di_plus_arr[i] = (sum_plus / sum_tr) * 100.0
                di_minus_arr[i] = (sum_minus / sum_tr) * 100.0
                di_sum = di_plus_arr[i] + di_minus_arr[i]
                if di_sum != 0.0:
                    dx_arr[i] = (abs(di_plus_arr[i] - di_minus_arr[i]) / di_sum) * 100.0

        main_arr = cls._smooth_adx(dx_arr, period, n)

        logger.info(
            "FR-BLOCKS-ADX-CALCULATE: Computed ADX(%d) for %d bars",
            period,
            n,
        )

        return {
            "main": IndicatorSeries(main_arr, name="ADX.Main"),
            "di_plus": IndicatorSeries(di_plus_arr, name="ADX.DIPlus"),
            "di_minus": IndicatorSeries(di_minus_arr, name="ADX.DIMinus"),
        }

    # Unified condition helpers
    @classmethod
    def di_plus_crosses_above_di_minus(
        cls, adx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate +DI crosses above -DI."""
        return adx_dict["di_plus"].crosses_above(adx_dict["di_minus"], shift)

    @classmethod
    def di_plus_crosses_below_di_minus(
        cls, adx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate +DI crosses below -DI."""
        return adx_dict["di_plus"].crosses_below(adx_dict["di_minus"], shift)

    @classmethod
    def di_plus_higher_di_minus(
        cls, adx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate +DI is higher than -DI."""
        return adx_dict["di_plus"].is_greater(adx_dict["di_minus"], shift)

    @classmethod
    def di_plus_lower_di_minus(
        cls, adx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate +DI is lower than -DI."""
        return adx_dict["di_plus"].is_lower(adx_dict["di_minus"], shift)

    @classmethod
    def is_trending(
        cls,
        adx_dict: dict[str, IndicatorSeries],
        threshold: float = 25.0,
        shift: int = 0,
    ) -> bool:
        """Evaluate ADX Main is greater than trend threshold (e.g. 25.0)."""
        return adx_dict["main"].is_greater(threshold, shift)
