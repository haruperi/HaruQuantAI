"""MetaTrader Keltner Channel (MTKC) indicator family implementation.

Description:
    Computes the MetaTrader variation of Keltner Channel, which centers the
    channels around a Simple Moving Average of Close price rather than Typical
    Price:
    Middle = SMA(Close, Period).
    Offset = SMA(High - Low, Period) * Deviation.
    Upper = Middle + Offset.
    Lower = Middle - Offset.
    Provides condition helpers for band touches, breakouts, and band slope direction.

Purpose:
    FEAT-BLOCKS-INDICATOR-MTKELTNER: MetaTrader Keltner Channel implementation.

Key Capabilities:
    - FR-BLOCKS-MTKELTNER-CALCULATE: Calculate Upper, Middle, Lower bands.
      Associated: `MTKeltnerChannel.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-BLOCKS-MTKELTNER-CONDITIONS: Condition checks (crosses, above, below, slopes).
      Associated: `MTKeltnerChannel.bar_closes_above_upper()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.mt_keltner_channel import MTKeltnerChannel

    high = np.array([10.5, 11.0, 11.5, 12.0, 12.5])
    low = np.array([9.5, 10.0, 10.5, 11.0, 11.5])
    close = np.array([10.0, 10.5, 11.0, 11.5, 12.0])
    kc = MTKeltnerChannel.calculate(high, low, close, period=20, deviation=1.5)
    upper = kc["upper"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.blocks.indicators.mt_keltner_channel
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.blocks.indicators.trend.moving_average import MovingAverage
from app.host.logging import get_logger

logger = get_logger(__name__)


class MTKeltnerChannel(BaseIndicator):
    """MetaTrader Keltner Channel indicator family (Close-based middle band)."""

    name: str = "MTKeltnerChannel"
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
        """Compute Upper, Middle, and Lower MT Keltner Channel series.

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
                "FR-BLOCKS-MTKELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        bar_range = high_arr - low_arr

        middle = MovingAverage.sma(close_arr, period)
        offset = MovingAverage.sma(bar_range, period) * deviation

        upper = middle + offset
        lower = middle - offset

        logger.info(
            "FR-BLOCKS-MTKELTNER-CALCULATE: MTKC(p=%d, d=%.2f) computed for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="MTKC.Upper"),
            "middle": IndicatorSeries(middle, name="MTKC.Middle"),
            "lower": IndicatorSeries(lower, name="MTKC.Lower"),
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
