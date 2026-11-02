"""ParabolicSAR trend indicator strategy block.

Description:
    Calculates Parabolic Stop and Reverse (SAR) trailing price curve.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Parabolic SAR trailing trend reversal.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    res = ParabolicSAR().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, Self, override

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
from app.extend.blocks.indicators.base import BaseIndicator

logger = get_logger(__name__)
MIN_LOOKBACK_BARS: int = 2


class ParabolicSAR(BaseIndicator):
    """Parabolic SAR indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.parabolic_sar",
        name="ParabolicSAR",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "step": {
                "type": "float",
                "min": 0.0,
                "max": 4,
                "default": 0.02,
                "min_exclusive": True,
            },
            "maximum": {
                "type": "float",
                "min": 0.0,
                "max": 4,
                "default": 0.2,
                "min_exclusive": True,
            },
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=2,
    )
    step: float = Field(default=0.02, gt=0.0)
    maximum: float = Field(default=0.2, gt=0.0)

    @classmethod
    def _step_long(
        cls,
        prev_sar: float,
        af: float,
        ep: float,
        *,
        h_t: float,
        l_t: float,
        step: float,
        maximum: float,
        l_prev1: float,
        l_prev2: float,
    ) -> tuple[float, bool, float, float]:
        """Advance one bar in long state.

        Returns (new_sar, is_long, new_af, new_ep).
        """
        curr_sar = prev_sar + af * (ep - prev_sar)
        curr_sar = min(curr_sar, l_prev1, l_prev2)
        if l_t < curr_sar:
            return (ep, False, step, l_t)
        new_af = min(af + step, maximum) if h_t > ep else af
        new_ep = max(ep, h_t)
        return (curr_sar, True, new_af, new_ep)

    @classmethod
    def _step_short(
        cls,
        prev_sar: float,
        af: float,
        ep: float,
        *,
        h_t: float,
        l_t: float,
        step: float,
        maximum: float,
        h_prev1: float,
        h_prev2: float,
    ) -> tuple[float, bool, float, float]:
        """Advance one bar in short state.

        Returns (new_sar, is_long, new_af, new_ep).
        """
        curr_sar = prev_sar + af * (ep - prev_sar)
        curr_sar = max(curr_sar, h_prev1, h_prev2)
        if h_t > curr_sar:
            return (ep, True, step, h_t)
        new_af = min(af + step, maximum) if l_t < ep else af
        new_ep = min(ep, l_t)
        return (curr_sar, False, new_af, new_ep)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.step > self.maximum:
            raise ValueError("step must not exceed maximum")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 2

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        step = self.step
        maximum = self.maximum
        h_arr = np.asarray(high, dtype=np.float64)
        l_arr = np.asarray(low, dtype=np.float64)
        n = len(h_arr)
        if n != len(l_arr):
            raise ValueError("High and Low arrays must have equal length.")
        step = 0.02 if step <= 0 else step
        maximum = 0.2 if maximum <= 0 else maximum
        sar = np.zeros(n, dtype=np.float64)
        if n == 0:
            return {"value": IndicatorSeries(sar, name=f"PSAR({step},{maximum})")}
        is_long = True
        af = step
        ep = h_arr[0]
        sar[0] = l_arr[0]
        for t in range(1, n):
            prev_sar = sar[t - 1]
            if is_long:
                l_p1 = l_arr[t - 1]
                l_p2 = l_arr[t - 2] if t >= MIN_LOOKBACK_BARS else l_p1
                sar[t], is_long, af, ep = self._step_long(
                    prev_sar,
                    af,
                    ep,
                    h_t=h_arr[t],
                    l_t=l_arr[t],
                    step=step,
                    maximum=maximum,
                    l_prev1=l_p1,
                    l_prev2=l_p2,
                )
            else:
                h_p1 = h_arr[t - 1]
                h_p2 = h_arr[t - 2] if t >= MIN_LOOKBACK_BARS else h_p1
                sar[t], is_long, af, ep = self._step_short(
                    prev_sar,
                    af,
                    ep,
                    h_t=h_arr[t],
                    l_t=l_arr[t],
                    step=step,
                    maximum=maximum,
                    h_prev1=h_p1,
                    h_prev2=h_p2,
                )
        logger.info(
            "FR-SERVICES-PSAR-CALCULATE: PSAR(step=%.3f, max=%.2f) for %d bars",
            step,
            maximum,
            n,
        )
        return {"value": IndicatorSeries(sar, name=f"PSAR({step},{maximum})")}
