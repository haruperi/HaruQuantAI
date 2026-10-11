"""Laguerre RSI Indicator Block.

Description:
    Computes John Ehlers' 4-element Laguerre filter Relative Strength Index
    (Laguerre RSI). Utilizes a damping factor (gamma) to create a low-lag,
    smoothed oscillator bounded in [0.0, 1.0]. Provides condition evaluators
    for overbought/oversold levels, crosses, and momentum reversals.

Purpose:
    FEAT-BLOCKS-INDICATOR-LAGUERRERSI

Key Capabilities:
    - FR-BLOCKS-LAGUERRERSI-CALCULATE: Computes Laguerre RSI bounded in [0.0, 1.0].
    - FR-BLOCKS-LAGUERRERSI-CONDITIONS: Evaluates overbought/oversold levels and turns.

Python API Usage:
    ```python
    from app.blocks.indicators.laguerre_rsi import LaguerreRSI

    lrsi = LaguerreRSI.calculate(close, gamma=0.5)

    # Condition checks
    is_rising = LaguerreRSI.is_rising(lrsi, shift=0)
    cross_up = LaguerreRSI.crosses_above(lrsi, level=0.2, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

WARMUP_BARS: int = 20
DEFAULT_GAMMA: float = 0.5


class LaguerreRSI(BaseIndicator):
    """John Ehlers' 4-element Laguerre filter Relative Strength Index."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        gamma: float = DEFAULT_GAMMA,
    ) -> IndicatorSeries:
        """Compute Laguerre RSI across price series.

        Formulas:
            L0[i] = (1 - gamma) * price[i] + gamma * L0[i-1]
            L1[i] = -gamma * L0[i] + L0[i-1] + gamma * L1[i-1]
            L2[i] = -gamma * L1[i] + L1[i-1] + gamma * L2[i-1]
            L3[i] = -gamma * L2[i] + L2[i-1] + gamma * L3[i-1]
            CU = sum of max(0, L_k - L_{k+1}) for k in 0..2
            CD = sum of max(0, L_{k+1} - L_k) for k in 0..2
            LRSI = CU / (CU + CD) if CU + CD != 0 else 0.0

        Args:
            price: Input price series (typically Close).
            gamma: Damping factor between 0.0 and 1.0 (default 0.5).

        Returns:
            IndicatorSeries bounded in [0.0, 1.0].

        Raises:
            ValueError: If gamma is outside [0.0, 1.0] or series is empty.
        """
        logger.info(
            "LaguerreRSI calculation initiated with gamma=%.3f",
            gamma,
            extra={"gamma": gamma},
        )
        if not (0.0 <= gamma <= 1.0):
            raise ValueError(f"Gamma must be between 0.0 and 1.0, got {gamma}")

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")

        lrsi_vals = np.zeros(n, dtype=np.float64)
        if n <= WARMUP_BARS:
            return IndicatorSeries(lrsi_vals, name=f"LaguerreRSI({gamma:.2f})")

        l0 = np.zeros(n, dtype=np.float64)
        l1 = np.zeros(n, dtype=np.float64)
        l2 = np.zeros(n, dtype=np.float64)
        l3 = np.zeros(n, dtype=np.float64)

        for i in range(WARMUP_BARS, n):
            c_val = p_arr[i]
            prev_l0 = l0[i - 1]
            prev_l1 = l1[i - 1]
            prev_l2 = l2[i - 1]
            prev_l3 = l3[i - 1]

            curr_l0 = ((1.0 - gamma) * c_val) + (gamma * prev_l0)
            curr_l1 = (-gamma * curr_l0) + prev_l0 + (gamma * prev_l1)
            curr_l2 = (-gamma * curr_l1) + prev_l1 + (gamma * prev_l2)
            curr_l3 = (-gamma * curr_l2) + prev_l2 + (gamma * prev_l3)

            l0[i] = curr_l0
            l1[i] = curr_l1
            l2[i] = curr_l2
            l3[i] = curr_l3

            cu, cd = cls._calc_cu_cd(curr_l0, curr_l1, curr_l2, curr_l3)
            total = cu + cd
            lrsi_vals[i] = (cu / total) if total != 0.0 else 0.0

        logger.info(
            "LaguerreRSI calculation complete: bars=%d, gamma=%.3f",
            n,
            gamma,
            extra={"bars": n, "gamma": gamma},
        )
        return IndicatorSeries(lrsi_vals, name=f"LaguerreRSI({gamma:.2f})")

    @staticmethod
    def _calc_cu_cd(l0: float, l1: float, l2: float, l3: float) -> tuple[float, float]:
        """Compute cumulative up and down price changes across Laguerre filters."""
        cu = 0.0
        cd = 0.0

        if l0 >= l1:
            cu += l0 - l1
        else:
            cd += l1 - l0

        if l1 >= l2:
            cu += l1 - l2
        else:
            cd += l2 - l1

        if l2 >= l3:
            cu += l2 - l3
        else:
            cd += l3 - l2

        return cu, cd

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI is rising."""
        logger.info("Evaluating LaguerreRSI is_rising at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] > s[prev])

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI is falling."""
        logger.info("Evaluating LaguerreRSI is_falling at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[curr] < s[prev])

    @staticmethod
    def crosses_above(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 0.2,
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI crossed above a threshold level."""
        logger.info("Evaluating LaguerreRSI crosses_above at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[prev] <= level and s[curr] > level)

    @staticmethod
    def crosses_below(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 0.8,
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI crossed below a threshold level."""
        logger.info("Evaluating LaguerreRSI crosses_below at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        curr = len(s) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(s) or np.isnan(s[curr]) or np.isnan(s[prev]):
            return False
        return bool(s[prev] >= level and s[curr] < level)

    @staticmethod
    def changes_up(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI turned upward (v0 > v1 and v1 <= v2)."""
        logger.info("Evaluating LaguerreRSI changes_up at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        i0 = len(s) - 1 - shift
        i1 = i0 - 1
        i2 = i0 - 2
        if i2 < 0 or i0 >= len(s):
            return False
        if np.isnan(s[i0]) or np.isnan(s[i1]) or np.isnan(s[i2]):
            return False
        return bool(s[i0] > s[i1] and s[i1] <= s[i2])

    @staticmethod
    def changes_down(
        series: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI turned downward (v0 < v1 and v1 >= v2)."""
        logger.info("Evaluating LaguerreRSI changes_down at shift=%d", shift)
        s = BaseIndicator.to_numpy(series)
        i0 = len(s) - 1 - shift
        i1 = i0 - 1
        i2 = i0 - 2
        if i2 < 0 or i0 >= len(s):
            return False
        if np.isnan(s[i0]) or np.isnan(s[i1]) or np.isnan(s[i2]):
            return False
        return bool(s[i0] < s[i1] and s[i1] >= s[i2])
