"""CCI indicator and related signal helpers.

FEAT-SERVICES-INDICATOR-CCI: validated batch calculation.
"""

from __future__ import annotations

from typing import ClassVar, override

import numpy as np
from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.average import sma_kernel

logger = get_logger(__name__)
WOODIES_ZLR_BAND: float = 100.0
WOODIES_FAMIR_LEVEL: float = 50.0
WOODIES_VEGAS_LEVEL: float = 200.0


class CCI(BaseIndicator):
    """Commodity Channel Index family consolidating calculation and conditions."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.momentum.cci",
        name="CCI",
        category="momentum",
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(OutputPort("value", PortType.SERIES),),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "period": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_causal=True,
        is_generation_eligible=True,
        required_history_lookback=14,
    )
    period: int = Field(default=14, ge=1)

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
        high_arr = np.asarray(high, dtype=np.float64)
        low_arr = np.asarray(low, dtype=np.float64)
        close_arr = np.asarray(close, dtype=np.float64)
        n = len(close_arr)
        if period <= 0:
            logger.warning(
                "FR-SERVICES-CCI-CALCULATE: Invalid period %d, defaulting to 14", period
            )
            period = 14
        tp = (high_arr + low_arr + close_arr) / 3.0
        sma_tp = sma_kernel(tp, period)
        cci_vals = np.full(n, np.nan, dtype=np.float64)
        for i in range(period - 1, n):
            window = tp[i - period + 1 : i + 1]
            mean_dev = float(np.mean(np.abs(window - sma_tp[i])))
            if mean_dev != 0.0:
                cci_vals[i] = (tp[i] - sma_tp[i]) / (0.015 * mean_dev)
            else:
                cci_vals[i] = 0.0
        logger.info(
            "FR-SERVICES-CCI-CALCULATE: Computed CCI(period=%d) for %d bars", period, n
        )
        return {"value": IndicatorSeries(cci_vals, name="CCI")}

    @staticmethod
    def _vals(series: IndicatorSeries, count: int, shift: int) -> list[float] | None:
        vals = [series.get(shift + k) for k in range(count)]
        if any(np.isnan(v) for v in vals):
            return None
        return vals

    @classmethod
    def woodies_zlr_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesZLRUP zero-line reject bullish hook."""
        v = cls._vals(series, 6, shift)
        if v is None:
            return False
        curr, c1, c2 = (v[0], v[1], v[2])
        trend_up = all(x > 0.0 for x in v)
        hook_up = curr > c1 and c2 > c1
        factor_cond = curr - c1 > factor and c2 - c1 > factor
        in_band = all(-WOODIES_ZLR_BAND < x < WOODIES_ZLR_BAND for x in (curr, c1, c2))
        return trend_up and hook_up and factor_cond and in_band

    @classmethod
    def woodies_zlr_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesZLRDown zero-line reject bearish hook."""
        v = cls._vals(series, 6, shift)
        if v is None:
            return False
        curr, c1, c2 = (v[0], v[1], v[2])
        trend_dn = all(x < 0.0 for x in v)
        hook_dn = curr < c1 and c2 < c1
        factor_cond = c1 - curr > factor and c1 - c2 > factor
        in_band = all(-WOODIES_ZLR_BAND < x < WOODIES_ZLR_BAND for x in (curr, c1, c2))
        return trend_dn and hook_dn and factor_cond and in_band

    @classmethod
    def woodies_famir_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesFamirUP failed ZLR bullish reversal."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3 = (v[0], v[1], v[2], v[3])
        prior_neg = all(x < 0.0 for x in v[1:])
        broken_hook = c1 < c2 and c3 < c2 and (curr > c1)
        factor_cond = c2 - c1 > factor and c2 - c3 > factor
        return curr > -WOODIES_FAMIR_LEVEL and prior_neg and broken_hook and factor_cond

    @classmethod
    def woodies_famir_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesFamirDown failed ZLR bearish reversal."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3 = (v[0], v[1], v[2], v[3])
        prior_pos = all(x > 0.0 for x in v[1:])
        broken_hook = c1 > c2 and c3 > c2 and (curr < c1)
        factor_cond = c1 - c2 > factor and c3 - c2 > factor
        return curr < WOODIES_FAMIR_LEVEL and prior_pos and broken_hook and factor_cond

    @classmethod
    def woodies_vegas_trade_up(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesVegasTradeUP extreme exhaustion bullish setup."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3, c4 = (v[0], v[1], v[2], v[3], v[4])
        trend_dn = all(x < 0.0 for x in v[1:])
        area200 = any(x < -WOODIES_VEGAS_LEVEL for x in v[1:6])
        basket_up = c1 < c2 and c1 < c3 and (c4 < c2) and (c4 < c3)
        factor_cond = c2 - c1 > factor and c3 - c4 > factor
        return (
            area200
            and basket_up
            and factor_cond
            and trend_dn
            and (curr > (c3 + c2) / 2.0)
        )

    @classmethod
    def woodies_vegas_trade_down(
        cls, series: IndicatorSeries, factor: float = 15.0, shift: int = 0
    ) -> bool:
        """Evaluate WoodiesVegasTradeDown extreme exhaustion bearish setup."""
        v = cls._vals(series, 7, shift)
        if v is None:
            return False
        curr, c1, c2, c3, c4 = (v[0], v[1], v[2], v[3], v[4])
        trend_up = all(x > 0.0 for x in v[1:])
        area200 = any(x > WOODIES_VEGAS_LEVEL for x in v[1:6])
        basket_dn = c1 > c2 and c1 > c3 and (c4 > c2) and (c4 > c3)
        factor_cond = c4 - c3 > factor and c1 - c2 > factor
        return (
            area200
            and basket_dn
            and factor_cond
            and trend_up
            and (curr < (c3 + c2) / 2.0)
        )
