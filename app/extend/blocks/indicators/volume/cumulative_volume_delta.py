"""CumulativeVolumeDelta volume indicator strategy block.

Description:
    Calculates Cumulative Volume Delta (CVD) tracking net market order pressure.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative volume indicator library.
Key Capabilities:
    - FR-indicator-volume: Cumulative volume delta calculation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    res = CumulativeVolumeDelta().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons import (
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_CVD_WINDOW: int = 1
DEFAULT_CVD_WINDOW: int = 14
MIN_ATI_WINDOW: int = 1
DEFAULT_ATI_WINDOW: int = 14
DEFAULT_BUYER_THRESHOLD: float = 0.2
DEFAULT_SELLER_THRESHOLD: float = -0.2
EPSILON: float = 1e-12


class CumulativeVolumeDelta(BaseIndicator):
    """Cumulative Volume Delta (CVD) tracking net aggressive buying/selling volume."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.cumulative_volume_delta",
        name="CumulativeVolumeDelta",
        category="volume",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("open", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
            InputPort("volume", PortType.SERIES, required=True),
            InputPort("buy_volume", PortType.SERIES, required=False),
            InputPort("sell_volume", PortType.SERIES, required=False),
        ),
        outputs=(
            OutputPort("cvd", PortType.SERIES),
            OutputPort("delta", PortType.SERIES),
        ),
        required_market_inputs=("open", "close", "volume"),
        parameter_search_space={
            "window": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    window: int = Field(default=DEFAULT_CVD_WINDOW, ge=MIN_CVD_WINDOW)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.window < MIN_CVD_WINDOW:
            raise ValueError(f"window must be >= {MIN_CVD_WINDOW}, got {self.window}")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.window

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        if bars.has_input("buy_volume") != bars.has_input("sell_volume"):
            raise ValueError("buy_volume and sell_volume must be supplied together")
        open_prices = bars.open
        close = bars.close
        volume = bars.volume
        buy_volume = bars.input("buy_volume", required=False)
        sell_volume = bars.input("sell_volume", required=False)
        window = self.window
        logger.info("CumulativeVolumeDelta calculation initiated: window=%d", window)
        o_arr = to_numpy(open_prices)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        bar_deltas = self._extract_bar_deltas(
            o_arr, c_arr, v_arr, buy_volume, sell_volume=sell_volume
        )
        cvd_vals = np.cumsum(bar_deltas)
        rolling_delta = self._compute_rolling_delta(bar_deltas, window, n)
        logger.info("CumulativeVolumeDelta calculation completed: bars=%d", n)
        return {
            "cvd": IndicatorSeries(cvd_vals, name="CVD"),
            "delta": IndicatorSeries(rolling_delta, name=f"CVD_Delta({window})"),
        }

    @classmethod
    def _extract_bar_deltas(
        cls,
        o_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
        *,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> np.ndarray[Any, Any]:
        """Extract bar delta values from taker volumes or price direction."""
        n = len(c_arr)
        if buy_volume is not None and sell_volume is not None:
            b_arr = to_numpy(buy_volume)
            s_arr = to_numpy(sell_volume)
            if len(b_arr) != n or len(s_arr) != n:
                raise ValueError("buy_volume and sell_volume lengths must match price")
            diff: np.ndarray[Any, Any] = np.asarray(b_arr - s_arr, dtype=np.float64)
            return diff
        sign = np.where(c_arr >= o_arr, 1.0, -1.0)
        res: np.ndarray[Any, Any] = np.asarray(sign * v_arr, dtype=np.float64)
        return res

    @classmethod
    def _compute_rolling_delta(
        cls, bar_deltas: np.ndarray[Any, Any], window: int, n: int
    ) -> np.ndarray[Any, Any]:
        """Compute rolling window delta over specified lookback."""
        rolling = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - window + 1)
            rolling[i] = float(np.sum(bar_deltas[start : i + 1]))
        return rolling

    @classmethod
    def is_positive(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD value is positive at shift."""
        logger.info("Evaluating CVD is_positive at shift=%d", shift)
        return is_greater(cvd, 0.0, shift1=shift)

    @classmethod
    def is_negative(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD value is negative at shift."""
        logger.info("Evaluating CVD is_negative at shift=%d", shift)
        return is_lower(cvd, 0.0, shift1=shift)

    @classmethod
    def crosses_above_zero(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD crosses above zero at shift."""
        logger.info("Evaluating CVD crosses_above_zero at shift=%d", shift)
        return crosses_above(cvd, 0.0, shift=shift)

    @classmethod
    def crosses_below_zero(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD crosses below zero at shift."""
        logger.info("Evaluating CVD crosses_below_zero at shift=%d", shift)
        return crosses_below(cvd, 0.0, shift=shift)

    @classmethod
    def is_rising(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating CVD is_rising at shift=%d", shift)
        return is_rising(cvd, shift=shift)

    @classmethod
    def is_falling(cls, cvd: IndicatorSeries, shift: int = 0) -> bool:
        """True if CVD is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating CVD is_falling at shift=%d", shift)
        return is_falling(cvd, shift=shift)
