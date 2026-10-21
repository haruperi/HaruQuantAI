"""Amihud Illiquidity Volatility Indicator Block.

Description:
    Computes Yakov Amihud's price impact illiquidity ratio measuring the
    price response associated with one dollar (or unit) of trading volume.
    High values signify illiquidity where small volume causes large price
    displacements, while low values signify deep, liquid order books.

Purpose:
    FEAT-SERVICES-INDICATOR-AMIHUD

Key Capabilities:
    - FR-SERVICES-AMIHUD-CALCULATE: Computes rolling Amihud illiquidity ratio.
      Associated: `AmihudIlliquidity.calculate()`
      Logging: INFO level logging of period, multiplier, and bar count.
    - FR-SERVICES-AMIHUD-CONDITIONS: Evaluates illiquid and liquid regime states.
      Associated: `AmihudIlliquidity.is_illiquid()`, etc.
      Logging: INFO level logging of evaluation parameters and result.

Python API Usage:
    ```python
    from app.services.indicators.volatility.amihud import AmihudIlliquidity

    amihud = AmihudIlliquidity.calculate(close, volume, period=20)
    is_thin = AmihudIlliquidity.is_illiquid(amihud, threshold=0.05, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

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

MIN_AMIHUD_PERIOD: int = 1
DEFAULT_AMIHUD_PERIOD: int = 20
DEFAULT_AMIHUD_MULTIPLIER: float = 1e6
EPSILON: float = 1e-12


class AmihudIlliquidity(BaseIndicator):
    """Amihud illiquidity price impact ratio indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any],
        period: int = DEFAULT_AMIHUD_PERIOD,
        multiplier: float = DEFAULT_AMIHUD_MULTIPLIER,
    ) -> IndicatorSeries:
        """Compute rolling Amihud illiquidity ratio.

        Args:
            close: Close price series.
            volume: Volume series.
            period: Lookback window (>= 1).
            multiplier: Scaling factor for readability (default: 1e6).

        Returns:
            IndicatorSeries with rolling Amihud illiquidity values.
        """
        logger.info(
            "AmihudIlliquidity initiated: period=%d, mult=%.1e",
            period,
            multiplier,
        )
        if period < MIN_AMIHUD_PERIOD:
            raise ValueError(f"period must be >= {MIN_AMIHUD_PERIOD}, got {period}")
        if multiplier <= 0.0:
            raise ValueError(f"multiplier must be > 0.0, got {multiplier}")

        c_arr = cls.to_numpy(close)
        v_arr = cls.to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")

        amihud_vals = cls._compute_amihud(c_arr, v_arr, period, multiplier, n)
        logger.info("AmihudIlliquidity completed: bars=%d", n)
        return IndicatorSeries(amihud_vals, name=f"Amihud({period})")

    @classmethod
    def _compute_amihud(
        cls,
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        period: int,
        multiplier: float,
        n: int,
    ) -> np.ndarray[Any, Any]:
        ret = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            prev_c = c_arr[i - 1]
            if prev_c > EPSILON:
                ret[i] = abs(c_arr[i] - prev_c) / prev_c

        dollar_vol = c_arr * v_arr
        raw_ratio = np.zeros(n, dtype=np.float64)
        valid_dv = dollar_vol > EPSILON
        raw_ratio[valid_dv] = (ret[valid_dv] / dollar_vol[valid_dv]) * multiplier

        amihud = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            amihud[i] = float(np.sum(raw_ratio[start : i + 1])) / window_len

        return amihud

    @classmethod
    def is_illiquid(
        cls,
        amihud: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if illiquidity ratio exceeds threshold (illiquid/thin market)."""
        logger.info(
            "Evaluating Amihud is_illiquid: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_greater(amihud, threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_liquid(
        cls,
        amihud: IndicatorSeries,
        threshold: float,
        shift: int = 0,
    ) -> bool:
        """True if illiquidity ratio is below threshold (liquid/deep market)."""
        logger.info(
            "Evaluating Amihud is_liquid: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_lower(amihud, threshold, shift1=shift, round_digits=8)

    @classmethod
    def crosses_above(
        cls,
        amihud: IndicatorSeries,
        level: float,
        shift: int = 0,
    ) -> bool:
        """True if Amihud ratio crosses above level at shift."""
        logger.info(
            "Evaluating Amihud crosses_above: level=%.4f, shift=%d",
            level,
            shift,
        )
        return crosses_above(amihud, level, shift=shift)

    @classmethod
    def crosses_below(
        cls,
        amihud: IndicatorSeries,
        level: float,
        shift: int = 0,
    ) -> bool:
        """True if Amihud ratio crosses below level at shift."""
        logger.info(
            "Evaluating Amihud crosses_below: level=%.4f, shift=%d",
            level,
            shift,
        )
        return crosses_below(amihud, level, shift=shift)

    @classmethod
    def is_rising(cls, amihud: IndicatorSeries, shift: int = 0) -> bool:
        """True if Amihud ratio is rising between shift+1 and shift."""
        logger.info("Evaluating Amihud is_rising at shift=%d", shift)
        return is_rising(amihud, shift=shift)

    @classmethod
    def is_falling(cls, amihud: IndicatorSeries, shift: int = 0) -> bool:
        """True if Amihud ratio is falling between shift+1 and shift."""
        logger.info("Evaluating Amihud is_falling at shift=%d", shift)
        return is_falling(amihud, shift=shift)
