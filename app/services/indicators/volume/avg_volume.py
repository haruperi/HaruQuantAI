"""Average Volume Indicator Block.

Description:
    Computes the Simple Moving Average of bar trading volume over a specified
    lookback period. Provides condition evaluation helpers for trend slope
    (rising/falling), crossover levels, and direct bar-volume directional checks.

Purpose:
    FEAT-SERVICES-INDICATOR-AVGVOLUME

Key Capabilities:
    - FR-SERVICES-AVGVOLUME-CALCULATE: Computes SMA of volume series over lookback.
    - FR-SERVICES-AVGVOLUME-CONDITIONS: Evaluates rising, falling, crosses, and
      volume slope.

Python API Usage:
    ```python
    from app.services.indicators.avg_volume import AvgVolume

    # Calculate 14-period Average Volume
    avg_vol = AvgVolume.calculate(volume_series, period=14)

    # Condition checks
    is_rising = AvgVolume.is_rising(avg_vol, shift=0)
    vol_spiking = AvgVolume.volume_above_average(volume_series, avg_vol, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_PERIOD: int = 14


class AvgVolume(BaseIndicator):
    """Average Volume indicator with trend and crossover condition evaluation."""

    @classmethod
    @override
    def calculate(
        cls,
        volume: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_PERIOD,
    ) -> IndicatorSeries:
        """Compute the Simple Moving Average of volume over the specified period.

        Args:
            volume: 1D array or IndicatorSeries containing trade volume.
            period: Lookback window size (defaults to 14, min 1).

        Returns:
            IndicatorSeries containing the rolling average volume values.
        """
        vol_arr = cls._to_numpy(volume)
        n = len(vol_arr)

        if period < 1:
            logger.warning(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Invalid period %d, defaulting to %d",
                period,
                DEFAULT_PERIOD,
            )
            period = DEFAULT_PERIOD

        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            logger.info(
                "FR-SERVICES-AVGVOLUME-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return IndicatorSeries(out, name=f"AvgVolume({period})")

        # Rolling SMA calculation via cumulative sum
        cumsum = np.cumsum(np.nan_to_num(vol_arr, nan=0.0))
        out[period - 1] = cumsum[period - 1] / period
        out[period:] = (cumsum[period:] - cumsum[:-period]) / period

        logger.info(
            "FR-SERVICES-AVGVOLUME-CALCULATE: AvgVolume(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(out, name=f"AvgVolume({period})")

    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if average volume is rising at shift compared to shift+1."""
        return series.is_rising(shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Check if average volume is falling at shift compared to shift+1."""
        return series.is_falling(shift=shift)

    @classmethod
    def crosses_above(
        cls,
        series1: IndicatorSeries,
        series2: IndicatorSeries | float,
        shift: int = 0,
    ) -> bool:
        """Check if series1 crosses above series2."""
        return series1.crosses_above(series2, shift=shift)

    @classmethod
    def crosses_below(
        cls,
        series1: IndicatorSeries,
        series2: IndicatorSeries | float,
        shift: int = 0,
    ) -> bool:
        """Check if series1 crosses below series2."""
        return series1.crosses_below(series2, shift=shift)

    @classmethod
    def is_higher(
        cls,
        series1: IndicatorSeries,
        series2: IndicatorSeries | float,
        shift: int = 0,
    ) -> bool:
        """Check if series1 is higher than series2."""
        return series1.is_greater(series2, shift=shift)

    @classmethod
    def is_lower(
        cls,
        series1: IndicatorSeries,
        series2: IndicatorSeries | float,
        shift: int = 0,
    ) -> bool:
        """Check if series1 is lower than series2."""
        return series1.is_lower(series2, shift=shift)

    @classmethod
    def volume_is_rising(cls, volume: IndicatorSeries, shift: int = 0) -> bool:
        """Check if raw bar volume is rising at shift compared to shift+1."""
        return volume.is_rising(shift=shift)

    @classmethod
    def volume_is_falling(cls, volume: IndicatorSeries, shift: int = 0) -> bool:
        """Check if raw bar volume is falling at shift compared to shift+1."""
        return volume.is_falling(shift=shift)

    @classmethod
    def volume_above_average(
        cls,
        volume: IndicatorSeries,
        avg_volume: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if raw bar volume is greater than average volume at shift."""
        return volume.is_greater(avg_volume, shift=shift)
