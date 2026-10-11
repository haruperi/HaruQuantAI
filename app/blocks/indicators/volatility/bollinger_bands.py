"""Bollinger Bands (BB) indicator family.

Description:
    Computes Bollinger Bands (Upper, Middle, Lower, and BandWidth) according
    to StrategyQuant X specification. Consolidates calculations and price/band
    cross and touch conditions into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-BB: Bollinger Bands volatility envelopes and conditions.

Key Capabilities:
    - FR-BLOCKS-BB-CALCULATE: Compute Upper, Middle, Lower bands and BandWidth.
      Associated: `BollingerBands.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-BB-CONDITIONS: Evaluate price crossing and touching band envelopes.
      Associated: `BollingerBands.price_crosses_above_upper()`,
      `BollingerBands.price_crosses_below_lower()`
      Logging: DEBUG on evaluation of BB conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.bollinger_bands import BollingerBands

    close = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0])
    bb = BollingerBands.calculate(close, period=5, deviation=2.0)
    upper_val = bb["upper"].get(0)
    lower_val = bb["lower"].get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "bb" --no-cov
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


class BollingerBands(BaseIndicator):
    """Bollinger Bands family consolidating Upper/Middle/Lower bands and conditions."""

    name = "(BB) Bollinger Bands"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        data: np.ndarray | Sequence[float],
        period: int = 20,
        deviation: float = 2.0,
    ) -> dict[str, IndicatorSeries]:
        """Compute the Bollinger Bands lines.

        Args:
            data: Input price series.
            period: Lookback period for SMA and StdDev (default 20).
            deviation: Multiplier for standard deviation (default 2.0).

        Returns:
            Dictionary with 'upper', 'middle', 'lower', and 'bandwidth' series.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-BB-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20

        middle_arr = MovingAverage.sma(arr, period)
        upper_arr = np.full(n, np.nan, dtype=np.float64)
        lower_arr = np.full(n, np.nan, dtype=np.float64)
        bandwidth_arr = np.full(n, np.nan, dtype=np.float64)

        for i in range(period - 1, n):
            window = arr[i - period + 1 : i + 1]
            std = float(np.std(window, ddof=0))
            mid = middle_arr[i]
            upper_arr[i] = mid + deviation * std
            lower_arr[i] = mid - deviation * std
            if mid != 0.0:
                bandwidth_arr[i] = (upper_arr[i] - lower_arr[i]) / mid

        logger.info(
            "FR-BLOCKS-BB-CALCULATE: Computed BB(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )

        return {
            "upper": IndicatorSeries(upper_arr, name="BB.Upper"),
            "middle": IndicatorSeries(middle_arr, name="BB.Middle"),
            "lower": IndicatorSeries(lower_arr, name="BB.Lower"),
            "bandwidth": IndicatorSeries(bandwidth_arr, name="BB.BandWidth"),
        }

    # Unified condition helpers
    @classmethod
    def price_crosses_above_upper(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price crosses above Upper band condition."""
        return price_series.crosses_above(bands["upper"], shift)

    @classmethod
    def price_crosses_below_lower(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price crosses below Lower band condition."""
        return price_series.crosses_below(bands["lower"], shift)

    @classmethod
    def price_higher_upper(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price is higher than Upper band."""
        return price_series.is_greater(bands["upper"], shift)

    @classmethod
    def price_lower_lower(
        cls,
        price_series: IndicatorSeries,
        bands: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate Price is lower than Lower band."""
        return price_series.is_lower(bands["lower"], shift)
