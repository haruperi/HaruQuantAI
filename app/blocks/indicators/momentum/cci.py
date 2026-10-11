"""Commodity Channel Index (CCI) indicator family.

Description:
    Computes Commodity Channel Index (CCI) according to StrategyQuant X
    specification. Consolidates calculations and all level crossovers,
    overbought, oversold, and momentum conditions into a unified Python module.

Purpose:
    FEAT-BLOCKS-INDICATOR-CCI: Commodity Channel Index oscillator and conditions.

Key Capabilities:
    - FR-BLOCKS-CCI-CALCULATE: Compute Typical Price, Mean Deviation, and CCI series.
      Associated: `CCI.calculate()`
      Logging: INFO when calculation completes; WARNING on invalid inputs.
    - FR-BLOCKS-CCI-CONDITIONS: Evaluate overbought, oversold, and zero-line crosses.
      Associated: `CCI.crosses_above()`, `CCI.crosses_below()`
      Logging: DEBUG on evaluation of CCI conditions.

Python API Usage:
    ```python
    import numpy as np
    from app.blocks.indicators.cci import CCI

    high = np.array([12.0, 12.5, 12.8, 12.2, 13.0, 12.9, 13.2])
    low = np.array([11.2, 11.5, 12.0, 11.8, 12.1, 12.0, 12.5])
    close = np.array([11.8, 12.2, 12.1, 12.0, 12.8, 12.6, 13.0])

    cci_series = CCI.calculate(high, low, close, period=5)
    current_cci = cci_series.get(0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py -k "test_cci" --no-cov
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


class CCI(BaseIndicator):
    """Commodity Channel Index family consolidating calculation and conditions."""

    name = "(CCI) Commodity Channel Index"
    category = "Indicators"

    @classmethod
    @override
    def calculate(
        cls,
        high: np.ndarray | Sequence[float],
        low: np.ndarray | Sequence[float],
        close: np.ndarray | Sequence[float],
        period: int = 14,
    ) -> IndicatorSeries:
        """Compute the Commodity Channel Index (CCI) series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback smoothing period (default 14).

        Returns:
            IndicatorSeries containing the calculated CCI values.
        """
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)

        if period <= 0:
            logger.warning(
                "FR-BLOCKS-CCI-CALCULATE: Invalid period %d, defaulting to 14",
                period,
            )
            period = 14

        tp = (high_arr + low_arr + close_arr) / 3.0
        sma_tp = MovingAverage.sma(tp, period)
        cci_vals = np.full(n, np.nan, dtype=np.float64)

        for i in range(period - 1, n):
            window = tp[i - period + 1 : i + 1]
            mean_dev = float(np.mean(np.abs(window - sma_tp[i])))
            if mean_dev != 0.0:
                cci_vals[i] = (tp[i] - sma_tp[i]) / (0.015 * mean_dev)
            else:
                cci_vals[i] = 0.0

        logger.info(
            "FR-BLOCKS-CCI-CALCULATE: Computed CCI(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(cci_vals, name="CCI")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate CCIFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate CCICrossUp condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate CCICrossDown condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate CCIHigher condition."""
        return series.is_higher(lookback, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate CCILower condition."""
        val0 = series.get(shift)
        val_past = series.get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past
