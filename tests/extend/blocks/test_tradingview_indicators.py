"""Comprehensive qualification test suite for TradingView indicators and functions.

Description:
    Validates calculation accuracy, shape preservation, parameter constraints,
    BlockSpec metadata, and non-silent requirement logging across all 48 newly added
    TradingView-compatible indicator blocks and quantitative statistical functions.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative indicator block verification.
    FEAT-FUNCTIONS-BLOCKS: Statistical and mathematical quantitative functions.
Key Capabilities:
    - FR-tradingview-indicators-calculation: Batch numerical calculation and series integrity.
    - FR-tradingview-indicators-validation: Parameter validation and boundary rejection.
    - FR-tradingview-indicators-logging: Non-silent requirement diagnostics under caplog.
    - FR-tradingview-indicators-registry: BlockSpec contract and metadata qualification.
Python API Usage:
    pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

import logging

import numpy as np
import pytest
from app.core.trading.blocks.base import BaseBlock
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.functions.correlation_coefficient import CorrelationCoefficient
from app.extend.blocks.functions.correlation_log import CorrelationLog
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.indicators.momentum.accelerator_oscillator import (
    AcceleratorOscillator,
)
from app.extend.blocks.indicators.momentum.balance_of_power import BalanceOfPower
from app.extend.blocks.indicators.momentum.chande_momentum_oscillator import (
    ChandeMomentumOscillator,
)
from app.extend.blocks.indicators.momentum.connors_rsi import ConnorsRSI
from app.extend.blocks.indicators.momentum.coppock_curve import CoppockCurve
from app.extend.blocks.indicators.momentum.detrended_price_oscillator import (
    DetrendedPriceOscillator,
)
from app.extend.blocks.indicators.momentum.fisher_transform import FisherTransform
from app.extend.blocks.indicators.momentum.know_sure_thing import KnowSureThing
from app.extend.blocks.indicators.momentum.price_oscillator import (
    PercentagePriceOscillator,
)
from app.extend.blocks.indicators.momentum.rank_correlation_index import (
    RankCorrelationIndex,
)
from app.extend.blocks.indicators.momentum.relative_vigor_index import (
    RelativeVigorIndex,
)
from app.extend.blocks.indicators.momentum.smi_ergodic import SMIErgodic
from app.extend.blocks.indicators.momentum.stochastic_rsi import StochasticRSI
from app.extend.blocks.indicators.momentum.trix import TRIX
from app.extend.blocks.indicators.momentum.true_strength_indicator import (
    TrueStrengthIndicator,
)
from app.extend.blocks.indicators.momentum.ultimate_oscillator import UltimateOscillator
from app.extend.blocks.indicators.regime.chop_zone import ChopZone
from app.extend.blocks.indicators.regime.majority_rule import MajorityRule
from app.extend.blocks.indicators.trend.accumulative_swing_index import (
    AccumulativeSwingIndex,
)
from app.extend.blocks.indicators.trend.alma import ArnaudLegouxMovingAverage
from app.extend.blocks.indicators.trend.dema import DoubleEMA
from app.extend.blocks.indicators.trend.envelopes import Envelopes
from app.extend.blocks.indicators.trend.guppy_mma import GuppyMMA
from app.extend.blocks.indicators.trend.mcginley_dynamic import McGinleyDynamic
from app.extend.blocks.indicators.trend.moving_average_channel import (
    MovingAverageChannel,
)
from app.extend.blocks.indicators.trend.moving_average_hamming import (
    MovingAverageHamming,
)
from app.extend.blocks.indicators.trend.trend_strength_index import TrendStrengthIndex
from app.extend.blocks.indicators.trend.williams_alligator import WilliamsAlligator
from app.extend.blocks.indicators.volatility.chaikin_volatility import ChaikinVolatility
from app.extend.blocks.indicators.volatility.chande_kroll_stop import ChandeKrollStop
from app.extend.blocks.indicators.volatility.mass_index import MassIndex
from app.extend.blocks.indicators.volatility.relative_volatility_index import (
    RelativeVolatilityIndex,
)
from app.extend.blocks.indicators.volatility.standard_error import StandardError
from app.extend.blocks.indicators.volatility.standard_error_bands import (
    StandardErrorBands,
)
from app.extend.blocks.indicators.volatility.volatility_index import VolatilityIndex
from app.extend.blocks.indicators.volatility.volatility_zero_trend import (
    VolatilityZeroTrend,
)
from app.extend.blocks.indicators.volume.accumulation_distribution import (
    AccumulationDistribution,
)
from app.extend.blocks.indicators.volume.advance_decline import AdvanceDecline
from app.extend.blocks.indicators.volume.chaikin_oscillator import ChaikinOscillator
from app.extend.blocks.indicators.volume.ease_of_movement import EaseOfMovement
from app.extend.blocks.indicators.volume.force_index import ForceIndex
from app.extend.blocks.indicators.volume.klinger_oscillator import KlingerOscillator
from app.extend.blocks.indicators.volume.net_volume import NetVolume
from app.extend.blocks.indicators.volume.price_volume_trend import PriceVolumeTrend
from app.extend.blocks.indicators.volume.volume_oscillator import VolumeOscillator
from app.extend.blocks.indicators.volume.vwma import VWMA
from pydantic import ValidationError

ALL_INDICATOR_CLASSES: list[type[BaseIndicator]] = [
    # Momentum (16)
    AcceleratorOscillator,
    BalanceOfPower,
    ChandeMomentumOscillator,
    ConnorsRSI,
    CoppockCurve,
    DetrendedPriceOscillator,
    FisherTransform,
    KnowSureThing,
    PercentagePriceOscillator,
    RankCorrelationIndex,
    RelativeVigorIndex,
    SMIErgodic,
    StochasticRSI,
    TRIX,
    TrueStrengthIndicator,
    UltimateOscillator,
    # Trend (10)
    AccumulativeSwingIndex,
    ArnaudLegouxMovingAverage,
    DoubleEMA,
    Envelopes,
    GuppyMMA,
    McGinleyDynamic,
    MovingAverageChannel,
    MovingAverageHamming,
    TrendStrengthIndex,
    WilliamsAlligator,
    # Volume (10)
    AccumulationDistribution,
    AdvanceDecline,
    ChaikinOscillator,
    EaseOfMovement,
    ForceIndex,
    KlingerOscillator,
    NetVolume,
    PriceVolumeTrend,
    VWMA,
    VolumeOscillator,
    # Volatility (8)
    ChaikinVolatility,
    ChandeKrollStop,
    MassIndex,
    RelativeVolatilityIndex,
    StandardError,
    StandardErrorBands,
    VolatilityZeroTrend,
    VolatilityIndex,
    # Regime (2)
    ChopZone,
    MajorityRule,
]

ALL_FUNCTION_CLASSES: list[type[CorrelationCoefficient | CorrelationLog]] = [
    CorrelationCoefficient,
    CorrelationLog,
]


@pytest.fixture
def synthetic_bars() -> BarData:
    """Generate deterministic synthetic BarData fixture for testing."""
    np.random.seed(42)
    n = 150
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.random.uniform(0.5, 2.0, size=n)
    low = close - np.random.uniform(0.5, 2.0, size=n)
    open_ = low + (high - low) * np.random.uniform(0.2, 0.8, size=n)
    volume = np.random.uniform(1000.0, 5000.0, size=n)
    timestamps = np.arange(1700000000, 1700000000 + n * 60, 60, dtype=np.int64)
    return BarData.from_arrays(
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        timestamps=timestamps,
    )


@pytest.mark.parametrize("block_cls", ALL_INDICATOR_CLASSES)
def test_indicator_spec_metadata(block_cls: type[BaseIndicator]) -> None:
    """Verify BlockSpec metadata presence and completeness across all indicators."""
    spec = block_cls.spec
    assert isinstance(spec.id, str)
    assert spec.id.startswith("indicator.")
    assert len(spec.name) > 0
    assert len(spec.description) > 0
    assert spec.category in ("momentum", "trend", "volume", "volatility", "regime")
    assert len(spec.outputs) >= 1
    for out in spec.outputs:
        assert len(out.name) > 0
        assert len(out.description) > 0


@pytest.mark.parametrize("block_cls", ALL_FUNCTION_CLASSES)
def test_function_spec_metadata(
    block_cls: type[CorrelationCoefficient | CorrelationLog],
) -> None:
    """Verify BlockSpec metadata presence and completeness across function blocks."""
    spec = block_cls.spec
    assert isinstance(spec.id, str)
    assert spec.id.startswith("function.")
    assert len(spec.name) > 0
    assert len(spec.description) > 0
    assert spec.category == "functions"
    assert len(spec.outputs) >= 1


@pytest.mark.parametrize("block_cls", ALL_INDICATOR_CLASSES)
def test_indicator_calculation_and_shape(
    block_cls: type[BaseIndicator], synthetic_bars: BarData
) -> None:
    """Verify calculation produces expected outputs and correct shape on BarData."""
    instance = block_cls()
    result: dict[str, IndicatorSeries] = instance.calculate(synthetic_bars)
    expected_outputs = [p.name for p in block_cls.spec.outputs]

    for key in expected_outputs:
        assert key in result, f"{block_cls.__name__} missing output key '{key}'"
        series = result[key]
        assert isinstance(series, IndicatorSeries)
        assert len(series) == len(synthetic_bars)
        values = np.asarray(series.values, dtype=np.float64)
        assert np.any(~np.isnan(values)), (
            f"{block_cls.__name__} has all NaN for '{key}'"
        )


@pytest.mark.parametrize("block_cls", ALL_FUNCTION_CLASSES)
def test_function_calculation_and_shape(
    block_cls: type[CorrelationCoefficient | CorrelationLog], synthetic_bars: BarData
) -> None:
    """Verify quantitative functions compute correct shapes from two source series."""
    instance = block_cls()
    result: dict[str, IndicatorSeries] = instance.calculate(
        synthetic_bars.close, synthetic_bars.open
    )
    assert "value" in result
    series = result["value"]
    assert isinstance(series, IndicatorSeries)
    assert len(series) == len(synthetic_bars)
    values = np.asarray(series.values, dtype=np.float64)
    assert np.any(~np.isnan(values))


def test_correlation_functions_numerical_identity() -> None:
    """Verify Pearson and Log correlation against identical and inverted series."""
    x = np.linspace(10.0, 50.0, 50)
    # Perfect positive correlation with self
    res_pos = CorrelationCoefficient(period=10).calculate(x, x)["value"].values
    valid_pos = res_pos[~np.isnan(res_pos)]
    assert np.allclose(valid_pos, 1.0, atol=1e-5)

    # Perfect negative correlation with inverted series
    res_neg = CorrelationCoefficient(period=10).calculate(x, -x)["value"].values
    valid_neg = res_neg[~np.isnan(res_neg)]
    assert np.allclose(valid_neg, -1.0, atol=1e-5)

    # CorrelationLog identity
    res_log = CorrelationLog(period=10).calculate(x, x)["value"].values
    valid_log = res_log[~np.isnan(res_log)]
    assert np.allclose(valid_log, 1.0, atol=1e-5)


def test_tradingview_indicator_bounds_and_properties(
    synthetic_bars: BarData,
) -> None:
    """Verify specific mathematical properties and bounds for key indicators."""
    # ConnorsRSI in [0, 100]
    crsi = ConnorsRSI().calculate(synthetic_bars)["value"].values
    valid_crsi = crsi[~np.isnan(crsi)]
    assert np.all((valid_crsi >= 0.0) & (valid_crsi <= 100.0))

    # StochasticRSI in [0, 100]
    stoch = StochasticRSI().calculate(synthetic_bars)
    k_vals = stoch["k"].values[~np.isnan(stoch["k"].values)]
    d_vals = stoch["d"].values[~np.isnan(stoch["d"].values)]
    assert np.all((k_vals >= 0.0) & (k_vals <= 100.0))
    assert np.all((d_vals >= 0.0) & (d_vals <= 100.0))

    # ChopZone discrete levels
    cz = ChopZone().calculate(synthetic_bars)
    valid_phase = cz["value"].values[~np.isnan(cz["value"].values)]
    allowed = {-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0}
    assert set(valid_phase).issubset(allowed)

    # Williams Alligator triple lines
    alligator = WilliamsAlligator().calculate(synthetic_bars)
    assert len(alligator["jaw"]) == len(synthetic_bars)
    assert len(alligator["teeth"]) == len(synthetic_bars)
    assert len(alligator["lips"]) == len(synthetic_bars)

    # Chande Kroll Stop long/short stops
    cks = ChandeKrollStop().calculate(synthetic_bars)
    assert len(cks["long_stop"]) == len(synthetic_bars)
    assert len(cks["short_stop"]) == len(synthetic_bars)
    assert np.any(~np.isnan(cks["long_stop"].values))
    assert np.any(~np.isnan(cks["short_stop"].values))


@pytest.mark.parametrize(
    ("cls", "param", "bad_val"),
    [
        (DoubleEMA, "period", 0),
        (ArnaudLegouxMovingAverage, "period", 0),
        (BalanceOfPower, "smooth_period", 0),
        (ConnorsRSI, "rsi_period", 0),
        (ConnorsRSI, "streak_period", 0),
        (ConnorsRSI, "rank_period", 0),
        (FisherTransform, "period", 0),
        (ChaikinOscillator, "fast_period", 0),
        (StandardError, "period", 0),
        (CorrelationCoefficient, "period", 1),  # ge=2
        (CorrelationLog, "period", 1),  # ge=2
    ],
)
def test_parameter_bounds_rejection(
    cls: type[BaseBlock], param: str, bad_val: int
) -> None:
    """Verify that illegal parameter choices raise Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        cls(**{param: bad_val})


