"""Average Daily Range (ADR) Indicator Block.

Description:
    Computes the Average Daily Range (ADR) measuring typical absolute price
    travel between high and low over a rolling lookback window. Also computes
    the ADR stretch ratio comparing current bar range against typical range to
    detect expansion breakouts and compression squeezes.

Purpose:
    FEAT-SERVICES-INDICATOR-ADR

Key Capabilities:
    - FR-SERVICES-ADR-CALCULATE: Computes rolling ADR and range stretch ratio.
      Associated: `AverageDailyRange.calculate()`
      Logging: INFO level logging of period and bar count.
    - FR-SERVICES-ADR-CONDITIONS: Evaluates stretch, compression, and trend states.
      Associated: `AverageDailyRange.is_stretched()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.volatility.adr import AverageDailyRange

    res = AverageDailyRange.calculate(high, low, period=14)
    adr = res["adr"]
    stretch = res["stretch"]
    is_expanding = AverageDailyRange.is_stretched(stretch, threshold=1.2, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

MIN_ADR_PERIOD: int = 1
DEFAULT_ADR_PERIOD: int = 14
DEFAULT_STRETCH_THRESHOLD: float = 1.2
DEFAULT_COMPRESS_THRESHOLD: float = 0.8
EPSILON: float = 1e-12


class AverageDailyRange(BaseIndicator):
    """Average Daily Range (ADR) price travel and stretch ratio block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_ADR_PERIOD,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling Average Daily Range and range stretch ratio.

        Args:
            high: High price series.
            low: Low price series.
            period: Lookback window (>= 1).

        Returns:
            Dictionary containing:
                - 'adr': Rolling average of bar range (high - low).
                - 'stretch': Current bar range divided by ADR.
        """
        logger.info("AverageDailyRange initiated: period=%d", period)
        if period < MIN_ADR_PERIOD:
            raise ValueError(f"period must be >= {MIN_ADR_PERIOD}, got {period}")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        n = len(h_arr)
        if n == 0 or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        adr_vals, stretch_vals = cls._compute_adr(h_arr, l_arr, period, n)
        logger.info("AverageDailyRange completed: bars=%d", n)
        return {
            "adr": IndicatorSeries(adr_vals, name=f"ADR({period})"),
            "stretch": IndicatorSeries(stretch_vals, name=f"ADR_Stretch({period})"),
        }

    @classmethod
    def _compute_adr(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        period: int,
        n: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        rng = np.maximum(0.0, h_arr - l_arr)
        adr = np.zeros(n, dtype=np.float64)
        stretch = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            mean_rng = float(np.sum(rng[start : i + 1])) / window_len
            adr[i] = mean_rng
            stretch[i] = rng[i] / mean_rng if mean_rng > EPSILON else 1.0

        return adr, stretch

    @classmethod
    def is_stretched(
        cls,
        stretch: IndicatorSeries,
        threshold: float = DEFAULT_STRETCH_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if bar range stretch exceeds threshold (volatility expansion)."""
        logger.info(
            "Evaluating ADR is_stretched: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        val = stretch.get(shift)
        return not np.isnan(val) and val > threshold

    @classmethod
    def is_compressed(
        cls,
        stretch: IndicatorSeries,
        threshold: float = DEFAULT_COMPRESS_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if bar range stretch is below threshold (volatility compression)."""
        logger.info(
            "Evaluating ADR is_compressed: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        val = stretch.get(shift)
        return not np.isnan(val) and val < threshold

    @classmethod
    def crosses_above(
        cls,
        adr: IndicatorSeries,
        level: float,
        shift: int = 0,
    ) -> bool:
        """True if ADR crosses above level at shift."""
        logger.info("Evaluating ADR crosses_above: level=%.4f, shift=%d", level, shift)
        curr = adr.get(shift)
        prev = adr.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev <= level and curr > level)

    @classmethod
    def crosses_below(
        cls,
        adr: IndicatorSeries,
        level: float,
        shift: int = 0,
    ) -> bool:
        """True if ADR crosses below level at shift."""
        logger.info("Evaluating ADR crosses_below: level=%.4f, shift=%d", level, shift)
        curr = adr.get(shift)
        prev = adr.get(shift + 1)
        if np.isnan(curr) or np.isnan(prev):
            return False
        return bool(prev >= level and curr < level)

    @classmethod
    def is_rising(cls, adr: IndicatorSeries, shift: int = 0) -> bool:
        """True if ADR is rising between shift+1 and shift."""
        logger.info("Evaluating ADR is_rising at shift=%d", shift)
        curr = adr.get(shift)
        prev = adr.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr > prev

    @classmethod
    def is_falling(cls, adr: IndicatorSeries, shift: int = 0) -> bool:
        """True if ADR is falling between shift+1 and shift."""
        logger.info("Evaluating ADR is_falling at shift=%d", shift)
        curr = adr.get(shift)
        prev = adr.get(shift + 1)
        return not np.isnan(curr) and not np.isnan(prev) and curr < prev
