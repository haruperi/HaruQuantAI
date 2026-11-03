"""AggressiveTradeImbalance indicator.

- Calculates order flow aggressive buy/sell trade volume imbalance.
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
MIN_CVD_WINDOW: int = 1
DEFAULT_CVD_WINDOW: int = 14
MIN_ATI_WINDOW: int = 1
DEFAULT_ATI_WINDOW: int = 14
DEFAULT_BUYER_THRESHOLD: float = 0.2
DEFAULT_SELLER_THRESHOLD: float = -0.2
EPSILON: float = 1e-12


class AggressiveTradeImbalance(BaseIndicator):
    """Aggressive Trade Imbalance (ATI) normalized ratio in [-1.0, 1.0]."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volume.aggressive_trade_imbalance",
        version="1.0.0",
        name="AggressiveTradeImbalance",
        description="Calculates order flow aggressive buy/sell trade volume imbalance.",
        category="volume",
        tags=("volume", "aggressive-trade-imbalance"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.SUB,
        inputs=(
            InputPort(
                "open", PortType.SERIES, required=True, description="Open input series"
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
                required=True,
                description="Volume input series",
            ),
            InputPort(
                "buy_volume",
                PortType.SERIES,
                required=False,
                description="Buy volume input series",
            ),
            InputPort(
                "sell_volume",
                PortType.SERIES,
                required=False,
                description="Sell volume input series",
            ),
        ),
        outputs=(
            OutputPort("value", PortType.SERIES, description="Value output series"),
        ),
        required_market_inputs=("open", "close", "volume"),
        required_history_lookback=14,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "window": {"type": "int", "min": 1, "max": 56, "default": 14}
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    window: int = Field(
        default=DEFAULT_ATI_WINDOW,
        ge=MIN_ATI_WINDOW,
        title="Window",
        description="Number of bars in the rolling calculation window",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.window < MIN_ATI_WINDOW:
            raise ValueError(f"window must be >= {MIN_ATI_WINDOW}, got {self.window}")
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
        return self.window

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: AggressiveTradeImbalance requested bars=%d",
            len(bars),
        )
        bars.require_inputs(self.required_inputs())
        if bars.has_input("buy_volume") != bars.has_input("sell_volume"):
            raise ValueError("buy_volume and sell_volume must be supplied together")
        open_prices = bars.open
        close = bars.close
        volume = bars.volume
        buy_volume = bars.input("buy_volume", required=False)
        sell_volume = bars.input("sell_volume", required=False)
        window = self.window
        logger.info("AggressiveTradeImbalance calculation initiated: window=%d", window)
        o_arr = to_numpy(open_prices)
        c_arr = to_numpy(close)
        v_arr = to_numpy(volume)
        n = len(c_arr)
        if n == 0 or len(o_arr) != n or len(v_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        b_vol, s_vol = self._extract_volume_components(
            o_arr, c_arr, v_arr, buy_volume, sell_volume=sell_volume
        )
        ati_vals = self._compute_ati(b_vol, s_vol, window, n)
        logger.info("AggressiveTradeImbalance calculation completed: bars=%d", n)
        return {"value": IndicatorSeries(ati_vals, name=f"ATI({window})")}

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def _extract_volume_components(
        cls,
        o_arr: np.ndarray[Any, Any],
        c_arr: np.ndarray[Any, Any],
        v_arr: np.ndarray[Any, Any],
        buy_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
        *,
        sell_volume: IndicatorSeries | np.ndarray[Any, Any] | None,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Extract separate buyer and seller volume components."""
        n = len(c_arr)
        if buy_volume is not None and sell_volume is not None:
            b_arr = to_numpy(buy_volume)
            s_arr = to_numpy(sell_volume)
            if len(b_arr) != n or len(s_arr) != n:
                raise ValueError("buy_volume and sell_volume lengths must match price")
            return (b_arr, s_arr)
        b_arr = np.where(c_arr >= o_arr, v_arr, 0.0)
        s_arr = np.where(c_arr < o_arr, v_arr, 0.0)
        return (b_arr, s_arr)

    @classmethod
    def _compute_ati(
        cls,
        b_vol: np.ndarray[Any, Any],
        s_vol: np.ndarray[Any, Any],
        window: int,
        n: int,
    ) -> np.ndarray[Any, Any]:
        """Compute rolling imbalance ratio clamped in [-1.0, 1.0]."""
        ati = np.zeros(n, dtype=np.float64)
        for i in range(n):
            start = max(0, i - window + 1)
            sum_b = float(np.sum(b_vol[start : i + 1]))
            sum_s = float(np.sum(s_vol[start : i + 1]))
            total = sum_b + sum_s
            if total > EPSILON:
                ratio = (sum_b - sum_s) / total
                ati[i] = float(np.clip(ratio, -1.0, 1.0))
            else:
                ati[i] = 0.0
        return ati

    @classmethod
    def is_buyer_dominated(
        cls,
        ati: IndicatorSeries,
        threshold: float = DEFAULT_BUYER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if ATI is greater than buyer dominance threshold."""
        logger.info(
            "Evaluating ATI is_buyer_dominated: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        return is_greater(ati, threshold, shift1=shift)

    @classmethod
    def is_seller_dominated(
        cls,
        ati: IndicatorSeries,
        threshold: float = DEFAULT_SELLER_THRESHOLD,
        shift: int = 0,
    ) -> bool:
        """True if ATI is less than seller dominance threshold."""
        logger.info(
            "Evaluating ATI is_seller_dominated: threshold=%.2f, shift=%d",
            threshold,
            shift,
        )
        return is_lower(ati, threshold, shift1=shift)

    @classmethod
    def crosses_above(
        cls, ati: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if ATI crosses above level at shift."""
        logger.info("Evaluating ATI crosses_above level=%.2f at shift=%d", level, shift)
        return crosses_above(ati, level, shift=shift)

    @classmethod
    def crosses_below(
        cls, ati: IndicatorSeries, level: float = 0.0, shift: int = 0
    ) -> bool:
        """True if ATI crosses below level at shift."""
        logger.info("Evaluating ATI crosses_below level=%.2f at shift=%d", level, shift)
        return crosses_below(ati, level, shift=shift)

    @classmethod
    def is_rising(cls, ati: IndicatorSeries, shift: int = 0) -> bool:
        """True if ATI is rising between bar shift+1 and bar shift."""
        logger.info("Evaluating ATI is_rising at shift=%d", shift)
        return is_rising(ati, shift=shift)

    @classmethod
    def is_falling(cls, ati: IndicatorSeries, shift: int = 0) -> bool:
        """True if ATI is falling between bar shift+1 and bar shift."""
        logger.info("Evaluating ATI is_falling at shift=%d", shift)
        return is_falling(ati, shift=shift)


# Public exports.
__all__ = ["AggressiveTradeImbalance"]
