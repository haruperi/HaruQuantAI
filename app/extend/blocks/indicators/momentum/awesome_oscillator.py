"""AwesomeOscillator momentum indicator strategy block.

Description:
    Calculates Awesome Oscillator (AO) as the difference between 5-period
    and 34-period SMAs of median prices.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Awesome oscillator computation.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    res = AwesomeOscillator().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class AwesomeOscillator(BaseIndicator):
    """Awesome Oscillator indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.awesome_oscillator",
        name="AwesomeOscillator",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low"),
        parameter_search_space={
            "fast_period": {"type": "int", "min": 1, "max": 20, "default": 5},
            "slow_period": {"type": "int", "min": 1, "max": 136, "default": 34},
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=34,
    )
    fast_period: int = Field(default=5, ge=1)
    slow_period: int = Field(default=34, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.fast_period, self.slow_period)

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        fast_period = self.fast_period
        slow_period = self.slow_period
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        n = len(high_arr)
        if fast_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid fast_period %d, defaulting to 5",
                fast_period,
            )
            fast_period = 5
        if slow_period <= 0:
            logger.warning(
                "FR-SERVICES-AWO-CALCULATE: Invalid slow_period %d, defaulting to 34",
                slow_period,
            )
            slow_period = 34
        median = (high_arr + low_arr) / 2.0
        fast_sma = sma_kernel(median, fast_period)
        slow_sma = sma_kernel(median, slow_period)
        res = fast_sma - slow_sma
        logger.info(
            "FR-SERVICES-AWO-CALCULATE: Computed AWO(fast=%d, slow=%d) for %d bars",
            fast_period,
            slow_period,
            n,
        )
        return {"value": IndicatorSeries(res, name="AwesomeOscillator")}
