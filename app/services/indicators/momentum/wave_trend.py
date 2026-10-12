"""WaveTrend Oscillator Indicator Block.

Description:
    Computes the WaveTrend oscillator (WT1 and WT2), an adaptation of the
    Commodity Channel Index smoothed with dual exponential moving averages.
    Detects cycle extremes, zero-line transitions, and signal line crossovers.

Purpose:
    FEAT-SERVICES-INDICATOR-WAVETREND

Key Capabilities:
    - FR-SERVICES-WAVETREND-CALCULATE: Computes WaveTrend WT1 (Main) and WT2 (Signal).
    - FR-SERVICES-WAVETREND-CONDITIONS: Evaluates signal/zero crosses, levels, slopes.

Python API Usage:
    ```python
    from app.services.indicators.wave_trend import WaveTrend

    wt = WaveTrend.calculate(high, low, close, channel_length=10, average_length=21)
    wt1 = wt["wt1"]
    wt2 = wt["wt2"]

    # Condition checks
    cross_up = WaveTrend.wt1_crosses_above_wt2(wt1, wt2, shift=0)
    is_rising = WaveTrend.wt1_is_rising(wt1, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_WT_PERIOD: int = 2
DEFAULT_CHANNEL_LENGTH: int = 10
DEFAULT_AVERAGE_LENGTH: int = 21
DEFAULT_SIGNAL_LENGTH: int = 4
CI_FACTOR: float = 0.015
EPSILON: float = 1e-12


class WaveTrend(BaseIndicator):
    """WaveTrend oscillator block generating Main (WT1) and Signal (WT2) lines."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        close: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        channel_length: int = DEFAULT_CHANNEL_LENGTH,
        average_length: int = DEFAULT_AVERAGE_LENGTH,
        signal_length: int = DEFAULT_SIGNAL_LENGTH,
    ) -> dict[str, IndicatorSeries]:
        """Compute WaveTrend WT1 and WT2 series.

        Args:
            high: High prices or input typical price series.
            low: Optional Low prices (if None, high is treated as typical price).
            close: Optional Close prices (if None, high is treated as typical price).
            channel_length: Smoothing period for ESA and absolute deviation.
            average_length: Smoothing period for Channel Index (Main line WT1).
            signal_length: Smoothing period for Signal line WT2 (default 4).

        Returns:
            Dictionary containing 'wt1' and 'wt2' IndicatorSeries.

        Raises:
            ValueError: If periods are < 2 or series lengths mismatch.
        """
        logger.info(
            "WaveTrend calculation initiated: ch=%d, avg=%d, sig=%d",
            channel_length,
            average_length,
            signal_length,
            extra={
                "channel_length": channel_length,
                "average_length": average_length,
                "signal_length": signal_length,
            },
        )
        if (
            channel_length < MIN_WT_PERIOD
            or average_length < MIN_WT_PERIOD
            or signal_length < 1
        ):
            raise ValueError("Lengths must satisfy channel>=2, avg>=2, signal>=1")

        ap = cls._compute_typical_price(high, low, close)
        n = len(ap)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        wt1_vals, wt2_vals = cls._compute_wt_lines(
            ap, channel_length, average_length, signal_length
        )

        logger.info(
            "WaveTrend calculation complete: bars=%d",
            n,
            extra={"bars": n},
        )
        return {
            "wt1": IndicatorSeries(wt1_vals, name=f"WT1({channel_length})"),
            "wt2": IndicatorSeries(wt2_vals, name=f"WT2({signal_length})"),
        }

    @classmethod
    def _compute_typical_price(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any] | None,
        close: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> np.ndarray[Any, Any]:
        """Derive typical price array (H+L+C)/3.0 or single price array."""
        h_arr = cls.to_numpy(high)
        if low is None or close is None:
            return h_arr

        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        if not (len(h_arr) == len(l_arr) == len(c_arr)):
            raise ValueError("High, Low, and Close array lengths must match")

        return np.asarray((h_arr + l_arr + c_arr) / 3.0, dtype=np.float64)

    @classmethod
    def _compute_wt_lines(
        cls,
        ap: np.ndarray[Any, Any],
        channel_len: int,
        avg_len: int,
        sig_len: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Compute recursive WaveTrend filter stages."""
        n = len(ap)
        wt1 = np.zeros(n, dtype=np.float64)
        wt2 = np.zeros(n, dtype=np.float64)

        esa_mult = 2.0 / (channel_len + 1.0)
        d_mult = 2.0 / (channel_len + 1.0)
        tci_mult = 2.0 / (avg_len + 1.0)
        wt2_mult = 2.0 / (sig_len + 1.0)

        esa = np.zeros(n, dtype=np.float64)
        d = np.zeros(n, dtype=np.float64)

        esa[0] = ap[0]
        d[0] = 0.0

        for i in range(1, n):
            curr_ap = ap[i]
            curr_esa = (esa_mult * curr_ap) + ((1.0 - esa_mult) * esa[i - 1])
            esa[i] = curr_esa

            diff = abs(curr_ap - curr_esa)
            curr_d = (d_mult * diff) + ((1.0 - d_mult) * d[i - 1])
            d[i] = curr_d

            denom = CI_FACTOR * curr_d
            if curr_d > EPSILON and denom > EPSILON:
                ci = (curr_ap - curr_esa) / denom
                curr_wt1 = (tci_mult * ci) + ((1.0 - tci_mult) * wt1[i - 1])
                curr_wt2 = (wt2_mult * curr_wt1) + ((1.0 - wt2_mult) * wt2[i - 1])
            else:
                curr_wt1 = wt1[i - 1]
                curr_wt2 = wt2[i - 1]

            wt1[i] = curr_wt1
            wt2[i] = curr_wt2

        return wt1, wt2

    @staticmethod
    def wt1_crosses_above_wt2(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        wt2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 crossed above WT2."""
        logger.info("Evaluating WaveTrend wt1_crosses_above_wt2 at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        w2 = BaseIndicator.to_numpy(wt2)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or curr >= len(w2):
            return False
        if np.isnan(w1[curr]) or np.isnan(w2[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[prev] <= w2[prev] and w1[curr] > w2[curr])

    @staticmethod
    def wt1_crosses_below_wt2(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        wt2: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 crossed below WT2."""
        logger.info("Evaluating WaveTrend wt1_crosses_below_wt2 at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        w2 = BaseIndicator.to_numpy(wt2)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or curr >= len(w2):
            return False
        if np.isnan(w1[curr]) or np.isnan(w2[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[prev] >= w2[prev] and w1[curr] < w2[curr])

    @staticmethod
    def wt1_crosses_above_zero(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 crossed above zero."""
        logger.info("Evaluating WaveTrend wt1_crosses_above_zero at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or np.isnan(w1[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[prev] <= 0.0 and w1[curr] > 0.0)

    @staticmethod
    def wt1_crosses_below_zero(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 crossed below zero."""
        logger.info("Evaluating WaveTrend wt1_crosses_below_zero at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or np.isnan(w1[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[prev] >= 0.0 and w1[curr] < 0.0)

    @staticmethod
    def wt1_is_rising(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 is rising."""
        logger.info("Evaluating WaveTrend wt1_is_rising at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or np.isnan(w1[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[curr] > w1[prev])

    @staticmethod
    def wt1_is_falling(
        wt1: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if WT1 is falling."""
        logger.info("Evaluating WaveTrend wt1_is_falling at shift=%d", shift)
        w1 = BaseIndicator.to_numpy(wt1)
        curr = len(w1) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(w1) or np.isnan(w1[curr]) or np.isnan(w1[prev]):
            return False
        return bool(w1[curr] < w1[prev])