def test_non_silent_requirement_logging(
    synthetic_bars: BarData, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify that every category emits non-silent requirement diagnostics."""
    caplog.set_level(logging.DEBUG)

    # 1. Momentum logging
    caplog.clear()
    ConnorsRSI().calculate(synthetic_bars)
    assert any(
        "FR-SERVICES-INDICATOR-MOMENTUM" in rec.message for rec in caplog.records
    )

    # 2. Trend logging
    caplog.clear()
    DoubleEMA().calculate(synthetic_bars)
    assert any("FR-SERVICES-INDICATOR-TREND" in rec.message for rec in caplog.records)

    # 3. Volume logging
    caplog.clear()
    VolumeOscillator().calculate(synthetic_bars)
    assert any("FR-SERVICES-INDICATOR-VOLUME" in rec.message for rec in caplog.records)

    # 4. Volatility logging
    caplog.clear()
    ChandeKrollStop().calculate(synthetic_bars)
    assert any(
        "FR-SERVICES-INDICATOR-VOLATILITY" in rec.message for rec in caplog.records
    )

    # 5. Regime logging
    caplog.clear()
    ChopZone().calculate(synthetic_bars)
    assert any("FR-SERVICES-INDICATOR-REGIME" in rec.message for rec in caplog.records)

    # 6. Function logging
    caplog.clear()
    CorrelationCoefficient().calculate(synthetic_bars.close, synthetic_bars.open)
    assert any(
        "FR-SERVICES-FUNCTION-CORRELATION" in rec.message for rec in caplog.records
    )
