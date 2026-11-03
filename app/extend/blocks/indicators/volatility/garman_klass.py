"""GarmanKlassVolatility indicator.

- Calculates Garman-Klass volatility estimator incorporating OHLC prices.
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
MIN_GK_PERIOD: int = 2
DEFAULT_GK_PERIOD: int = 20
DEFAULT_TRADING_PERIODS: int = 252
EPSILON: float = 1e-12
GK_HIGH_LOW_FACTOR: float = 0.5
GK_CLOSE_FACTOR: float = 2.0 * np.log(2.0) - 1.0


class GarmanKlassVolatility(BaseIndicator):
    """Garman-Klass OHLC volatility estimator block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.garman_klass",
        version="1.0.0",
        name="GarmanKlassVolatility",
        description=(
            "Calculates Garman-Klass volatility estimator incorporating OHLC prices."
        ),
        category="volatility",
        tags=("volatility", "garman-klass"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
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
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("open", "high", "low", "close"),
        required_history_lookback=20,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 80, "default": 20},
            "annualize": {"type": "bool", "choices": [False, True], "default": False},
            "trading_periods": {"type": "int", "min": 1, "max": 1008, "default": 252},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    period: int = Field(
        default=DEFAULT_GK_PERIOD,
        ge=MIN_GK_PERIOD,
        title="Period",
        description="Number of bars in the calculation window",
    )

    annualize: bool = Field(
        default=False,
        title="Annualize",
        description="Whether to scale volatility to an annual value",
    )

    trading_periods: int = Field(
        default=DEFAULT_TRADING_PERIODS,
        ge=1,
        title="Trading periods",
        description="Number of trading periods per year for annualization",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.period < MIN_GK_PERIOD:
            raise ValueError(f"period must be >= {MIN_GK_PERIOD}, got {self.period}")
        if self.trading_periods < 1:
            raise ValueError(
                f"trading_periods must be >= 1, got {self.trading_periods}"
            )
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
        return self.period

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: GarmanKlassVolatility requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        open_prices = bars.open
        high = bars.high
        low = bars.low
        close = bars.close
        period = self.period
        annualize = self.annualize
        trading_periods = self.trading_periods
        logger.info(
            "GarmanKlassVolatility initiated: period=%d, annualize=%s",
            period,
            annualize,
        )
        o_arr = to_numpy(open_prices)
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(h_arr) != n or (len(l_arr) != n):
            raise ValueError("Arrays cannot be empty and lengths must match")
        ann_factor = np.sqrt(float(trading_periods)) if annualize else 1.0
        vol_vals = self._compute_garman_klass(
            (o_arr, h_arr, l_arr, c_arr), period, ann_factor
        )
        logger.info("GarmanKlassVolatility completed: bars=%d", n)
        return {"value": IndicatorSeries(vol_vals, name=f"GarmanKlass({period})")}

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def _compute_garman_klass(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
        period: int,
        ann_factor: float,
    ) -> np.ndarray[Any, Any]:
        o_arr, h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        valid_o = np.maximum(o_arr, EPSILON)
        valid_l = np.maximum(l_arr, EPSILON)
        valid_h = np.maximum(h_arr, valid_l)
        valid_c = np.maximum(c_arr, EPSILON)
        log_hl = np.log(valid_h / valid_l)
        log_co = np.log(valid_c / valid_o)
        bar_var = (
            GK_HIGH_LOW_FACTOR * log_hl * log_hl - GK_CLOSE_FACTOR * log_co * log_co
        )
        vol = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - period + 1)
            window_len = i - start + 1
            mean_var = float(np.sum(bar_var[start : i + 1])) / window_len
            vol[i] = np.sqrt(max(0.0, mean_var)) * ann_factor
        return vol

    @classmethod
    def is_elevated(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility exceeds threshold."""
        logger.info(
            "Evaluating GarmanKlass is_elevated: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_greater(vol, threshold, shift1=shift, round_digits=8)

    @classmethod
    def is_subdued(cls, vol: IndicatorSeries, threshold: float, shift: int = 0) -> bool:
        """True if volatility is below threshold."""
        logger.info(
            "Evaluating GarmanKlass is_subdued: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return is_lower(vol, threshold, shift1=shift, round_digits=8)

    @classmethod
    def crosses_above(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility crosses above threshold at shift."""
        logger.info(
            "Evaluating GarmanKlass crosses_above: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_above(vol, threshold, shift=shift)

    @classmethod
    def crosses_below(
        cls, vol: IndicatorSeries, threshold: float, shift: int = 0
    ) -> bool:
        """True if volatility crosses below threshold at shift."""
        logger.info(
            "Evaluating GarmanKlass crosses_below: threshold=%.4f, shift=%d",
            threshold,
            shift,
        )
        return crosses_below(vol, threshold, shift=shift)

    @classmethod
    def is_rising(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is rising between shift+1 and shift."""
        logger.info("Evaluating GarmanKlass is_rising at shift=%d", shift)
        return is_rising(vol, shift=shift)

    @classmethod
    def is_falling(cls, vol: IndicatorSeries, shift: int = 0) -> bool:
        """True if volatility is falling between shift+1 and shift."""
        logger.info("Evaluating GarmanKlass is_falling at shift=%d", shift)
        return is_falling(vol, shift=shift)


# Public exports.
__all__ = ["GarmanKlassVolatility"]
