"""DirectionalIndex indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-DIRECTIONALINDEX: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.host.logging import get_logger
from app.include.blocks.comparisons import (
    changes_down,
    changes_up,
    crosses_above,
    crosses_below,
    is_falling,
    is_lower,
    is_rising,
)
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.indicators.trend.adx import ADX
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.series import BarData, IndicatorSeries

logger = get_logger(__name__)


class DirectionalIndex(BaseIndicator):
    """Directional Index indicator family."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.directional_index",
        name="DirectionalIndex",
        category="trend",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("di_plus", PortType.SERIES),
            OutputPort("di_minus", PortType.SERIES),
            OutputPort("dx", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        dependencies=("indicator.trend.adx",),
        required_history_lookback=15,
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.period + 1

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        period = self.period
        adx_dict = ADX(period=period).calculate(bars)
        di_plus = adx_dict["di_plus"]
        di_minus = adx_dict["di_minus"]
        p_vals = di_plus.values
        m_vals = di_minus.values
        denom = p_vals + m_vals
        dx_arr = np.full_like(p_vals, np.nan)
        valid = ~np.isnan(denom) & (denom > 0)
        dx_arr[valid] = 100.0 * np.abs(p_vals[valid] - m_vals[valid]) / denom[valid]
        logger.info(
            "FR-SERVICES-DX-CALCULATE: Computed DX(period=%d) for %d bars",
            period,
            len(p_vals),
        )
        return {
            "di_plus": di_plus,
            "di_minus": di_minus,
            "dx": IndicatorSeries(dx_arr, name=f"DX({period})"),
        }

    @classmethod
    def di_crosses_above(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if DI+ crosses above DI-."""
        return crosses_above(
            di_dict["di_plus"], di_dict["di_minus"], shift=shift, round_digits=8
        )

    @classmethod
    def di_crosses_below(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Check if DI+ crosses below DI-."""
        return crosses_below(
            di_dict["di_plus"], di_dict["di_minus"], shift=shift, round_digits=8
        )

    @classmethod
    def di_plus_rising(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is rising."""
        return is_rising(di_dict["di_plus"], shift=shift)

    @classmethod
    def di_plus_falling(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is falling."""
        return is_falling(di_dict["di_plus"], shift=shift)

    @classmethod
    def di_plus_higher(
        cls, di_dict: dict[str, IndicatorSeries], lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is higher than lookback bars ago."""
        return is_greater(
            di_dict["di_plus"],
            di_dict["di_plus"],
            shift1=shift,
            shift2=shift + lookback,
        )

    @classmethod
    def di_plus_lower(
        cls, di_dict: dict[str, IndicatorSeries], lookback: int = 1, shift: int = 0
    ) -> bool:
        """Evaluate if DI+ is lower than lookback bars ago."""
        return is_lower(
            di_dict["di_plus"],
            di_dict["di_plus"],
            shift1=shift,
            shift2=shift + lookback,
        )

    @classmethod
    def di_plus_changes_up(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ turned upward."""
        return changes_up(di_dict["di_plus"], shift=shift)

    @classmethod
    def di_plus_changes_down(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI+ turned downward."""
        return changes_down(di_dict["di_plus"], shift=shift)

    @classmethod
    def di_minus_rising(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- is rising."""
        return is_rising(di_dict["di_minus"], shift=shift)

    @classmethod
    def di_minus_falling(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- is falling."""
        return is_falling(di_dict["di_minus"], shift=shift)

    @classmethod
    def di_minus_changes_up(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- turned upward."""
        return changes_up(di_dict["di_minus"], shift=shift)

    @classmethod
    def di_minus_changes_down(
        cls, di_dict: dict[str, IndicatorSeries], shift: int = 0
    ) -> bool:
        """Evaluate if DI- turned downward."""
        return changes_down(di_dict["di_minus"], shift=shift)
