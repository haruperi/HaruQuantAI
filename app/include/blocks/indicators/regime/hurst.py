"""HurstExponent indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-HURSTEXPONENT: validated batch calculation.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.include.blocks.comparisons import (
    is_greater_or_equal,
    is_lower,
    is_lower_or_equal,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

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

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.hurst",
        name="HurstExponent",
        category="regime",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(
            OutputPort("hurst", PortType.SERIES),
            OutputPort("regime", PortType.SERIES),
        ),
        required_market_inputs=("close",),
        parameter_search_space={
            "window": {"type": "int", "min": 20, "max": 400, "default": 100},
            "min_scale": {"type": "int", "min": 2, "max": 32, "default": 8},
            "max_scale": {"type": "int", "min": 2, "max": 200, "default": 50},
            "scale_count": {"type": "int", "min": 2, "max": 20, "default": 5},
            "lower_threshold": {"type": "float", "min": 0, "max": 4, "default": 0.45},
            "upper_threshold": {"type": "float", "min": 0, "max": 4, "default": 0.55},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=100,
    )
    window: int = Field(default=DEFAULT_WINDOW, ge=20)
    min_scale: int = Field(default=DEFAULT_MIN_SCALE, ge=2)
    max_scale: int = Field(default=DEFAULT_MAX_SCALE, ge=2)
    scale_count: int = Field(default=DEFAULT_SCALE_COUNT, ge=2)
    lower_threshold: float = Field(default=DEFAULT_LOWER_THRESHOLD)
    upper_threshold: float = Field(default=DEFAULT_UPPER_THRESHOLD)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.lower_threshold >= self.upper_threshold:
            raise ValueError("lower_threshold must be below upper_threshold")
        if self.min_scale >= self.max_scale:
            raise ValueError("min_scale must be below max_scale")
        if self.max_scale > self.window:
            raise ValueError("max_scale must not exceed window")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.window

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        window = self.window
        min_scale = self.min_scale
        max_scale = self.max_scale
        scale_count = self.scale_count
        lower_threshold = self.lower_threshold
        upper_threshold = self.upper_threshold
        logger.info(
            "HurstExponent initiated: window=%d, min=%d, max=%d",
            window,
            min_scale,
            max_scale,
        )
        self._validate_params(
            window, min_scale, max_scale, lower_threshold, upper_threshold
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input price series cannot be empty")
        scales = self._generate_scales(min_scale, max_scale, scale_count)
        h_vals, reg_vals = self._compute_rolling_hurst(
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
            round(min_scale + i * step)
            for i in range(count)
            if round(min_scale + i * step) >= MIN_SCALE_VALUE
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
            return (h_vals, reg_vals)
        returns = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            prev = p_arr[i - 1]
            returns[i] = math.log(p_arr[i] / prev) if prev > 0.0 else 0.0
        for i in range(window, n):
            sample = returns[i - window + 1 : i + 1]
            h = cls._rs_slope(sample, scales)
            h_vals[i] = h
            reg_vals[i] = cls._classify_regime(h, lower_threshold, upper_threshold)
        return (h_vals, reg_vals)

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
        return is_greater(hurst, upper_threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_anti_persistent(
        cls,
        hurst: IndicatorSeries,
        lower_threshold: float = DEFAULT_LOWER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if series shows anti-persistent mean-reverting memory."""
        logger.info("Evaluating Hurst is_anti_persistent at shift=%d", shift)
        return is_lower(hurst, lower_threshold, shift1=shift, round_digits=8)

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
        return is_greater_or_equal(
            hurst, lower_threshold, shift1=shift, round_digits=8
        ) and is_lower_or_equal(hurst, upper_threshold, shift1=shift, round_digits=8)
