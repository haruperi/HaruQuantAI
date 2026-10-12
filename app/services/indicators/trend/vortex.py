"""Vortex Indicator (VI+ / VI-) indicator family implementation.

Description:
    Computes Etienne Botes and Douglas Siepman's Vortex Indicator identifying
    the start of a trend and confirming trend direction:
    VM+ = |High[t] - Low[t-1]|
    VM- = |Low[t] - High[t-1]|
    VI+[t] = sum(VM+, Period) / sum(TrueRange, Period)
    VI-[t] = sum(VM-, Period) / sum(TrueRange, Period)
    Vortex Oscillator = VI+ - VI-.
    Provides condition helpers for uptrends, downtrends, and trend crossovers.

Purpose:
    FEAT-SERVICES-INDICATOR-VORTEX: Vortex trend direction and crossover detection.

Key Capabilities:
    - FR-SERVICES-VORTEX-CALCULATE: Vectorized calculation of VI+, VI-, and Oscillator.
      Associated: `Vortex.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-VORTEX-CONDITIONS: Trend state and crossover condition checks.
      Associated: `Vortex.is_uptrend()`, `Vortex.changes_trend_up()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.vortex import Vortex

    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    close = np.linspace(9.0, 29.0, 40)

    vx = Vortex.calculate(high, low, close, period=14)
    vi_p = vx["vi_plus"].get(0)
    vi_m = vx["vi_minus"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.vortex
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.volatility.atr import ATR

logger = get_logger(__name__)


class Vortex(BaseIndicator):
    """Vortex indicator family."""

    name: str = "Vortex"
    category: str = "Trend"

    MIN_BARS: int = 2

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute VI+, VI-, and Vortex Oscillator series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback window period (default 14).

        Returns:
            Dictionary with 'vi_plus', 'vi_minus', and 'oscillator' IndicatorSeries.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if n != len(high_arr) or n != len(low_arr):
            raise ValueError("High, low, and close arrays must have equal length.")

        if period <= 0:
            logger.warning(
                "FR-SERVICES-VORTEX-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        vi_plus = np.zeros(n, dtype=np.float64)
        vi_minus = np.zeros(n, dtype=np.float64)

        if n <= period or n < cls.MIN_BARS:
            return {
                "vi_plus": IndicatorSeries(vi_plus, name=f"VI+({period})"),
                "vi_minus": IndicatorSeries(vi_minus, name=f"VI-({period})"),
                "oscillator": IndicatorSeries(
                    vi_plus - vi_minus, name=f"VortexOsc({period})"
                ),
            }

        tr = ATR.true_range(high_arr, low_arr, close_arr)

        vm_plus = np.zeros(n, dtype=np.float64)
        vm_minus = np.zeros(n, dtype=np.float64)

        vm_plus[1:] = np.abs(high_arr[1:] - low_arr[:-1])
        vm_minus[1:] = np.abs(low_arr[1:] - high_arr[:-1])

        # Rolling sums over period
        for t in range(period, n):
            sum_tr = float(np.sum(tr[t - period + 1 : t + 1]))
            sum_vmp = float(np.sum(vm_plus[t - period + 1 : t + 1]))
            sum_vmm = float(np.sum(vm_minus[t - period + 1 : t + 1]))

            if sum_tr > 0:
                vi_plus[t] = sum_vmp / sum_tr
                vi_minus[t] = sum_vmm / sum_tr
            else:
                vi_plus[t] = 0.0
                vi_minus[t] = 0.0

        oscillator = vi_plus - vi_minus

        logger.info(
            "FR-SERVICES-VORTEX-CALCULATE: Computed Vortex(period=%d) for %d bars",
            period,
            n,
        )
        return {
            "vi_plus": IndicatorSeries(vi_plus, name=f"VI+({period})"),
            "vi_minus": IndicatorSeries(vi_minus, name=f"VI-({period})"),
            "oscillator": IndicatorSeries(oscillator, name=f"VortexOsc({period})"),
        }

    # Condition helpers
    @classmethod
    def is_uptrend(cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if Vortex is in uptrend (VI+ > VI-)."""
        return vx_dict["vi_plus"].is_greater(vx_dict["vi_minus"], shift)

    @classmethod
    def is_downtrend(cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0) -> bool:
        """Evaluate if Vortex is in downtrend (VI+ < VI-)."""
        return vx_dict["vi_plus"].is_lower(vx_dict["vi_minus"], shift)

    @classmethod
    def changes_trend_up(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ crosses above VI- (bullish reversal)."""
        return vx_dict["vi_plus"].crosses_above(vx_dict["vi_minus"], shift)

    @classmethod
    def changes_trend_down(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ crosses below VI- (bearish reversal)."""
        return vx_dict["vi_plus"].crosses_below(vx_dict["vi_minus"], shift)

    @classmethod
    def vi_plus_rising(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ is rising."""
        return vx_dict["vi_plus"].is_rising(shift)

    @classmethod
    def vi_plus_falling(
        cls, vx_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if VI+ is falling."""
        return vx_dict["vi_plus"].is_falling(shift)
