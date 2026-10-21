"""Ulcer Index (UI) indicator family implementation.

Description:
    Computes Peter Martin's Ulcer Index measuring the depth and duration of price
    drawdowns or rallies over a lookback period.
    Mode 1 (Up / Downside Risk): Percentage retracement from rolling highest close.
    Mode 2 (Down / Upside Risk): Percentage rally from rolling lowest close.
    UI = sqrt( sum(drawdown_pct^2, Period) / Period ).
    Provides unified condition evaluation helpers for safe-level thresholds and trend.

Purpose:
    FEAT-SERVICES-INDICATOR-ULCER: Ulcer Index risk calculation and conditions.

Key Capabilities:
    - FR-SERVICES-ULCER-CALCULATE: Vectorized calculation of Ulcer Index values.
      Associated: `UlcerIndex.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-ULCER-CONDITIONS: Condition checks (rising, falling, thresholds).
      Associated: `UlcerIndex.is_rising()`, `UlcerIndex.is_lower()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.volatility.ulcer_index import UlcerIndex

    close = np.array([10.0, 10.5, 9.8, 9.5, 9.2, 9.0, 8.8, 8.5])
    ui = UlcerIndex.calculate(close, mode=1, period=5)
    val = ui.get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.volatility.ulcer_index
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np
from app.host.logging import get_logger
from app.services.include.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_greater,
    is_lower,
    is_rising,
)
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)


class UlcerIndex(BaseIndicator):
    """Ulcer Index indicator family."""

    name: str = "UlcerIndex"
    category: str = "Volatility"

    UP_UI = 1
    DOWN_UI = 2

    @classmethod
    @override
    def calculate(
        cls,
        data: Sequence[float] | np.ndarray,
        mode: int = 1,
        period: int = 24,
    ) -> IndicatorSeries:
        """Compute the Ulcer Index series.

        Args:
            data: Close price series.
            mode: 1 for UP UI (drawdown from high), 2 for Down UI (rally from low).
            period: Lookback period (default 24).

        Returns:
            IndicatorSeries containing Ulcer Index values.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        if period <= 0:
            logger.warning(
                "FR-SERVICES-ULCER-CALCULATE: Invalid period %d, defaulting to 24",
                period,
            )
            period = 24

        dd_buffer = np.zeros(n, dtype=np.float64)
        res = np.zeros(n, dtype=np.float64)

        for i in range(n):
            start = max(0, i - period + 1)
            win = arr[start : i + 1]

            if mode == cls.DOWN_UI:
                lc = float(np.min(win))
                if lc != 0.0 and not np.isnan(lc):
                    dd_buffer[i] = 100.0 * (arr[i] - lc) / lc
            else:
                hc = float(np.max(win))
                if hc != 0.0 and not np.isnan(hc):
                    dd_buffer[i] = 100.0 * (arr[i] - hc) / hc

            if i >= period:
                dd_win = dd_buffer[i - period + 1 : i + 1]
                sum_sq = float(np.sum(np.square(dd_win)))
                res[i] = float(np.sqrt(sum_sq / period))

        logger.info(
            "FR-SERVICES-ULCER-CALCULATE: UI(mode=%d, period=%d) computed for %d bars",
            mode,
            period,
            n,
        )
        return IndicatorSeries(res, name=f"UlcerIndex(mode={mode},{period})")

    # Unified condition helpers
    @classmethod
    def is_rising(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is rising condition."""
        return is_rising(series, shift=shift)

    @classmethod
    def is_falling(cls, series: IndicatorSeries, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is falling condition."""
        return is_falling(series, shift=shift)

    @classmethod
    def crosses_above(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index crosses above level."""
        return crosses_above(series, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, series: IndicatorSeries, level: float, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index crosses below level (below safe level)."""
        return crosses_below(series, level, shift=shift)

    @classmethod
    def is_lower(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is below safe level threshold."""
        return is_lower(series, level, shift=shift)

    @classmethod
    def is_greater(cls, series: IndicatorSeries, level: float, shift: int = 0) -> bool:
        """Evaluate Ulcer Index is above safe level threshold."""
        return is_greater(series, level, shift=shift)

    @classmethod
    def is_higher(
        cls, series: IndicatorSeries, lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate Ulcer Index is higher than past value."""
        return is_greater(series, series, shift1=shift, shift2=shift + lookback)
