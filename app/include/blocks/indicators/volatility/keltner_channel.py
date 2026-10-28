"""KeltnerChannel indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-KELTNERCHANNEL: validated batch calculation.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import is_falling, is_lower, is_rising
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
from app.include.calculators.average import sma_kernel

logger = get_logger(__name__)


class KeltnerChannel(BaseIndicator):
    """Keltner Channel indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.keltner_channel",
        name="KeltnerChannel",
        category="volatility",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("upper", PortType.SERIES),
            OutputPort("middle", PortType.SERIES),
            OutputPort("lower", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
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
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=20,
    )
    period: int = Field(default=20, ge=1)
    deviation: float = Field(default=1.5, gt=0.0)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
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

    @classmethod
    def bar_closes_above_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesAboveUpper (`Close[shift] > Upper[shift]`)."""
        return is_greater(close_series, kc_dict["upper"], shift=shift)

    @classmethod
    def bar_closes_below_upper(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesBelowUpper (`Close[shift] < Upper[shift]`)."""
        return is_lower(close_series, kc_dict["upper"], shift=shift)

    @classmethod
    def bar_closes_above_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesAboveLower (`Close[shift] > Lower[shift]`)."""
        return is_greater(close_series, kc_dict["lower"], shift=shift)

    @classmethod
    def bar_closes_below_lower(
        cls,
        close_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarClosesBelowLower (`Close[shift] < Lower[shift]`)."""
        return is_lower(close_series, kc_dict["lower"], shift=shift)

    @classmethod
    def bar_opens_above_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveUpper (`Open[shift] > Upper[shift + 1]`)."""
        return is_greater(
            open_series,
            kc_dict["upper"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below_upper(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowUpper (`Open[shift] < Upper[shift + 1]`)."""
        return is_lower(
            open_series,
            kc_dict["upper"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_above_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensAboveLower (`Open[shift] > Lower[shift + 1]`)."""
        return is_greater(
            open_series,
            kc_dict["lower"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

    @classmethod
    def bar_opens_below_lower(
        cls,
        open_series: IndicatorSeries | Sequence[float] | np.ndarray,
        kc_dict: dict[str, IndicatorSeries],
        shift: int = 0,
    ) -> bool:
        """Evaluate KCBarOpensBelowLower (`Open[shift] < Lower[shift + 1]`)."""
        return is_lower(
            open_series,
            kc_dict["lower"],
            shift1=shift,
            shift2=shift + 1,
            round_digits=8,
        )

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

    @classmethod
    def upper_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is rising."""
        return is_rising(kc_dict["upper"], shift=shift)

    @classmethod
    def upper_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Upper band is falling."""
        return is_falling(kc_dict["upper"], shift=shift)

    @classmethod
    def lower_is_rising(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is rising."""
        return is_rising(kc_dict["lower"], shift=shift)

    @classmethod
    def lower_is_falling(
        cls, kc_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if Lower band is falling."""
        return is_falling(kc_dict["lower"], shift=shift)
