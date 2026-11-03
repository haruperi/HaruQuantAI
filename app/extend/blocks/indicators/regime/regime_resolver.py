"""MarketRegimeResolver indicator.

- Resolves consolidated multi-dimensional market regime states and labels.
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

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
from app.extend.blocks.comparisons import equals
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.regime.choppiness import ChoppinessIndex
from app.extend.blocks.indicators.trend.adx import ADX
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
REGIME_TRANSITION: float = 1.0
REGIME_RANGE: float = 2.0
REGIME_CHOPPY_RANGE: float = 3.0
REGIME_TREND_UP: float = 4.0
REGIME_TREND_DOWN: float = 5.0
REGIME_BREAKOUT_UP: float = 6.0
REGIME_BREAKOUT_DOWN: float = 7.0
REGIME_LOW_LIQUIDITY: float = 8.0
REGIME_UNSTABLE: float = 9.0
DEFAULT_ADX_PERIOD: int = 14
DEFAULT_ADX_THRESHOLD: float = 25.0
WEAK_TREND_ADX: float = 20.0
DEFAULT_CHOP_PERIOD: int = 14
DEFAULT_CHOP_LOWER: float = 38.2
DEFAULT_CHOP_UPPER: float = 61.8
DEFAULT_DONCHIAN_PERIOD: int = 20
BREAKOUT_CONFIDENCE: float = 0.85
RANGE_CONFIDENCE: float = 0.7
TRANSITION_CONFIDENCE: float = 0.5


class MarketRegimeResolver(BaseIndicator):
    """Multi-factor market regime resolver and confidence estimator."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.regime.regime_resolver",
        version="1.0.0",
        name="MarketRegimeResolver",
        description=(
            "Resolves consolidated multi-dimensional market regime states and labels."
        ),
        category="regime",
        tags=("regime", "regime-resolver"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
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
            InputPort(
                "volume",
                PortType.SERIES,
                required=False,
                description="Volume input series",
            ),
        ),
        outputs=(
            OutputPort("regime", PortType.SERIES, description="Regime output series"),
            OutputPort(
                "confidence", PortType.SERIES, description="Confidence output series"
            ),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=28,
        dependencies=("indicator.regime.choppiness", "indicator.trend.adx"),
        is_generation_eligible=True,
        parameter_search_space={
            "adx_period": {"type": "int", "min": 1, "max": 56, "default": 14},
            "adx_threshold": {"type": "float", "min": 0, "max": 100.0, "default": 25.0},
            "chop_period": {"type": "int", "min": 1, "max": 56, "default": 14},
            "chop_lower": {"type": "float", "min": 0, "max": 152.8, "default": 38.2},
            "chop_upper": {"type": "float", "min": 0, "max": 247.2, "default": 61.8},
            "donchian_period": {"type": "int", "min": 1, "max": 80, "default": 20},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    adx_period: int = Field(
        default=DEFAULT_ADX_PERIOD,
        ge=1,
        title="Adx period",
        description="Number of bars in the adx window",
    )

    adx_threshold: float = Field(
        default=DEFAULT_ADX_THRESHOLD,
        title="Adx threshold",
        description="ADX level used to identify a trending market",
    )

    chop_period: int = Field(
        default=DEFAULT_CHOP_PERIOD,
        ge=1,
        title="Chop period",
        description="Number of bars in the chop window",
    )

    chop_lower: float = Field(
        default=DEFAULT_CHOP_LOWER,
        title="Chop lower",
        description="Lower choppiness boundary used for regime classification",
    )

    chop_upper: float = Field(
        default=DEFAULT_CHOP_UPPER,
        title="Chop upper",
        description="Upper choppiness boundary used for regime classification",
    )

    donchian_period: int = Field(
        default=DEFAULT_DONCHIAN_PERIOD,
        ge=1,
        title="Donchian period",
        description="Number of bars in the donchian window",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Reject inconsistent settings before calculation."""
        if self.chop_lower >= self.chop_upper:
            raise ValueError("chop_lower must be below chop_upper")
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
        return max(2 * self.adx_period, self.chop_period, self.donchian_period)

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: MarketRegimeResolver requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        adx_period = self.adx_period
        adx_threshold = self.adx_threshold
        chop_period = self.chop_period
        chop_lower = self.chop_lower
        chop_upper = self.chop_upper
        donchian_period = self.donchian_period
        logger.info(
            "MarketRegimeResolver initiated: adx=%d, chop=%d, donchian=%d",
            adx_period,
            chop_period,
            donchian_period,
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError(
                "High, Low, and Close arrays cannot be empty and lengths must match"
            )
        adx_dict = ADX(period=adx_period).calculate(bars)
        adx_vals = adx_dict["main"].values
        pdi_vals = adx_dict["di_plus"].values
        mdi_vals = adx_dict["di_minus"].values
        chop_dict = ChoppinessIndex(
            period=chop_period, lower_threshold=chop_lower, upper_threshold=chop_upper
        ).calculate(bars)
        chop_vals = chop_dict["chop"].values
        regime_vals, conf_vals = self._resolve_regimes(
            prices=(h_arr, l_arr, c_arr),
            adx_data=(adx_vals, pdi_vals, mdi_vals),
            chop_vals=chop_vals,
            adx_thresh=adx_threshold,
            chop_bounds=(chop_lower, chop_upper),
            donchian_period=donchian_period,
        )
        return {
            "regime": IndicatorSeries(regime_vals, name="MarketRegime"),
            "confidence": IndicatorSeries(conf_vals, name="RegimeConfidence"),
        }

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def _resolve_regimes(
        cls,
        *,
        prices: tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]],
        adx_data: tuple[
            np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]
        ],
        chop_vals: np.ndarray[Any, Any],
        adx_thresh: float,
        chop_bounds: tuple[float, float],
        donchian_period: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        h_arr, l_arr, c_arr = prices
        adx_vals, pdi_vals, mdi_vals = adx_data
        chop_lower, chop_upper = chop_bounds
        n = len(c_arr)
        regime = np.full(n, REGIME_TRANSITION, dtype=np.float64)
        confidence = np.full(n, TRANSITION_CONFIDENCE, dtype=np.float64)
        for i in range(n):
            c = c_arr[i]
            adx = adx_vals[i]
            pdi = pdi_vals[i]
            mdi = mdi_vals[i]
            chop = chop_vals[i]
            start = max(0, i - donchian_period)
            upper_band = float(np.max(h_arr[start:i])) if i > 0 else h_arr[0]
            lower_band = float(np.min(l_arr[start:i])) if i > 0 else l_arr[0]
            r, conf = cls._classify_single_bar(
                c=c,
                bands=(upper_band, lower_band),
                dmi=(adx, pdi, mdi),
                chop=chop,
                thresholds=(adx_thresh, chop_lower, chop_upper),
            )
            regime[i] = r
            confidence[i] = conf
        return (regime, confidence)

    @staticmethod
    def _classify_single_bar(
        *,
        c: float,
        bands: tuple[float, float],
        dmi: tuple[float, float, float],
        chop: float,
        thresholds: tuple[float, float, float],
    ) -> tuple[float, float]:
        """Classify a single bar into regime and confidence score."""
        upper_band, lower_band = bands
        adx, pdi, mdi = dmi
        adx_thresh, chop_lower, chop_upper = thresholds
        if upper_band > 0.0 and c >= upper_band:
            return (REGIME_BREAKOUT_UP, BREAKOUT_CONFIDENCE)
        if lower_band > 0.0 and c <= lower_band:
            return (REGIME_BREAKOUT_DOWN, BREAKOUT_CONFIDENCE)
        if not np.isnan(adx) and (adx >= adx_thresh or chop <= chop_lower):
            reg = REGIME_TREND_UP if pdi > mdi else REGIME_TREND_DOWN
            return (reg, min(1.0, max(0.5, adx / 50.0)))
        if chop >= chop_upper:
            return (REGIME_CHOPPY_RANGE, min(1.0, chop / 100.0))
        if not np.isnan(adx) and adx < WEAK_TREND_ADX:
            return (REGIME_RANGE, RANGE_CONFIDENCE)
        return (REGIME_TRANSITION, TRANSITION_CONFIDENCE)

    @classmethod
    def is_uptrend(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is in uptrend or upward breakout."""
        logger.info("Evaluating MarketRegimeResolver is_uptrend at shift=%d", shift)
        return equals(regime, REGIME_TREND_UP, shift1=shift) or equals(
            regime, REGIME_BREAKOUT_UP, shift1=shift
        )

    @classmethod
    def is_downtrend(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is in downtrend or downward breakout."""
        logger.info("Evaluating MarketRegimeResolver is_downtrend at shift=%d", shift)
        return equals(regime, REGIME_TREND_DOWN, shift1=shift) or equals(
            regime, REGIME_BREAKOUT_DOWN, shift1=shift
        )

    @classmethod
    def is_ranging(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is ranging or in choppy consolidation."""
        logger.info("Evaluating MarketRegimeResolver is_ranging at shift=%d", shift)
        return equals(regime, REGIME_RANGE, shift1=shift) or equals(
            regime, REGIME_CHOPPY_RANGE, shift1=shift
        )

    @classmethod
    def is_breakout(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is breaking out above or below channels."""
        logger.info("Evaluating MarketRegimeResolver is_breakout at shift=%d", shift)
        return equals(regime, REGIME_BREAKOUT_UP, shift1=shift) or equals(
            regime, REGIME_BREAKOUT_DOWN, shift1=shift
        )


# Public exports.
__all__ = ["MarketRegimeResolver"]
