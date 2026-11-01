"""LaguerreRSI indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-LAGUERRERSI: validated batch calculation.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import (
    changes_down,
    changes_up,
    crosses_above,
    crosses_below,
    is_falling,
    is_rising,
)
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.include.calculators.base import to_numpy

logger = get_logger(__name__)
WARMUP_BARS: int = 20
DEFAULT_GAMMA: float = 0.5


class LaguerreRSI(BaseIndicator):
    """John Ehlers' 4-element Laguerre filter Relative Strength Index."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.laguerre_rsi",
        name="LaguerreRSI",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(InputPort("close", PortType.SERIES, required=True),),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("close",),
        parameter_search_space={
            "gamma": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=1,
    )
    gamma: float = Field(default=DEFAULT_GAMMA, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if not 0.0 <= self.gamma <= 1.0:
            raise ValueError(f"Gamma must be between 0.0 and 1.0, got {self.gamma}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        price = bars.close
        gamma = self.gamma
        logger.info(
            "LaguerreRSI calculation initiated with gamma=%.3f",
            gamma,
            extra={"gamma": gamma},
        )
        p_arr = to_numpy(price)
        n = len(p_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        lrsi_vals = np.zeros(n, dtype=np.float64)
        if n <= WARMUP_BARS:
            return {
                "value": IndicatorSeries(lrsi_vals, name=f"LaguerreRSI({gamma:.2f})")
            }
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
            curr_l0 = (1.0 - gamma) * c_val + gamma * prev_l0
            curr_l1 = -gamma * curr_l0 + prev_l0 + gamma * prev_l1
            curr_l2 = -gamma * curr_l1 + prev_l1 + gamma * prev_l2
            curr_l3 = -gamma * curr_l2 + prev_l2 + gamma * prev_l3
            l0[i] = curr_l0
            l1[i] = curr_l1
            l2[i] = curr_l2
            l3[i] = curr_l3
            cu, cd = self._calc_cu_cd(curr_l0, curr_l1, curr_l2, curr_l3)
            total = cu + cd
            lrsi_vals[i] = cu / total if total != 0.0 else 0.0
        logger.info(
            "LaguerreRSI calculation complete: bars=%d, gamma=%.3f",
            n,
            gamma,
            extra={"bars": n, "gamma": gamma},
        )
        return {"value": IndicatorSeries(lrsi_vals, name=f"LaguerreRSI({gamma:.2f})")}

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
        return (cu, cd)

    @staticmethod
    def is_rising(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Laguerre RSI is rising."""
        logger.info("Evaluating LaguerreRSI is_rising at shift=%d", shift)
        return is_rising(series, shift=shift)

    @staticmethod
    def is_falling(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Laguerre RSI is falling."""
        logger.info("Evaluating LaguerreRSI is_falling at shift=%d", shift)
        return is_falling(series, shift=shift)

    @staticmethod
    def crosses_above(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 0.2,
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI crossed above a threshold level."""
        logger.info("Evaluating LaguerreRSI crosses_above at shift=%d", shift)
        return crosses_above(series, level, shift=shift)

    @staticmethod
    def crosses_below(
        series: IndicatorSeries | np.ndarray[Any, Any],
        level: float = 0.8,
        shift: int = 0,
    ) -> bool:
        """Check if Laguerre RSI crossed below a threshold level."""
        logger.info("Evaluating LaguerreRSI crosses_below at shift=%d", shift)
        return crosses_below(series, level, shift=shift)

    @staticmethod
    def changes_up(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Laguerre RSI turned upward (v0 > v1 and v1 <= v2)."""
        logger.info("Evaluating LaguerreRSI changes_up at shift=%d", shift)
        return changes_up(series, shift=shift)

    @staticmethod
    def changes_down(
        series: IndicatorSeries | np.ndarray[Any, Any], shift: int = 0
    ) -> bool:
        """Check if Laguerre RSI turned downward (v0 < v1 and v1 >= v2)."""
        logger.info("Evaluating LaguerreRSI changes_down at shift=%d", shift)
        return changes_down(series, shift=shift)
