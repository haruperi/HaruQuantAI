"""Directional Index (DI+ / DI- / DX) indicator family implementation.

Description:
    Computes J. Welles Wilder's Directional Movement Index system comprising
    Positive Directional Indicator (DI+), Negative Directional Indicator (DI-),
    and raw Directional Index (DX = 100 * |DI+ - DI-| / (DI+ + DI-)).
    Provides comprehensive condition helpers for DI crossovers, trend slopes,
    relative highs/lows, and turning points.

Purpose:
    FEAT-SERVICES-INDICATOR-DX: Directional Index calculation and condition blocks.

Key Capabilities:
    - FR-SERVICES-DX-CALCULATE: Vectorized calculation of DI+, DI-, and DX series.
      Associated: `DirectionalIndex.calculate()`
      Logging: INFO level logs on calculation completion.
    - FR-SERVICES-DX-CONDITIONS: Crossovers, slope, and turning point conditions.
      Associated: `DirectionalIndex.di_crosses_above()`,
                  `DirectionalIndex.di_plus_changes_up()`
      Logging: DEBUG level logs on condition evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.indicators.directional_index import DirectionalIndex

    high = np.linspace(10.0, 20.0, 30)
    low = np.linspace(8.0, 18.0, 30)
    close = np.linspace(9.0, 19.0, 30)

    res = DirectionalIndex.calculate(high, low, close, period=14)
    di_p = res["di_plus"].get(0)
    di_m = res["di_minus"].get(0)
    dx = res["dx"].get(0)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.indicators.directional_index
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.trend.adx import ADX

logger = get_logger(__name__)


class DirectionalIndex(BaseIndicator):
    """Directional Index indicator family."""

    name: str = "DirectionalIndex"
    category: str = "Trend"

    @classmethod
    @override
    def calculate(
        cls,
        high: Sequence[float] | np.ndarray,
        low: Sequence[float] | np.ndarray,
        close: Sequence[float] | np.ndarray,
        period: int = 14,
    ) -> dict[str, IndicatorSeries]:
        """Compute DI+, DI-, and raw DX series.

        Args:
            high: High prices array.
            low: Low prices array.
            close: Close prices array.
            period: Lookback smoothing period (default 14).

        Returns:
            Dictionary with 'di_plus', 'di_minus', and 'dx' IndicatorSeries.
        """
        adx_dict = ADX.calculate(high, low, close, period=period)
        di_plus = adx_dict["di_plus"]
        di_minus = adx_dict["di_minus"]

        p_vals = di_plus.values
        m_vals = di_minus.values
        denom = p_vals + m_vals

        dx_arr = np.full_like(p_vals, np.nan)
        valid = ~np.isnan(denom) & (denom > 0)
        dx_arr[valid] = 100.0 * np.abs(p_vals[valid] - m_vals[valid]) / denom[valid]

        logger.info(
            "FR-SERVICES-DX-CALCULATE: Computed DX(period=%d) for %d bars",
            period,
            len(p_vals),
        )
        return {
            "di_plus": di_plus,
            "di_minus": di_minus,
            "dx": IndicatorSeries(dx_arr, name=f"DX({period})"),
        }

    # DI Condition helpers
    @classmethod
    def di_crosses_above(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if DI+ crosses above DI-."""
        return di_dict["di_plus"].crosses_above(di_dict["di_minus"], shift)

    @classmethod
    def di_crosses_below(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if DI+ crosses below DI-."""
        return di_dict["di_plus"].crosses_below(di_dict["di_minus"], shift)

    @classmethod
    def di_plus_rising(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is rising."""
        return di_dict["di_plus"].is_rising(shift)

    @classmethod
    def di_plus_falling(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is falling."""
        return di_dict["di_plus"].is_falling(shift)

    @classmethod
    def di_plus_higher(
        cls, di_dict: dict[str, IndicatorSeries], lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is higher than lookback bars ago."""
        return di_dict["di_plus"].is_higher(lookback, shift)

    @classmethod
    def di_plus_lower(
        cls, di_dict: dict[str, IndicatorSeries], lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is lower than lookback bars ago."""
        val0 = di_dict["di_plus"].get(shift)
        val_past = di_dict["di_plus"].get(shift + lookback)
        if np.isnan(val0) or np.isnan(val_past):
            return False
        return val0 < val_past

    @classmethod
    def di_plus_changes_up(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ turned upward."""
        return di_dict["di_plus"].changes_up(shift)

    @classmethod
    def di_plus_changes_down(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ turned downward."""
        return di_dict["di_plus"].changes_down(shift)

    @classmethod
    def di_minus_rising(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- is rising."""
        return di_dict["di_minus"].is_rising(shift)

    @classmethod
    def di_minus_falling(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- is falling."""
        return di_dict["di_minus"].is_falling(shift)

    @classmethod
    def di_minus_changes_up(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- turned upward."""
        return di_dict["di_minus"].changes_up(shift)

    @classmethod
    def di_minus_changes_down(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- turned downward."""
        return di_dict["di_minus"].changes_down(shift)
