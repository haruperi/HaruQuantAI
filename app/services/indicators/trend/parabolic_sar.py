"""Parabolic SAR (PSAR) indicator family implementation.

Description:
    Computes J. Welles Wilder's Parabolic Stop and Reverse (SAR) trailing stop
    system designed to establish trailing stops for long or short positions:
    SAR[t] = SAR[t-1] + AF * (EP - SAR[t-1])
    where AF accelerates by Step (default 0.02) up to Maximum (default 0.2)
    each time a new extreme price (EP) is reached.
    Provides condition helpers for price/SAR relative positions and trend flips.

Purpose:
    FEAT-SERVICES-INDICATOR-PSAR: Parabolic SAR trailing stop calculation.

Key Capabilities:
    - FR-SERVICES-PSAR-CALCULATE: Vectorized stateful calculation of Parabolic SAR.
      Associated: `ParabolicSAR.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-PSAR-CONDITIONS: SAR position and price relation condition checks.
      Associated: `ParabolicSAR.is_bar_higher()`, `ParabolicSAR.is_bar_lower()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.parabolic_sar import ParabolicSAR

    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    psar = ParabolicSAR.calculate(high, low, step=0.02, maximum=0.2)
    val = psar.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.parabolic_sar
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class ParabolicSAR(BaseIndicator):
    """Parabolic SAR indicator family."""

    name: str = "ParabolicSAR"
    category: str = "Trend"

    MIN_LOOKBACK_BARS: int = 2

    @classmethod
    def _step_long(
        cls,
        prev_sar: float,
        af: float,
        ep: float,
        *,
        h_t: float,
        l_t: float,
        step: float,
        maximum: float,
        l_prev1: float,
        l_prev2: float,
    ) -> tuple[float, bool, float, float]:
        """Advance one bar in long state.

        Returns (new_sar, is_long, new_af, new_ep).
        """
        curr_sar = prev_sar + af * (ep - prev_sar)
        curr_sar = min(curr_sar, l_prev1, l_prev2)
        if l_t < curr_sar:
            return ep, False, step, l_t

        new_af = min(af + step, maximum) if h_t > ep else af
        new_ep = max(ep, h_t)
        return curr_sar, True, new_af, new_ep

    @classmethod
    def _step_short(
        cls,
        prev_sar: float,
        af: float,
        ep: float,
        *,
        h_t: float,
        l_t: float,
        step: float,
        maximum: float,
        h_prev1: float,
        h_prev2: float,
    ) -> tuple[float, bool, float, float]:
        """Advance one bar in short state.

        Returns (new_sar, is_long, new_af, new_ep).
        """
        curr_sar = prev_sar + af * (ep - prev_sar)
        curr_sar = max(curr_sar, h_prev1, h_prev2)
        if h_t > curr_sar:
            return ep, True, step, h_t

        new_af = min(af + step, maximum) if l_t < ep else af
        new_ep = min(ep, l_t)
        return curr_sar, False, new_af, new_ep

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        step: float = 0.02,
        maximum: float = 0.2,
    ) -> IndicatorSeries:
        """Compute Parabolic SAR series.

        Args:
            high: High prices array.
            low: Low prices array.
            step: Acceleration factor increment step (default 0.02).
            maximum: Maximum acceleration factor cap (default 0.2).

        Returns:
            IndicatorSeries containing Parabolic SAR price levels.
        """
        h_arr = np.asarray(high, dtype=np.float64)
        l_arr = np.asarray(low, dtype=np.float64)
        n = len(h_arr)

        if n != len(l_arr):
            raise ValueError("High and Low arrays must have equal length.")

        step = 0.02 if step <= 0 else step
        maximum = 0.2 if maximum <= 0 else maximum

        sar = np.zeros(n, dtype=np.float64)
        if n == 0:
            return IndicatorSeries(sar, name=f"PSAR({step},{maximum})")

        is_long = True
        af = step
        ep = h_arr[0]
        sar[0] = l_arr[0]

        for t in range(1, n):
            prev_sar = sar[t - 1]
            if is_long:
                l_p1 = l_arr[t - 1]
                l_p2 = l_arr[t - 2] if t >= cls.MIN_LOOKBACK_BARS else l_p1
                sar[t], is_long, af, ep = cls._step_long(
                    prev_sar,
                    af,
                    ep,
                    h_t=h_arr[t],
                    l_t=l_arr[t],
                    step=step,
                    maximum=maximum,
                    l_prev1=l_p1,
                    l_prev2=l_p2,
                )
            else:
                h_p1 = h_arr[t - 1]
                h_p2 = h_arr[t - 2] if t >= cls.MIN_LOOKBACK_BARS else h_p1
                sar[t], is_long, af, ep = cls._step_short(
                    prev_sar,
                    af,
                    ep,
                    h_t=h_arr[t],
                    l_t=l_arr[t],
                    step=step,
                    maximum=maximum,
                    h_prev1=h_p1,
                    h_prev2=h_p2,
                )

        logger.info(
            "FR-SERVICES-PSAR-CALCULATE: PSAR(step=%.3f, max=%.2f) for %d bars",
            step,
            maximum,
            n,
        )
        return IndicatorSeries(sar, name=f"PSAR({step},{maximum})")

    # Condition helpers
    @classmethod
    def is_bar_higher(
        cls,
        price: IndicatorSeries | Sequence[float] | np.ndarray,
        sar_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if price at shift is higher than SAR (uptrend position)."""
        p_series = (
            price
            if isinstance(price, IndicatorSeries)
            else IndicatorSeries(price, name="Price")
        )
        return p_series.is_greater(sar_series, shift)

    @classmethod
    def is_bar_lower(
        cls,
        price: IndicatorSeries | Sequence[float] | np.ndarray,
        sar_series: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Evaluate if price at shift is lower than SAR (downtrend position)."""
        p_series = (
            price
            if isinstance(price, IndicatorSeries)
            else IndicatorSeries(price, name="Price")
        )
        return p_series.is_lower(sar_series, shift)

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if PSAR is rising."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate if PSAR is falling."""
        return series.is_falling(shift)
