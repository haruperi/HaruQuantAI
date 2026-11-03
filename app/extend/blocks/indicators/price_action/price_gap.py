"""PriceGap indicator.

- Detects opening, runaway, and exhaustion price gaps in time series.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np
from pydantic import Field

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
from app.extend.blocks.comparisons import is_lower
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_GAP_THRESHOLD: float = 0.5
EPSILON: float = 1e-12


class PriceGap(BaseIndicator):
    """Price Gap detection and fill tracking block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.price_gap",
        version="1.0.0",
        name="PriceGap",
        description=(
            "Detects opening, runaway, and exhaustion price gaps in time series."
        ),
        category="price_action",
        tags=("price_action", "price-gap"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "open", PortType.SERIES, required=True, description="Open input series"
            ),
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort(
                "gap_size", PortType.SERIES, description="Gap size output series"
            ),
            OutputPort(
                "gap_filled", PortType.SERIES, description="Gap filled output series"
            ),
        ),
        required_market_inputs=("open", "high", "low", "close"),
        required_history_lookback=2,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "full_gap": {"type": "bool", "choices": [False, True], "default": True}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    full_gap: bool = Field(
        default=True,
        title="Full gap",
        description="Full gap used by the indicator calculation",
    )

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
        logger.debug("FR-indicator-calculation: PriceGap requested bars=%d", len(bars))
        bars.require_inputs(self.required_inputs())
        open_prices = bars.open
        high = bars.high
        low = bars.low
        close = bars.close
        full_gap = self.full_gap
        logger.info("PriceGap.calculate called: full_gap=%s", full_gap)
        o_arr = to_numpy(open_prices)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or (len(l_arr) != n):
            raise ValueError("Arrays cannot be empty and lengths must match")
        gap_size, gap_filled = self._compute_gaps(
            (o_arr, h_arr, l_arr, c_arr), full_gap
        )
        logger.info("PriceGap completed: bars=%d", n)
        mode_label = "Full" if full_gap else "Body"
        return {
            "gap_size": IndicatorSeries(gap_size, name=f"PriceGapSize({mode_label})"),
            "gap_filled": IndicatorSeries(
                gap_filled, name=f"PriceGapFilled({mode_label})"
            ),
        }

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def _compute_gaps(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        full_gap: bool,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        gap_size = np.zeros(n, dtype=np.float64)
        gap_filled = np.zeros(n, dtype=np.float64)
        for i in range(1, n):
            prev_h = h_arr[i - 1]
            prev_l = l_arr[i - 1]
            if full_gap:
                if l_arr[i] > prev_h:
                    gap_size[i] = l_arr[i] - prev_h
                elif h_arr[i] < prev_l:
                    gap_size[i] = h_arr[i] - prev_l
            elif o_arr[i] > prev_h:
                gap_size[i] = o_arr[i] - prev_h
                if l_arr[i] <= prev_h:
                    gap_filled[i] = 1.0
            elif o_arr[i] < prev_l:
                gap_size[i] = o_arr[i] - prev_l
                if h_arr[i] >= prev_l:
                    gap_filled[i] = 1.0
        return (gap_size, gap_filled)

    @classmethod
    def is_gap_up(
        cls, gap_series: IndicatorSeries, min_size: float = 0.0, shift: int = 0
    ) -> bool:
        """True if positive price gap exceeds minimum size at shift."""
        logger.info(
            "Evaluating PriceGap.is_gap_up: min_size=%.2f, shift=%d", min_size, shift
        )
        return is_greater(gap_series, min_size, shift1=shift, round_digits=8)

    @classmethod
    def is_gap_down(
        cls, gap_series: IndicatorSeries, min_size: float = 0.0, shift: int = 0
    ) -> bool:
        """True if negative price gap exceeds minimum magnitude at shift."""
        logger.info(
            "Evaluating PriceGap.is_gap_down: min_size=%.2f, shift=%d", min_size, shift
        )
        return is_lower(gap_series, -min_size, shift1=shift, round_digits=8)

    @classmethod
    def is_gap_filled(cls, gap_filled_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if price gap was filled within the bar at shift."""
        logger.info("Evaluating PriceGap.is_gap_filled: shift=%d", shift)
        return is_greater(
            gap_filled_series, DEFAULT_GAP_THRESHOLD, shift1=shift, round_digits=8
        )


# Public exports.
__all__ = ["PriceGap"]
