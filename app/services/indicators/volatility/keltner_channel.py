"""Keltner Channel (KC) indicator family implementation.

Description:
    Computes Chester Keltner's volatility channels based on Average True Range /
    bar range envelopes around a moving average of typical price.
    Middle = SMA(Typical Price, Period), where Typical = (High + Low + Close) / 3.
    Offset = SMA(High - Low, Period) * Deviation.
    Upper = Middle + Offset.
    Lower = Middle - Offset.
    Provides condition helpers for band touches, breakouts, and band slope direction.

Purpose:
    FEAT-SERVICES-INDICATOR-KELTNER: Keltner Channel calculation and conditions.

Key Capabilities:
    - FR-SERVICES-KELTNER-CALCULATE: Vectorized Upper, Middle, Lower band calculation.
      Associated: `KeltnerChannel.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-KELTNER-CONDITIONS: Condition checks (crosses, above, below, slopes).
      Associated: `KeltnerChannel.bar_closes_above_upper()`,
                  `KeltnerChannel.upper_is_rising()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.keltner_channel import KeltnerChannel

    high = np.array([10.5, 11.0, 11.5, 12.0, 12.5])
    low = np.array([9.5, 10.0, 10.5, 11.0, 11.5])
    close = np.array([10.0, 10.5, 11.0, 11.5, 12.0])
    kc = KeltnerChannel.calculate(high, low, close, period=20, deviation=1.5)
    upper = kc["upper"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.keltner_channel
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


class KeltnerChannel(BaseIndicator):
    """Keltner Channel indicator family."""

    name: str = "KeltnerChannel"
    category: str = "Bands"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 20,
        deviation: float = 1.5,
    ) -> dict[str, IndicatorSeries]:
        """Compute Upper, Middle, and Lower Keltner Channel series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback period for SMA (default 20).
            deviation: Multiplier for range offset (default 1.5).

        Returns:
            Dictionary with 'upper', 'middle', and 'lower' IndicatorSeries.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-KELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        typical = (high_arr + low_arr + close_arr) / 3.0
        bar_range = high_arr - low_arr

        middle = MovingAverage.sma(typical, period)
        offset = MovingAverage.sma(bar_range, period) * deviation

        upper = middle + offset
        lower = middle - offset

        logger.info(
            "FR-SERVICES-KELTNER-CALCULATE: KC(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="KC.Upper"),
            "middle": IndicatorSeries(middle, name="KC.Middle"),
            "lower": IndicatorSeries(lower, name="KC.Lower"),
        }

    # Unified condition helpers
    @classmethod
    def bar_closes_above_upper(
        cls,
        close_series: IndicatorSeries,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is higher than Upper band."""
        return close_series.is_greater(kc_dict["upper"], shift)

    @classmethod
    def bar_closes_below_upper(
        cls,
        close_series: IndicatorSeries,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is lower than Upper band."""
        return close_series.is_lower(kc_dict["upper"], shift)

    @classmethod
    def bar_closes_above_lower(
        cls,
        close_series: IndicatorSeries,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is higher than Lower band."""
        return close_series.is_greater(kc_dict["lower"], shift)

    @classmethod
    def bar_closes_below_lower(
        cls,
        close_series: IndicatorSeries,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate if Close bar at shift is lower than Lower band."""
        return close_series.is_lower(kc_dict["lower"], shift)

    @classmethod
    def upper_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is rising."""
        return kc_dict["upper"].is_rising(shift)

    @classmethod
    def upper_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is falling."""
        return kc_dict["upper"].is_falling(shift)

    @classmethod
    def lower_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is rising."""
        return kc_dict["lower"].is_rising(shift)

    @classmethod
    def lower_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is falling."""
        return kc_dict["lower"].is_falling(shift)
