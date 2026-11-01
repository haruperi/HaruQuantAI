"""Bollinger Bands (BB) strategy indicator block."""

from __future__ import annotations

from typing import Any, ClassVar, override

import numpy as np
from pydantic import Field

from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.include.calculators.average import sma_kernel


def _bollinger_bands_kernel(
    data: np.ndarray[Any, np.dtype[np.float64]] | list[float],
    period: int,
    deviation: float = 2.0,
) -> dict[str, np.ndarray[Any, np.dtype[np.float64]]]:
    """Compute Bollinger Bands (upper, middle, lower, bandwidth, range)."""
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)

    upper_arr = np.full(n, np.nan, dtype=np.float64)
    middle_arr = sma_kernel(arr, period)
    lower_arr = np.full(n, np.nan, dtype=np.float64)
    bandwidth_arr = np.full(n, np.nan, dtype=np.float64)
    range_arr = np.full(n, np.nan, dtype=np.float64)

    if period < 1 or n < period:
        return {
            "upper": upper_arr,
            "middle": middle_arr,
            "lower": lower_arr,
            "bandwidth": bandwidth_arr,
            "range": range_arr,
        }

    windows = np.lib.stride_tricks.sliding_window_view(arr, period)
    stds = np.std(windows, axis=-1, ddof=0)
    mids = middle_arr[period - 1 :]
    dev_std = deviation * stds

    upper_arr[period - 1 :] = mids + dev_std
    lower_arr[period - 1 :] = mids - dev_std
    range_arr[period - 1 :] = 2.0 * dev_std

    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(
            upper_arr[period - 1 :] - lower_arr[period - 1 :],
            mids,
            out=bandwidth_arr[period - 1 :],
            where=mids != 0.0,
        )

    return {
        "upper": upper_arr,
        "middle": middle_arr,
        "lower": lower_arr,
        "bandwidth": bandwidth_arr,
        "range": range_arr,
    }


class BollingerBands(BaseIndicator):
    """Bollinger Bands volatility indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.volatility.bollinger_bands",
        version="1.0.0",
        name="Bollinger Bands",
        description=(
            "Calculates volatility envelopes around a moving average "
            "using standard deviation"
        ),
        category="volatility",
        tags=("volatility", "bands", "bollinger"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(InputPort("close", PortType.SERIES, "Close price series"),),
        outputs=(
            OutputPort("upper", PortType.SERIES, "Upper Bollinger Band"),
            OutputPort("middle", PortType.SERIES, "Middle Bollinger Band (SMA)"),
            OutputPort("lower", PortType.SERIES, "Lower Bollinger Band"),
            OutputPort("bandwidth", PortType.SERIES, "Normalized Bollinger BandWidth"),
            OutputPort("range", PortType.SERIES, "Bollinger Band Range"),
        ),
        required_market_inputs=("close",),
        is_generation_eligible=True,
        parameter_search_space={
            "period": {"type": "int", "min": 2, "max": 100, "default": 20},
            "deviation": {"type": "float", "min": 0.5, "max": 5.0, "default": 2.0},
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    period: int = Field(
        default=20,
        ge=1,
        title="Period",
        description="Rolling window lookback period in bars",
    )
    deviation: float = Field(
        default=2.0,
        gt=0.0,
        title="Deviation",
        description="Standard deviation multiplier for bands",
    )

    @override
    def required_history(self) -> int:
        """Return minimum history bars needed for the first valid BB calculation."""
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute Bollinger Bands over closing prices in batch.

        Args:
            bars: Shared calculation context containing OHLCV price series.

        Returns:
            Dictionary with upper, middle, lower, bandwidth, and range series.
        """
        bands = _bollinger_bands_kernel(bars.close, self.period, self.deviation)
        return {
            "upper": IndicatorSeries(bands["upper"], name="BB.Upper"),
            "middle": IndicatorSeries(bands["middle"], name="BB.Middle"),
            "lower": IndicatorSeries(bands["lower"], name="BB.Lower"),
            "bandwidth": IndicatorSeries(bands["bandwidth"], name="BB.BandWidth"),
            "range": IndicatorSeries(bands["range"], name="BB.Range"),
        }


__all__ = ["BollingerBands"]
