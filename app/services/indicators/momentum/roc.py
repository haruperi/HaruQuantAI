"""Rate of Change (ROC) indicator family implementation.

Description:
    Computes the Rate of Change percentage momentum oscillator measuring the
    percentage change between current price and price n-periods ago, centered
    at 0.0.
    Value = ((Price[t] - Price[t - Period]) / Price[t - Period]) * 100.0.
    Provides unified condition evaluation helpers for level crossovers,
    threshold comparisons, and trend direction.

Purpose:
    FEAT-SERVICES-INDICATOR-ROC: Rate of Change indicator calculation and conditions.

Key Capabilities:
    - FR-SERVICES-ROC-CALCULATE: Vectorized calculation of ROC percentage values.
      Associated: `ROC.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-ROC-CONDITIONS: Condition checks (rising, falling, crosses, levels).
      Associated: `ROC.is_rising()`, `ROC.crosses_above()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.roc import ROC

    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    roc = ROC.calculate(close, period=5)
    val = roc.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.roc
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class ROC(BaseIndicator):
    """Rate of Change (ROC) indicator family."""

    name: str = "ROC"
    category: str = "Oscillators"

    @classmethod
    @override
    def calculate(
        cls,
        data: Sequence[float] | np.ndarray,
        period: int = 5,
    ) -> IndicatorSeries:
        """Compute the Rate of Change series centered at 0.0.

        Args:
            data: Price series array (e.g. close).
            period: Lookback period (default 5).

        Returns:
            IndicatorSeries containing ROC values in percent.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-ROC-CALCULATE: Invalid period %d, defaulting to 5",
                period,
            )
            period = 5

        res = np.zeros(n, dtype=np.float64)
        for i in range(period, n):
            past = arr[i - period]
            if past != 0.0 and not np.isnan(past):
                res[i] = ((arr[i] - past) / past) * 100.0
            else:
                res[i] = 0.0

        logger.info(
            "FR-SERVICES-ROC-CALCULATE: Computed ROC(period=%d) for %d bars",
            period,
            n,
        )
        return IndicatorSeries(res, name=f"ROC({period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ROCRising condition."""
        return series.is_rising(shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate ROCFalling condition."""
        return series.is_falling(shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCCrossesAboveLevel condition."""
        return series.crosses_above(level, shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCCrossesBelowLevel condition."""
        return series.crosses_below(level, shift)

    @classmethod
    def is_greater(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCAboveLevel condition."""
        return series.is_greater(level, shift)

    @classmethod
    def is_lower(
        cls, series: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """Evaluate ROCBelowLevel condition."""
        return series.is_lower(level, shift)
