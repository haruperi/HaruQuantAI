"""ParabolicSAR indicator.

- Calculates Parabolic Stop and Reverse (SAR) trailing price curve.
"""

from __future__ import annotations

from typing import ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
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

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.parabolic_sar",
        version="1.0.0",
        name="ParabolicSAR",
        description="Calculates Parabolic Stop and Reverse (SAR) trailing price curve.",
        category="trend",
        tags=("trend", "parabolic-sar"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("high", "low"),
        required_history_lookback=2,
        dependencies=(),
        is_generation_eligible=True,
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
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    step: float = Field(
        default=0.02,
        gt=0.0,
        title="Step",
        description="Step used by the indicator calculation",
    )

    maximum: float = Field(
        default=0.2,
        gt=0.0,
        title="Maximum",
        description="Maximum used by the indicator calculation",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.step > self.maximum:
            raise ValueError("step must not exceed maximum")
        return self

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return 2

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: ParabolicSAR requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
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

    # Specialized methods: indicator-specific behavior only.
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


# Public exports.
__all__ = ["ParabolicSAR"]
