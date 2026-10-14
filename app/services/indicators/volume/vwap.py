"""Volume Weighted Average Price (VWAP) Indicator Block.

Description:
    Calculates rolling Volume Weighted Average Price (VWAP) over a configurable
    lookback period using OHLC average or typical price. Provides condition
    evaluators for price vs. VWAP crossovers, slope (rising/falling), and
    multi-period fast/slow VWAP comparisons.

Purpose:
    FEAT-SERVICES-INDICATOR-VWAP

Key Capabilities:
    - FR-SERVICES-VWAP-CALCULATE: Computes rolling volume-weighted average price.
    - FR-SERVICES-VWAP-CONDITIONS: Evaluates close crosses, slope, and fast/slow bands.

Python API Usage:
    ```python
    from app.services.indicators.vwap import VWAP

    # Calculate 10-period rolling VWAP
    vwap_series = VWAP.calculate(
        high, low, close, volume, open_prices=open_p, period=10
    )

    # Condition checks
    is_above = VWAP.bar_closes_above(close_series, vwap_series, shift=0)
    is_rising = VWAP.is_rising(vwap_series, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

DEFAULT_PERIOD: int = 10


class VWAP(BaseIndicator):
    """Rolling Volume Weighted Average Price indicator with condition helpers."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        *,
        open_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        period: int = DEFAULT_PERIOD,
    ) -> IndicatorSeries:
        """Calculate rolling Volume Weighted Average Price over the specified period.

        Formula:
            Price = (Open + High + Low + Close) / 4 (if open) or (H + L + C) / 3
            VWAP = sum(Price * Volume, period) / sum(Volume, period)

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Trading volume series.
            open_prices: Optional open price series (for 4-price average).
            period: Lookback window (defaults to 10, min 1).

        Returns:
            IndicatorSeries containing the rolling VWAP line.
        """
        h_arr = cls._to_numpy(high)
        l_arr = cls._to_numpy(low)
        c_arr = cls._to_numpy(close)
        v_arr = cls._to_numpy(volume)
        n = len(c_arr)

        if period < 1:
            logger.warning(
                "FR-SERVICES-VWAP-CALCULATE: Invalid period %d, defaulting to %d",
                period,
                DEFAULT_PERIOD,
            )
            period = DEFAULT_PERIOD

        out = np.full(n, np.nan, dtype=np.float64)
        if n < period:
            logger.info(
                "FR-SERVICES-VWAP-CALCULATE: Insufficient bars (%d < %d)",
                n,
                period,
            )
            return IndicatorSeries(out, name=f"VWAP({period})")

        # Determine price representation: 4-price average if open provided, else typical
        if open_prices is not None:
            o_arr = cls._to_numpy(open_prices)
            price_arr = (o_arr + h_arr + l_arr + c_arr) / 4.0
        else:
            price_arr = (h_arr + l_arr + c_arr) / 3.0

        pv_arr = price_arr * v_arr

        # Vectorized rolling sum of PV and V
        cum_pv = np.cumsum(np.nan_to_num(pv_arr, nan=0.0))
        cum_vol = np.cumsum(np.nan_to_num(v_arr, nan=0.0))

        # First window
        sum_pv_init = cum_pv[period - 1]
        sum_vol_init = cum_vol[period - 1]
        out[period - 1] = (
            sum_pv_init / sum_vol_init if sum_vol_init > 0 else price_arr[period - 1]
        )

        # Subsequent windows
        window_pv = cum_pv[period:] - cum_pv[:-period]
        window_vol = cum_vol[period:] - cum_vol[:-period]

        valid_vol = window_vol > 0
        window_vwap = np.where(
            valid_vol,
            window_pv / np.where(valid_vol, window_vol, 1.0),
            price_arr[period:],
        )
        out[period:] = window_vwap

        logger.info(
            "FR-SERVICES-VWAP-CALCULATE: Computed VWAP(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(out, name=f"VWAP({period})")

    @classmethod
    def bar_closes_above(
        cls,
        close: IndicatorSeries,
        vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is above VWAP at specified shift."""
        return close.is_greater(vwap, shift=shift)

    @classmethod
    def bar_closes_below(
        cls,
        close: IndicatorSeries,
        vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if bar close is below VWAP at specified shift."""
        return close.is_lower(vwap, shift=shift)

    @classmethod
    def is_rising(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is rising at shift compared to shift+1."""
        return vwap.is_rising(shift=shift)

    @classmethod
    def is_falling(cls, vwap: IndicatorSeries, shift: int = 0) -> bool:
        """Check if VWAP is falling at shift compared to shift+1."""
        return vwap.is_falling(shift=shift)

    @classmethod
    def fast_above_slow(
        cls,
        fast_vwap: IndicatorSeries,
        slow_vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if fast VWAP is above slow VWAP at shift."""
        return fast_vwap.is_greater(slow_vwap, shift=shift)

    @classmethod
    def fast_below_slow(
        cls,
        fast_vwap: IndicatorSeries,
        slow_vwap: IndicatorSeries,
        shift: int = 0,
    ) -> bool:
        """Check if fast VWAP is below slow VWAP at shift."""
        return fast_vwap.is_lower(slow_vwap, shift=shift)

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
