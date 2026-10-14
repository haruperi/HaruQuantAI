"""Hurst Exponent Statistical Persistence Regime Block.

Description:
    Computes the Hurst Exponent (H) via Rescaled Range (R/S) analysis over
    rolling logarithmic price returns to classify market statistical memory.
    H > 0.55 indicates persistent trending dynamics.
    H < 0.45 indicates anti-persistent mean-reverting dynamics.
    0.45 <= H <= 0.55 is consistent with Geometric Brownian Motion.

Purpose:
    FEAT-SERVICES-INDICATOR-HURST

Key Capabilities:
    - FR-SERVICES-HURST-CALCULATE: Computes rolling Hurst exponent series.
    - FR-SERVICES-HURST-CONDITIONS: Evaluates persistence and random walk states.

Python API Usage:
    ```python
    from app.services.indicators.regime.hurst import HurstExponent

    res = HurstExponent.calculate(close, window=100)
    hurst = res["hurst"]
    regime = res["regime"]

    trending = HurstExponent.is_persistent(hurst, shift=0)
    mean_reverting = HurstExponent.is_anti_persistent(hurst, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

import math
from typing import Any, override

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries

logger = get_logger(__name__)

HURST_REGIME_RANDOM: float = 0.0
HURST_REGIME_PERSISTENT: float = 1.0
HURST_REGIME_ANTI_PERSISTENT: float = 2.0

MIN_WINDOW: int = 20
MIN_SCALE_VALUE: int = 2
MIN_REGRESSION_POINTS: int = 2
RANDOM_WALK_HURST: float = 0.5

DEFAULT_WINDOW: int = 100
DEFAULT_MIN_SCALE: int = 8
DEFAULT_MAX_SCALE: int = 50
DEFAULT_SCALE_COUNT: int = 5
DEFAULT_LOWER_THRESHOLD: float = 0.45
DEFAULT_UPPER_THRESHOLD: float = 0.55
EPSILON: float = 1e-12


class HurstExponent(BaseIndicator):
    """Hurst Exponent statistical persistence regime indicator."""

    @classmethod
    @override
    def calculate(
        cls,
        price: IndicatorSeries | np.ndarray[Any, Any],
        window: int = DEFAULT_WINDOW,
        min_scale: int = DEFAULT_MIN_SCALE,
        max_scale: int = DEFAULT_MAX_SCALE,
        scale_count: int = DEFAULT_SCALE_COUNT,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
    ) -> dict[str, IndicatorSeries]:
        """Compute rolling Hurst Exponent and persistence regime state.

        Args:
            price: Input price series.
            window: Rolling return window length (>= 20).
            min_scale: Minimum sub-period partition scale.
            max_scale: Maximum sub-period partition scale.
            scale_count: Number of evaluation scales.
            lower_threshold: Anti-persistent boundary.
            upper_threshold: Persistent boundary.

        Returns:
            Dictionary with 'hurst' and 'regime' IndicatorSeries.
        """
        logger.info(
            "HurstExponent initiated: window=%d, min=%d, max=%d",
            window,
            min_scale,
            max_scale,
        )
        cls._validate_params(
            window, min_scale, max_scale, lower_threshold, upper_threshold
        )

        p_arr = cls.to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input price series cannot be empty")

        scales = cls._generate_scales(min_scale, max_scale, scale_count)
        h_vals, reg_vals = cls._compute_rolling_hurst(
            p_arr,
            window=window,
            scales=scales,
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
        )

        return {
            "hurst": IndicatorSeries(h_vals, name=f"Hurst({window})"),
            "regime": IndicatorSeries(reg_vals, name=f"Hurst_Regime({window})"),
        }

    @staticmethod
    def _validate_params(
        window: int,
        min_scale: int,
        max_scale: int,
        lower_threshold: float,
        upper_threshold: float,
    ) -> None:
        if window < MIN_WINDOW:
            raise ValueError(f"window must be >= {MIN_WINDOW}, got {window}")
        if min_scale < MIN_SCALE_VALUE or min_scale >= max_scale:
            raise ValueError(
                f"Invalid scale range: min_scale={min_scale}, max_scale={max_scale}"
            )
        if lower_threshold >= upper_threshold:
            raise ValueError(
                "lower_threshold must be strictly less than upper_threshold"
            )

    @staticmethod
    def _generate_scales(min_scale: int, max_scale: int, count: int) -> tuple[int, ...]:
        step = (max_scale - min_scale) / max(1, count - 1)
        scale_set = {
            round(min_scale + (i * step))
            for i in range(count)
            if round(min_scale + (i * step)) >= MIN_SCALE_VALUE
        }
        return tuple(sorted(scale_set))

    @classmethod
    def _compute_rolling_hurst(
        cls,
        p_arr: np.ndarray[Any, Any],
        *,
        window: int,
        scales: tuple[int, ...],
        lower_threshold: float,
        upper_threshold: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(p_arr)
        h_vals = np.full(n, RANDOM_WALK_HURST, dtype=np.float64)
        reg_vals = np.full(n, HURST_REGIME_RANDOM, dtype=np.float64)
        if n <= window:
            return h_vals, reg_vals

        # Log returns
        returns = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            prev = p_arr[i - 1]
            returns[i] = math.log(p_arr[i] / prev) if prev > 0.0 else 0.0

        for i in range(window, n):
            sample = returns[i - window + 1 : i + 1]
            h = cls._rs_slope(sample, scales)
            h_vals[i] = h
            reg_vals[i] = cls._classify_regime(h, lower_threshold, upper_threshold)

        return h_vals, reg_vals

    @staticmethod
    def _rs_slope(sample: np.ndarray[Any, Any], scales: tuple[int, ...]) -> float:
        """Estimate Hurst exponent by log-log regression of R/S against scales."""
        log_n: list[float] = []
        log_rs: list[float] = []

        for scale in scales:
            num_blocks = len(sample) // scale
            if num_blocks < 1:
                continue

            ratios: list[float] = []
            for b in range(num_blocks):
                block = sample[b * scale : (b + 1) * scale]
                mean_b = float(np.mean(block))
                devs = np.cumsum(block - mean_b)
                r_val = float(np.max(devs) - np.min(devs))
                s_val = float(np.std(block))

                if s_val > EPSILON:
                    ratios.append(r_val / s_val)

            if ratios:
                mean_rs = float(np.mean(ratios))
                if mean_rs > 0.0:
                    log_n.append(math.log(scale))
                    log_rs.append(math.log(mean_rs))

        if len(log_n) < MIN_REGRESSION_POINTS:
            return RANDOM_WALK_HURST

        mean_x = float(np.mean(log_n))
        mean_y = float(np.mean(log_rs))
        ss_xx = float(np.sum((np.array(log_n) - mean_x) ** 2))
        ss_xy = float(np.sum((np.array(log_n) - mean_x) * (np.array(log_rs) - mean_y)))
        if ss_xx > EPSILON:
            return max(0.0, min(1.0, ss_xy / ss_xx))
        return RANDOM_WALK_HURST

    @staticmethod
    def _classify_regime(h: float, lower: float, upper: float) -> float:
        if h > upper:
            return HURST_REGIME_PERSISTENT
        if h < lower:
            return HURST_REGIME_ANTI_PERSISTENT
        return HURST_REGIME_RANDOM

    @classmethod
    def is_persistent(
        cls,
        hurst: IndicatorSeries,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if series shows persistent trending memory."""
        logger.info("Evaluating Hurst is_persistent at shift=%d", shift)
        val = hurst.get(shift)
        return not np.isnan(val) and val > upper_threshold

    @classmethod
    def is_anti_persistent(
        cls,
        hurst: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if series shows anti-persistent mean-reverting memory."""
        logger.info("Evaluating Hurst is_anti_persistent at shift=%d", shift)
        val = hurst.get(shift)
        return not np.isnan(val) and val < lower_threshold

    @classmethod
    def is_random_walk(
        cls,
        hurst: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        upper_threshold: float = DEFAULT_UPPER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if series is consistent with a random walk."""
        logger.info("Evaluating Hurst is_random_walk at shift=%d", shift)
        val = hurst.get(shift)
        return not np.isnan(val) and (lower_threshold <= val <= upper_threshold)
