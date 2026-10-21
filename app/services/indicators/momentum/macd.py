"""Moving Average Convergence Divergence (MACD) indicator family.

Description:
    Computes MACD (Main, Signal, and Histogram) and consolidates all line
    crossovers, zero-line crosses, threshold comparisons, direction changes, and
    signal slope conditions into a unified Python module.

Purpose:
    FEAT-SERVICES-INDICATOR-MACD: MACD momentum oscillator and conditions.

Key Capabilities:
    - FR-SERVICES-MACD-CALCULATE: Compute Main line, Signal line, and Histogram.
      Associated: `MACD.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-SERVICES-MACD-CONDITIONS: Evaluate signal, zero-line, and level conditions.
      Associated: `MACD.main_crosses_above_signal()`, `MACD.main_changes_up()`,
      `MACD.signal_is_rising()`
      Logging: DEBUG on evaluation of MACD conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.momentum.macd import MACD

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0, 12.2, 12.1])
    macd_dict = MACD.calculate(close, fast=12, slow=26, smooth=9)
    main = macd_dict["main"]
    signal = macd_dict["signal"]
    hist = macd_dict["histogram"]
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/indicators/test_indicator_gaps.py -k "macd"
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
        """Compute the MACD Main, Signal, and Histogram series."""
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
        """Evaluate MACDMainCrossAboveSignal."""
        return macd_dict["main"].crosses_above(macd_dict["signal"], shift)

    @classmethod
    def main_crosses_below_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainCrossBelowSignal."""
        return macd_dict["main"].crosses_below(macd_dict["signal"], shift)

    @classmethod
    def main_higher_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainHigherSignal."""
        return macd_dict["main"].is_greater(macd_dict["signal"], shift)

    @classmethod
    def main_lower_signal(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainLowerSignal."""
        return macd_dict["main"].is_lower(macd_dict["signal"], shift)

    @classmethod
    def main_crosses_above_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainCrossAboveZero."""
        return macd_dict["main"].crosses_above(0.0, shift)

    @classmethod
    def main_crosses_below_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainCrossBelowZero."""
        return macd_dict["main"].crosses_below(0.0, shift)

    @classmethod
    def main_changes_up(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainChangesUp (`Main[s+2] > Main[s+1] < Main[s]`)."""
        return macd_dict["main"].changes_up(shift)

    @classmethod
    def main_changes_down(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainChangesDown (`Main[s+2] < Main[s+1] > Main[s]`)."""
        return macd_dict["main"].changes_down(shift)

    @classmethod
    def main_crosses_above(
        cls, macd_dict: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate MACDMainCrossAbove level."""
        return macd_dict["main"].crosses_above(level, shift)

    @classmethod
    def main_crosses_below(
        cls, macd_dict: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate MACDMainCrossBelow level."""
        return macd_dict["main"].crosses_below(level, shift)

    @classmethod
    def main_is_rising(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainRising."""
        return macd_dict["main"].is_rising(shift)

    @classmethod
    def main_is_falling(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainFalling."""
        return macd_dict["main"].is_falling(shift)

    @classmethod
    def main_is_higher(
        cls, macd_dict: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate MACDMainHigher than level."""
        return macd_dict["main"].is_greater(level, shift)

    @classmethod
    def main_is_lower(
        cls, macd_dict: dict[str, IndicatorSeries], level: float, shift: int = 0
    ) -> bool:
        """Evaluate MACDMainLower than level."""
        return macd_dict["main"].is_lower(level, shift)

    @classmethod
    def main_higher_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainHigherZero (`Main[shift] > 0`)."""
        return macd_dict["main"].is_greater(0.0, shift)

    @classmethod
    def main_lower_zero(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDMainLowerZero (`Main[shift] < 0`)."""
        return macd_dict["main"].is_lower(0.0, shift)

    @classmethod
    def signal_is_rising(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDSignalRising."""
        return macd_dict["signal"].is_rising(shift)

    @classmethod
    def signal_is_falling(
        cls, macd_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate MACDSignalFalling."""
        return macd_dict["signal"].is_falling(shift)
