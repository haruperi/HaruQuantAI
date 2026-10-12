"""Moving Average Convergence Divergence (MACD) indicator family.

Description:
    Computes MACD (Main, Signal, and Histogram) according to StrategyQuant X
    specification. Consolidates calculations and all line crossovers, zero-line
    crosses, and histogram momentum conditions into a unified Python module.

Purpose:
    FEAT-SERVICES-INDICATOR-MACD: MACD momentum oscillator and conditions.

Key Capabilities:
    - FR-SERVICES-MACD-CALCULATE: Compute Main line, Signal line, and Histogram.
      Associated: `MACD.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-MACD-CONDITIONS: Evaluate signal line and zero-line crossovers.
      Associated: `MACD.main_crosses_above_signal()`, `MACD.main_crosses_below_signal()`
      Logging: DEBUG on evaluation of MACD conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.macd import MACD

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0, 12.2, 12.1])
    macd_dict = MACD.calculate(close, fast=12, slow=26, smooth=9)
    main = macd_dict["main"]
    signal = macd_dict["signal"]
    hist = macd_dict["histogram"]
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_indicators.py -k "test_macd" --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.trend.moving_average import MovingAverage

logger = get_logger(__name__)


class MACD(BaseIndicator):
    """MACD family consolidating Main/Signal/Histogram and crossover conditions."""

    name = "(MACD) MACD"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        data: np.ndarray | Sequence[float],
        fast: int = 12,
        slow: int = 26,
        smooth: int = 9,
    ) -> dict[str, IndicatorSeries]:
        """Compute the MACD Main, Signal, and Histogram series.

        Args:
            data: Input price series.
            fast: Fast EMA period (default 12).
            slow: Slow EMA period (default 26).
            smooth: Signal smoothing period (default 9).

        Returns:
            Dictionary with 'main', 'signal', and 'histogram' series.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        fast_ema = MovingAverage.ema(arr, fast)
        slow_ema = MovingAverage.ema(arr, slow)

        main_arr = np.full(n, np.nan, dtype=np.float64)
        valid_mask = ~np.isnan(fast_ema) & ~np.isnan(slow_ema)
        main_arr[valid_mask] = fast_ema[valid_mask] - slow_ema[valid_mask]

        signal_arr = np.full(n, np.nan, dtype=np.float64)
        valid_indices = np.where(valid_mask)[0]
        if len(valid_indices) >= smooth:
            first_idx = valid_indices[0]
            valid_main = main_arr[first_idx:]
            sig_part = MovingAverage.sma(valid_main, smooth)
            signal_arr[first_idx:] = sig_part

        hist_arr = np.full(n, np.nan, dtype=np.float64)
        hist_mask = ~np.isnan(main_arr) & ~np.isnan(signal_arr)
        hist_arr[hist_mask] = main_arr[hist_mask] - signal_arr[hist_mask]

        logger.info(
            "FR-SERVICES-MACD-CALCULATE: Computed MACD(%d,%d,%d) for %d bars",
            fast,
            slow,
            smooth,
            n,
        )

        return {
            "main": IndicatorSeries(main_arr, name="MACD.Main"),
            "signal": IndicatorSeries(signal_arr, name="MACD.Signal"),
            "histogram": IndicatorSeries(hist_arr, name="MACD.Histogram"),
        }

    # Unified condition helpers
    @classmethod
    def main_crosses_above_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main crosses above Signal line."""
        return macd_dict["main"].crosses_above(macd_dict["signal"], shift)

    @classmethod
    def main_crosses_below_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main crosses below Signal line."""
        return macd_dict["main"].crosses_below(macd_dict["signal"], shift)

    @classmethod
    def main_higher_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main is higher than Signal line."""
        return macd_dict["main"].is_greater(macd_dict["signal"], shift)

    @classmethod
    def main_lower_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main is lower than Signal line."""
        return macd_dict["main"].is_lower(macd_dict["signal"], shift)

    @classmethod
    def main_crosses_above_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main crosses above zero line."""
        return macd_dict["main"].crosses_above(0.0, shift)

    @classmethod
    def main_crosses_below_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACD Main crosses below zero line."""
        return macd_dict["main"].crosses_below(0.0, shift)
