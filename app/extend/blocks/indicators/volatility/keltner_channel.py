"""KeltnerChannel indicator.

- Calculates Keltner Channel EMA center line with ATR volatility envelope.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

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
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)


class KeltnerChannel(BaseIndicator):
    """Keltner Channel indicator family."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.keltner_channel",
        version="1.0.0",
        name="KeltnerChannel",
        description=(
            "Calculates Keltner Channel EMA center line with ATR volatility envelope."
        ),
        category="volatility",
        tags=("volatility", "keltner-channel"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
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
            OutputPort("upper", PortType.SERIES, description="Upper output series"),
            OutputPort("middle", PortType.SERIES, description="Middle output series"),
            OutputPort("lower", PortType.SERIES, description="Lower output series"),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 80, "default": 20},
            "deviation": {
                "type": "float",
                "min": 0.0,
                "max": 6.0,
                "default": 1.5,
                "min_exclusive": True,
            },
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=20,
        ge=1,
        title="Period",
        description="Number of bars in the calculation window",
    )

    deviation: float = Field(
        default=1.5,
        gt=0.0,
        title="Deviation",
        description="Deviation used by the indicator calculation",
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: KeltnerChannel requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        deviation = self.deviation
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-KELTNER-CALCULATE: Invalid period %d, defaulting to 20",
                period,
            )
            period = 20
        typical = (high_arr + low_arr + close_arr) / 3.0
        bar_range = high_arr - low_arr
        middle = sma_kernel(typical, period)
        offset = sma_kernel(bar_range, period) * deviation
        upper = middle + offset
        lower = middle - offset
        logger.info(
            "FR-SERVICES-KELTNER-CALCULATE: KC(period=%d, dev=%.2f) for %d bars",
            period,
            deviation,
            n,
        )
        return {
            "upper": IndicatorSeries(upper, name="KC.Upper"),
            "middle": IndicatorSeries(middle, name="KC.Middle"),
            "lower": IndicatorSeries(lower, name="KC.Lower"),
        }

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def bar_opens_above_upper_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveUpperAfterOpenBelow (`Open[s+1] < Upper[s+1]`)."""
        return is_lower(
            open_series,
            kc_dict["upper"],
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_greater(
            open_series,
            kc_dict["upper"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below_upper_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowUpperAfterOpenAbove (`Open[s+1] > Upper[s+1]`)."""
        return is_greater(
            open_series,
            kc_dict["upper"],
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_lower(
            open_series,
            kc_dict["upper"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_above_lower_after_open_below(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveLowerAfterOpenBelow (`Open[s+1] < Lower[s+1]`)."""
        return is_lower(
            open_series,
            kc_dict["lower"],
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_greater(
            open_series,
            kc_dict["lower"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below_lower_after_open_above(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowLowerAfterOpenAbove (`Open[s+1] > Lower[s+1]`)."""
        return is_greater(
            open_series,
            kc_dict["lower"],
            shift1=shift + 1,
            shift2=shift + 1,
            round_digits=8,
        ) and is_lower(
            open_series,
            kc_dict["lower"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )


# Public exports.
__all__ = ["KeltnerChannel"]
