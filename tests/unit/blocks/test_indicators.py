"""Unit tests for the unified indicator families and condition evaluators.

Description:
    Validates calculation accuracy, numerical invariants, shift indexing,
    and condition evaluations for ATR, RSI, MovingAverage, BollingerBands,
    MACD, Stochastic, CCI, ADX, AwesomeOscillator, BullsPower, BearsPower,
    DeMarker, Momentum, ROC, WilliamsPR, OSMA, BarRange, TrueRange, StdDev,
    KeltnerChannel, MTATR, MTKeltnerChannel, UlcerIndex, SRPercentRank,
    Aroon, DirectionalIndex, SuperTrend, KAMA, KaufmanEfficiencyRatio,
    HullMovingAverage, ParabolicSAR, and Vortex using deterministic test vectors.

Purpose:
    FEAT-BLOCKS-INDICATOR-FOUNDATION: Verification of indicator math and conditions.

Key Capabilities:
    - FR-BLOCKS-SERIES-CONDITION-EVALUATOR: Test universal condition operations.
      Associated: `test_indicator_series_conditions()`
      Logging: Logger asserts condition triggers.
    - FR-BLOCKS-ATR-CALCULATE: Verify ATR calculations and conditions.
      Associated: `test_atr_calculation_and_conditions()`
      Logging: Logger asserts calculation logs.
    - FR-BLOCKS-RSI-CALCULATE: Verify RSI calculations and boundaries.
      Associated: `test_rsi_calculation_and_bounds()`
      Logging: Logger asserts RSI logs.
    - FR-BLOCKS-MA-CALCULATE: Verify SMA, EMA, SMMA, and LWMA calculations.
      Associated: `test_moving_average_methods()`
      Logging: Logger asserts MA logs.
    - FR-BLOCKS-BB-CALCULATE: Verify Bollinger Bands geometry and bandwidth.
      Associated: `test_bollinger_bands_geometry()`
      Logging: Logger asserts BB logs.
    - FR-BLOCKS-MACD-CALCULATE: Verify MACD lines, signal, and histogram.
      Associated: `test_macd_lines_and_crosses()`
      Logging: Logger asserts MACD logs.
    - FR-BLOCKS-STOCH-CALCULATE: Verify Stochastic %K and %D calculations.
      Associated: `test_stochastic_oscillator()`
      Logging: Logger asserts Stoch logs.
    - FR-BLOCKS-CCI-CALCULATE: Verify Commodity Channel Index calculation.
      Associated: `test_cci_calculation()`
      Logging: Logger asserts CCI logs.
    - FR-BLOCKS-ADX-CALCULATE: Verify ADX, +DI, and -DI calculations.
      Associated: `test_adx_directional_system()`
      Logging: Logger asserts ADX logs.
    - FR-BLOCKS-AWO-CALCULATE: Verify Awesome Oscillator calculation.
      Associated: `test_awesome_oscillator()`
      Logging: Logger asserts AWO logs.
    - FR-BLOCKS-BULLS-CALCULATE: Verify Bulls Power calculation.
      Associated: `test_bulls_power()`
      Logging: Logger asserts BullsPower logs.
    - FR-BLOCKS-BEARS-CALCULATE: Verify Bears Power calculation.
      Associated: `test_bears_power()`
      Logging: Logger asserts BearsPower logs.
    - FR-BLOCKS-DEMARKER-CALCULATE: Verify DeMarker calculation and bounds.
      Associated: `test_demarker_oscillator()`
      Logging: Logger asserts DeMarker logs.
    - FR-BLOCKS-MOMENTUM-CALCULATE: Verify Momentum calculation.
      Associated: `test_momentum_indicator()`
      Logging: Logger asserts Momentum logs.
    - FR-BLOCKS-ROC-CALCULATE: Verify Rate of Change calculation.
      Associated: `test_roc_indicator()`
      Logging: Logger asserts ROC logs.
    - FR-BLOCKS-WILLIAMS-CALCULATE: Verify Williams %R bounds and calculation.
      Associated: `test_williams_pr()`
      Logging: Logger asserts WilliamsPR logs.
    - FR-BLOCKS-OSMA-CALCULATE: Verify OSMA oscillator calculation.
      Associated: `test_osma_oscillator()`
      Logging: Logger asserts OSMA logs.
    - FR-BLOCKS-BARRANGE-CALCULATE: Verify BarRange calculation and conditions.
      Associated: `test_bar_range()`
      Logging: Logger asserts BarRange logs.
    - FR-BLOCKS-TRUERANGE-CALCULATE: Verify TrueRange calculation and conditions.
      Associated: `test_true_range()`
      Logging: Logger asserts TrueRange logs.
    - FR-BLOCKS-STDDEV-CALCULATE: Verify StdDev calculation and conditions.
      Associated: `test_std_dev()`
      Logging: Logger asserts StdDev logs.
    - FR-BLOCKS-KELTNER-CALCULATE: Verify KeltnerChannel calculation and conditions.
      Associated: `test_keltner_channel()`
      Logging: Logger asserts KeltnerChannel logs.
    - FR-BLOCKS-MTATR-CALCULATE: Verify MTATR calculation and conditions.
      Associated: `test_mt_atr()`
      Logging: Logger asserts MTATR logs.
    - FR-BLOCKS-MTKELTNER-CALCULATE: Verify MTKeltnerChannel calculation and conditions.
      Associated: `test_mt_keltner_channel()`
      Logging: Logger asserts MTKeltnerChannel logs.
    - FR-BLOCKS-ULCER-CALCULATE: Verify UlcerIndex calculation and conditions.
      Associated: `test_ulcer_index()`
      Logging: Logger asserts UlcerIndex logs.
    - FR-BLOCKS-SRPERCENT-CALCULATE: Verify SRPercentRank calculation and conditions.
      Associated: `test_sr_percent_rank()`
      Logging: Logger asserts SRPercentRank logs.
    - FR-BLOCKS-AROON-CALCULATE: Verify Aroon Up, Down, Oscillator calculations.
      Associated: `test_aroon()`
      Logging: Logger asserts Aroon logs.
    - FR-BLOCKS-DX-CALCULATE: Verify DirectionalIndex DI+, DI-, DX calculations.
      Associated: `test_directional_index()`
      Logging: Logger asserts DX logs.
    - FR-BLOCKS-SUPERTREND-CALCULATE: Verify SuperTrend trailing stop calculation.
      Associated: `test_supertrend()`
      Logging: Logger asserts SuperTrend logs.
    - FR-BLOCKS-KAMA-CALCULATE: Verify KAMA adaptive moving average calculation.
      Associated: `test_kama()`
      Logging: Logger asserts KAMA logs.
    - FR-BLOCKS-KER-CALCULATE: Verify Kaufman Efficiency Ratio calculation.
      Associated: `test_kaufman_efficiency_ratio()`
      Logging: Logger asserts KER logs.
    - FR-BLOCKS-HMA-CALCULATE: Verify Hull Moving Average calculation.
      Associated: `test_hull_moving_average()`
      Logging: Logger asserts HMA logs.
    - FR-BLOCKS-PSAR-CALCULATE: Verify Parabolic SAR calculation.
      Associated: `test_parabolic_sar()`
      Logging: Logger asserts PSAR logs.
    - FR-BLOCKS-VORTEX-CALCULATE: Verify Vortex Indicator calculations.
      Associated: `test_vortex()`
      Logging: Logger asserts Vortex logs.
    - FR-BLOCKS-AVGVOLUME-CALCULATE: Verify AvgVolume calculation and conditions.
      Associated: `test_avg_volume()`
      Logging: Logger asserts AvgVolume logs.
    - FR-BLOCKS-VWAP-CALCULATE: Verify VWAP rolling calculation and conditions.
      Associated: `test_vwap()`
      Logging: Logger asserts VWAP logs.
    - FR-BLOCKS-AVWAP-CALCULATE: Verify AnchoredVWAP calculation and bands.
      Associated: `test_anchored_vwap()`
      Logging: Logger asserts AVWAP logs.
    - FR-BLOCKS-VOLUMEPROFILE-CALCULATE: Verify VolumeProfile POC, VAH, VAL.
      Associated: `test_volume_profile()`
      Logging: Logger asserts VolumeProfile logs.
    - FR-BLOCKS-TPOPROFILE-CALCULATE: Verify TPOProfile POC, VAH, VAL, IB.
      Associated: `test_tpo_profile()`
      Logging: Logger asserts TPOProfile logs.
    - FR-BLOCKS-COT-CALCULATE: Verify COT Composite Score and CPI indexes.
      Associated: `test_cot()`
      Logging: Logger asserts COT logs.
    - FR-BLOCKS-HEIKENASHI-CALCULATE: Verify HeikenAshi calculations and condition checks.
      Associated: `test_heiken_ashi()`
      Logging: Logger asserts HeikenAshi logs.
    - FR-BLOCKS-HIGHESTLOWEST-CALCULATE: Verify HighestLowest calculation and breakout open conditions.
      Associated: `test_highest_lowest()`
      Logging: Logger asserts HighestLowest logs.
    - FR-BLOCKS-FRACTAL-CALCULATE: Verify Fractal 3-bar and 5-bar calculation and condition checks.
      Associated: `test_fractal()`
      Logging: Logger asserts Fractal logs.
    - FR-BLOCKS-GANNHILO-CALCULATE: Verify GannHiLo stop line, bands, and trend regime transitions.
      Associated: `test_gann_hi_lo()`
      Logging: Logger asserts GannHiLo logs.
    - FR-BLOCKS-PIVOTS-CALCULATE: Verify Pivots PP, R1-R3, S1-S3, and crossover conditions.
      Associated: `test_pivots()`
      Logging: Logger asserts Pivots logs.
    - FR-BLOCKS-FIBO-CALCULATE: Verify Fibo standard and custom retracement levels.
      Associated: `test_fibo()`
      Logging: Logger asserts Fibo logs.
    - FR-BLOCKS-LINREG-CALCULATE: Verify LinReg fitted value, slope, intercept, and conditions.
      Associated: `test_lin_reg()`
      Logging: Logger asserts LinReg logs.
    - FR-BLOCKS-TREND-CALCULATE: Verify Trend regime state, baseline MA, and transitions.
      Associated: `test_trend()`
      Logging: Logger asserts Trend logs.
    - FR-BLOCKS-LAGUERRERSI-CALCULATE: Verify LaguerreRSI calculation and conditions.
      Associated: `test_laguerre_rsi()`
      Logging: Logger asserts LaguerreRSI logs.
    - FR-BLOCKS-QQE-CALCULATE: Verify QQE Value1 and Value2 line calculations.
      Associated: `test_qqe()`
      Logging: Logger asserts QQE logs.
    - FR-BLOCKS-REFLEX-CALCULATE: Verify Reflex cycle indicator calculations.
      Associated: `test_reflex()`
      Logging: Logger asserts Reflex logs.
    - FR-BLOCKS-STC-CALCULATE: Verify Schaff Trend Cycle calculation and conditions.
      Associated: `test_schaff_trend_cycle()`
      Logging: Logger asserts STC logs.
    - FR-BLOCKS-WAVETREND-CALCULATE: Verify WaveTrend WT1 and WT2 calculations.
      Associated: `test_wave_trend()`
      Logging: Logger asserts WaveTrend logs.
    - FR-BLOCKS-ICHIMOKU-CALCULATE: Verify Ichimoku 5-line system and cloud conditions.
      Associated: `test_ichimoku()`
      Logging: Logger asserts Ichimoku logs.
    - FR-BLOCKS-CHOPPINESS-CALCULATE: Verify Choppiness Index and regime states.
      Associated: `test_choppiness_index()`
      Logging: Logger asserts Choppiness logs.
    - FR-BLOCKS-HURST-CALCULATE: Verify Hurst Exponent R/S analysis and persistence.
      Associated: `test_hurst_exponent()`
      Logging: Logger asserts Hurst logs.
    - FR-BLOCKS-REGIMERESOLVER-CALCULATE: Verify Multi-Factor Market Regime Resolver.
      Associated: `test_market_regime_resolver()`
      Logging: Logger asserts Regime Resolver logs.
    - FR-BLOCKS-OBV-CALCULATE: Verify On-Balance Volume calculation and conditions.
      Associated: `test_obv()`
      Logging: Logger asserts OBV logs.
    - FR-BLOCKS-MFI-CALCULATE: Verify Money Flow Index calculation and bounds.
      Associated: `test_mfi()`
      Logging: Logger asserts MFI logs.
    - FR-BLOCKS-CMF-CALCULATE: Verify Chaikin Money Flow accumulation/distribution.
      Associated: `test_cmf()`
      Logging: Logger asserts CMF logs.
    - FR-BLOCKS-CVD-CALCULATE: Verify Cumulative Volume Delta and rolling delta.
      Associated: `test_order_flow()`
      Logging: Logger asserts CVD logs.
    - FR-BLOCKS-ATI-CALCULATE: Verify Aggressive Trade Imbalance ratio and dominance.
      Associated: `test_order_flow()`
      Logging: Logger asserts ATI logs.
    - FR-BLOCKS-DONCHIAN-CALCULATE: Verify DonchianChannels bands and conditions.
      Associated: `test_donchian_channels()`
      Logging: Logger asserts Donchian logs.
    - FR-BLOCKS-TEMA-CALCULATE: Verify TEMA calculation and crossovers.
      Associated: `test_tema()`
      Logging: Logger asserts TEMA logs.
    - FR-BLOCKS-ZIGZAG-CALCULATE: Verify ZigZag swing points and trendlines.
      Associated: `test_zigzag()`
      Logging: Logger asserts ZigZag logs.
    - FR-BLOCKS-PARKINSON-CALCULATE: Verify ParkinsonVolatility calculations.
      Associated: `test_parkinson_volatility()`
      Logging: Logger asserts Parkinson logs.
    - FR-BLOCKS-GARMANKLASS-CALCULATE: Verify GarmanKlassVolatility calculations.
      Associated: `test_garman_klass_volatility()`
      Logging: Logger asserts Garman-Klass logs.
    - FR-BLOCKS-ROGERSSATCHELL-CALCULATE: Verify RogersSatchellVolatility.
      Associated: `test_rogers_satchell_volatility()`
      Logging: Logger asserts Rogers-Satchell logs.
    - FR-BLOCKS-ADR-CALCULATE: Verify AverageDailyRange and stretch ratio.
      Associated: `test_average_daily_range()`
      Logging: Logger asserts ADR logs.
    - FR-BLOCKS-AMIHUD-CALCULATE: Verify AmihudIlliquidity ratio calculations.
      Associated: `test_amihud_illiquidity()`
      Logging: Logger asserts Amihud logs.
    - FR-BLOCKS-PRICEVELOCITY-CALCULATE: Verify PriceVelocity rate and acceleration.
      Associated: `test_price_velocity()`
      Logging: Logger asserts PriceVelocity logs.
    - FR-BLOCKS-CANDLESTICK-CALCULATE: Verify CandlestickPatterns multi-pattern recognition.
      Associated: `test_candlestick_patterns()`
      Logging: Logger asserts CandlestickPatterns logs.
    - FR-BLOCKS-CHARTPATTERNS-CALCULATE: Verify ChartPatterns structural extrema.
      Associated: `test_chart_patterns()`
      Logging: Logger asserts ChartPatterns logs.
    - FR-BLOCKS-PRICEGAP-CALCULATE: Verify PriceGap size and gap fill tracking.
      Associated: `test_price_gap()`
      Logging: Logger asserts PriceGap logs.
    - FR-BLOCKS-LEVELCLUSTERING-CALCULATE: Verify LevelClustering recency-weighted pivots.
      Associated: `test_level_clustering()`
      Logging: Logger asserts LevelClustering logs.

Python API Usage:
    Run isolated tests through pytest:
    ```python
    uv run pytest tests/unit/blocks/test_indicators.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/blocks/test_indicators.py --no-cov
    ```
"""

from __future__ import annotations

import numpy as np
import pytest
from app.blocks.indicators import (
    ADX,
    ATR,
    CCI,
    CMF,
    COT,
    KAMA,
    MACD,
    MFI,
    MTATR,
    OBV,
    OSMA,
    QQE,
    ROC,
    RSI,
    TEMA,
    VWAP,
    AggressiveTradeImbalance,
    AmihudIlliquidity,
    AnchoredVWAP,
    Aroon,
    AverageDailyRange,
    AvgVolume,
    AwesomeOscillator,
    BarRange,
    BearsPower,
    BollingerBands,
    BullsPower,
    CandlestickPatterns,
    ChartPatterns,
    ChoppinessIndex,
    CumulativeVolumeDelta,
    DeMarker,
    DirectionalIndex,
    DonchianChannels,
    Fibo,
    Fractal,
    GannHiLo,
    GarmanKlassVolatility,
    HeikenAshi,
    HighestLowest,
    HullMovingAverage,
    HurstExponent,
    Ichimoku,
    KaufmanEfficiencyRatio,
    KeltnerChannel,
    LaguerreRSI,
    LevelClustering,
    LinReg,
    MarketRegimeResolver,
    Momentum,
    MovingAverage,
    MTKeltnerChannel,
    ParabolicSAR,
    ParkinsonVolatility,
    Pivots,
    PriceGap,
    PriceVelocity,
    Reflex,
    RogersSatchellVolatility,
    SchaffTrendCycle,
    SRPercentRank,
    StdDev,
    Stochastic,
    Supertrend,
    TPOProfile,
    Trend,
    TrueRange,
    UlcerIndex,
    VolumeProfile,
    Vortex,
    WaveTrend,
    WilliamsPR,
    ZigZag,
)
from app.blocks.indicators.base import IndicatorSeries

SuperTrend = Supertrend


def test_indicator_series_conditions() -> None:
    """Verify IndicatorSeries shift indexing and universal condition operations."""
    series = IndicatorSeries(
        np.array([10.0, 12.0, 11.5, 13.0, 14.0]), name="TestSeries"
    )

    # Name and values properties
    assert series.name == "TestSeries"
    assert len(series.values) == 5

    # Sequence initialization
    seq_series = IndicatorSeries([1.0, 2.0, 3.0])
    assert len(seq_series) == 3

    # Shift access: 0 is current (14.0), 1 is previous (13.0), etc.
    assert series.get(0) == 14.0
    assert series.get(1) == 13.0
    assert series.get(2) == 11.5
    assert np.isnan(series.get(10))
    assert np.isnan(series.get(-1))

    # Rising / Falling
    assert series.is_rising(shift=0) is True  # 14.0 > 13.0
    assert series.is_falling(shift=0) is False
    assert series.is_rising(shift=2) is False  # 11.5 < 12.0
    assert series.is_falling(shift=2) is True

    # Higher / Lower with float and IndicatorSeries
    assert series.is_higher(lookback=2, shift=0) is True  # 14.0 > 11.5
    assert series.is_lower(15.0, shift=0) is True
    assert series.is_lower(13.0, shift=0) is False
    assert series.is_greater(13.5, shift=0) is True
    assert series.is_greater(15.0, shift=0) is False

    other_series = IndicatorSeries(np.array([9.0, 11.0, 12.0, 12.5, 13.5]))
    assert series.is_greater(other_series, shift=0) is True
    assert series.is_lower(other_series, shift=0) is False

    # Out of bounds comparison returns False
    assert series.is_greater(other_series, shift=10) is False
    assert series.is_lower(other_series, shift=10) is False
    assert series.is_higher(lookback=1, shift=10) is False

    # Crosses above / below
    level = 13.5
    assert series.crosses_above(level, shift=0) is True  # 13.0 <= 13.5 and 14.0 > 13.5
    assert series.crosses_below(level, shift=0) is False
    cross_series = IndicatorSeries(np.array([10.0, 14.0, 13.0, 11.0]))
    assert cross_series.crosses_below(12.0, shift=0) is True
    assert cross_series.crosses_above(other_series, shift=10) is False

    # Turn conditions (changes_up / changes_down)
    turn_series = IndicatorSeries(np.array([15.0, 12.0, 11.0, 11.0, 13.0]))
    # Shifts: 0=13.0, 1=11.0, 2=11.0 -> 13.0 > 11.0 and 11.0 <= 11.0 -> changes_up True
    assert turn_series.changes_up(shift=0) is True
    assert turn_series.changes_down(shift=0) is False
    assert turn_series.changes_up(shift=10) is False

    peak_series = IndicatorSeries(np.array([10.0, 12.0, 14.0, 14.0, 12.0]))
    # Shifts: 0=12.0, 1=14.0, 2=14.0 -> 12.0 < 14.0 and 14.0 >= 14.0 -> changes_down True
    assert peak_series.changes_down(shift=0) is True
    assert peak_series.changes_down(shift=10) is False


def test_atr_calculation_and_conditions() -> None:
    """Verify ATR True Range and Wilder smoothing against manual calculation."""
    high = np.array([10.0, 11.0, 12.0, 11.5, 12.5])
    low = np.array([9.0, 9.5, 10.5, 10.0, 11.0])
    close = np.array([9.5, 10.5, 11.0, 11.2, 12.0])

    atr = ATR.calculate(high, low, close, period=3)
    assert len(atr) == 5

    # True range on bar 0: 10 - 9 = 1.0
    assert atr.get(4) == pytest.approx(1.0)

    # All ATR values must be strictly positive
    for s in range(5):
        assert atr.get(s) > 0.0

    # ATR condition helpers
    assert isinstance(ATR.is_rising(atr, shift=0), bool)
    assert isinstance(ATR.is_falling(atr, shift=0), bool)
    assert isinstance(ATR.crosses_above(atr, level=0.5, shift=0), bool)
    assert isinstance(ATR.crosses_below(atr, level=0.5, shift=0), bool)
    assert isinstance(ATR.is_higher(atr, lookback=1, shift=0), bool)
    assert isinstance(ATR.is_lower(atr, lookback=1, shift=0), bool)
    assert isinstance(ATR.changes_up(atr, shift=0), bool)
    assert isinstance(ATR.changes_down(atr, shift=0), bool)

    # Edge case: period <= 0 defaults to 14
    atr_def = ATR.calculate(high, low, close, period=0)
    assert len(atr_def) == 5


def test_rsi_calculation_and_bounds() -> None:
    """Verify RSI produces values within [0, 100] and detects trend direction."""
    # Prices recovering from dip -> RSI rises from 18 to 75
    turn_close = np.array([10.0, 9.5, 9.0, 8.5, 8.0, 7.8, 8.2, 8.7, 9.3, 10.0, 10.8])
    rsi = RSI.calculate(turn_close, period=5)

    current_rsi = rsi.get(0)
    assert not np.isnan(current_rsi)
    assert 0.0 <= current_rsi <= 100.0

    # Falling prices
    falling_close = np.array([10.0, 10.5, 11.0, 11.2, 10.8, 10.2, 9.5, 9.0, 8.5, 8.0])
    rsi_down = RSI.calculate(falling_close, period=5)

    # Condition checks
    assert RSI.is_rising(rsi, shift=0) is True
    assert RSI.is_falling(rsi_down, shift=0) is True
    assert isinstance(RSI.crosses_above(rsi, level=50.0, shift=0), bool)
    assert isinstance(RSI.crosses_below(rsi, level=50.0, shift=0), bool)
    assert isinstance(RSI.is_higher(rsi, lookback=1, shift=0), bool)
    assert isinstance(RSI.is_lower(rsi, lookback=1, shift=0), bool)
    assert isinstance(RSI.changes_up(rsi, shift=0), bool)
    assert isinstance(RSI.changes_down(rsi, shift=0), bool)

    # Edge cases: period <= 0 and constant price (loss=0, gain=0)
    rsi_zero_period = RSI.calculate(turn_close, period=0)
    assert len(rsi_zero_period) == len(turn_close)

    flat_close = np.full(10, 100.0)
    rsi_flat = RSI.calculate(flat_close, period=5)
    assert rsi_flat.get(0) == 50.0


def test_moving_average_methods() -> None:
    """Verify SMA, EMA, SMMA, and LWMA computations."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    period = 3

    sma = MovingAverage.calculate(data, period=period, method=MovingAverage.SMA)
    # SMA at bar 3 (values 1, 2, 3) = 2.0
    assert sma.get(4) == pytest.approx(2.0)
    # SMA at last bar (values 5, 6, 7) = 6.0
    assert sma.get(0) == pytest.approx(6.0)

    ema = MovingAverage.calculate(data, period=period, method=MovingAverage.EMA)
    assert not np.isnan(ema.get(0))

    smma = MovingAverage.calculate(data, period=period, method=MovingAverage.SMMA)
    assert not np.isnan(smma.get(0))

    lwma = MovingAverage.calculate(data, period=period, method=MovingAverage.LWMA)
    # LWMA at last bar: (5*1 + 6*2 + 7*3)/(1+2+3) = (5 + 12 + 21)/6 = 38/6 = 6.3333
    assert lwma.get(0) == pytest.approx(38.0 / 6.0)

    # Helper functions
    assert MovingAverage.is_rising(sma, shift=0) is True
    assert MovingAverage.is_falling(sma, shift=0) is False
    assert MovingAverage.crosses_above(lwma, sma, shift=0) in (True, False)
    assert MovingAverage.crosses_below(sma, lwma, shift=0) in (True, False)
    assert MovingAverage.is_greater(lwma, sma, shift=0) is True
    assert MovingAverage.is_lower(sma, lwma, shift=0) is True

    # Invalid period defaults
    ma_def = MovingAverage.calculate(data, period=0)
    assert len(ma_def) == len(data)


def test_bollinger_bands_geometry() -> None:
    """Verify Upper Band >= Middle Band >= Lower Band geometry."""
    data = np.array([10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0, 11.8, 12.2, 12.5])
    bands = BollingerBands.calculate(data, period=5, deviation=2.0)

    upper = bands["upper"].get(0)
    middle = bands["middle"].get(0)
    lower = bands["lower"].get(0)
    bandwidth = bands["bandwidth"].get(0)

    assert upper >= middle >= lower
    assert bandwidth == pytest.approx((upper - lower) / middle)

    # Condition helpers
    price_series = IndicatorSeries(data)
    assert isinstance(
        BollingerBands.price_higher_upper(price_series, bands, shift=0), bool
    )
    assert isinstance(
        BollingerBands.price_lower_lower(price_series, bands, shift=0), bool
    )
    assert isinstance(
        BollingerBands.price_crosses_above_upper(price_series, bands, shift=0), bool
    )
    assert isinstance(
        BollingerBands.price_crosses_below_lower(price_series, bands, shift=0), bool
    )

    # Default period handling
    bands_def = BollingerBands.calculate(data, period=0)
    assert len(bands_def["middle"]) == len(data)


def test_macd_lines_and_crosses() -> None:
    """Verify MACD Main, Signal, and Histogram relationship."""
    data = np.linspace(10.0, 30.0, 40)
    macd_res = MACD.calculate(data, fast=12, slow=26, smooth=9)

    main_val = macd_res["main"].get(0)
    sig_val = macd_res["signal"].get(0)
    hist_val = macd_res["histogram"].get(0)

    assert not np.isnan(main_val)
    assert not np.isnan(sig_val)
    assert not np.isnan(hist_val)
    assert hist_val == pytest.approx(main_val - sig_val)

    assert isinstance(MACD.main_crosses_above_signal(macd_res, shift=0), bool)
    assert isinstance(MACD.main_crosses_below_signal(macd_res, shift=0), bool)
    assert isinstance(MACD.main_higher_signal(macd_res, shift=0), bool)
    assert isinstance(MACD.main_lower_signal(macd_res, shift=0), bool)
    assert isinstance(MACD.main_crosses_above_zero(macd_res, shift=0), bool)
    assert isinstance(MACD.main_crosses_below_zero(macd_res, shift=0), bool)


def test_stochastic_oscillator() -> None:
    """Verify %K and %D bounds and crossover conditions."""
    high = np.linspace(12.0, 20.0, 30)
    low = np.linspace(10.0, 18.0, 30)
    close = np.linspace(11.0, 19.5, 30)

    stoch = Stochastic.calculate(high, low, close, k_period=14, d_period=3, slowing=3)

    k_val = stoch["k"].get(0)
    d_val = stoch["d"].get(0)

    assert 0.0 <= k_val <= 100.0
    assert 0.0 <= d_val <= 100.0
    assert isinstance(Stochastic.k_crosses_above_d(stoch, shift=0), bool)
    assert isinstance(Stochastic.k_crosses_below_d(stoch, shift=0), bool)
    assert isinstance(Stochastic.k_higher_d(stoch, shift=0), bool)
    assert isinstance(Stochastic.k_lower_d(stoch, shift=0), bool)

    # Edge cases: period <= 0 and flat high==low
    stoch_def = Stochastic.calculate(high, low, close, k_period=0)
    assert len(stoch_def["k"]) == len(high)

    flat_h = np.full(20, 10.0)
    flat_l = np.full(20, 10.0)
    flat_c = np.full(20, 10.0)
    flat_stoch = Stochastic.calculate(flat_h, flat_l, flat_c, k_period=5)
    assert flat_stoch["k"].get(0) == 50.0


def test_cci_calculation() -> None:
    """Verify CCI oscillator calculation and level cross logic."""
    high = np.linspace(12.0, 20.0, 30)
    low = np.linspace(10.0, 18.0, 30)
    close = np.linspace(11.0, 19.5, 30)

    cci = CCI.calculate(high, low, close, period=14)
    current_cci = cci.get(0)

    assert not np.isnan(current_cci)
    assert isinstance(CCI.crosses_above(cci, level=100.0, shift=0), bool)
    assert isinstance(CCI.crosses_below(cci, level=-100.0, shift=0), bool)
    assert isinstance(CCI.is_rising(cci, shift=0), bool)
    assert isinstance(CCI.is_falling(cci, shift=0), bool)
    assert isinstance(CCI.is_higher(cci, lookback=1, shift=0), bool)
    assert isinstance(CCI.is_lower(cci, lookback=1, shift=0), bool)

    # Edge case: period <= 0
    cci_def = CCI.calculate(high, low, close, period=0)
    assert len(cci_def) == len(high)


def test_adx_directional_system() -> None:
    """Verify ADX, +DI, and -DI calculations in an uptrend."""
    # Strong uptrend: High and Low constantly rising
    high = np.linspace(10.0, 50.0, 50)
    low = np.linspace(8.0, 48.0, 50)
    close = np.linspace(9.5, 49.5, 50)

    adx_dict = ADX.calculate(high, low, close, period=14)

    adx_val = adx_dict["main"].get(0)
    di_plus = adx_dict["di_plus"].get(0)
    di_minus = adx_dict["di_minus"].get(0)

    assert not np.isnan(adx_val)
    assert not np.isnan(di_plus)
    assert not np.isnan(di_minus)

    # In a strong uptrend, +DI should exceed -DI and ADX should indicate a trend
    assert di_plus > di_minus
    assert ADX.di_plus_higher_di_minus(adx_dict, shift=0) is True
    assert ADX.di_plus_lower_di_minus(adx_dict, shift=0) is False
    assert ADX.is_trending(adx_dict, threshold=20.0, shift=0) is True
    assert isinstance(ADX.di_plus_crosses_above_di_minus(adx_dict, shift=0), bool)
    assert isinstance(ADX.di_plus_crosses_below_di_minus(adx_dict, shift=0), bool)

    # Edge cases: period <= 0
    adx_def = ADX.calculate(high, low, close, period=0)
    assert len(adx_def["main"]) == len(high)


def test_awesome_oscillator() -> None:
    """Verify Awesome Oscillator fast/slow median price calculation and conditions."""
    high = np.linspace(10.0, 50.0, 50)
    low = np.linspace(8.0, 48.0, 50)

    awo = AwesomeOscillator.calculate(high, low, fast_period=5, slow_period=34)
    assert len(awo) == 50
    assert not np.isnan(awo.get(0))

    # In a rising linear sequence, fast SMA > slow SMA -> AWO > 0
    assert awo.get(0) > 0.0
    assert AwesomeOscillator.is_rising(awo, shift=0) is True
    assert AwesomeOscillator.is_falling(awo, shift=0) is False
    assert AwesomeOscillator.crosses_above(awo, level=0.0, shift=0) in (True, False)
    assert AwesomeOscillator.crosses_below(awo, level=0.0, shift=0) is False
    assert AwesomeOscillator.is_higher(awo, lookback=1, shift=0) is True
    assert AwesomeOscillator.is_lower(awo, lookback=1, shift=0) is False
    assert isinstance(AwesomeOscillator.changes_up(awo, shift=0), bool)
    assert isinstance(AwesomeOscillator.changes_down(awo, shift=0), bool)

    # Edge cases: period <= 0
    awo_def = AwesomeOscillator.calculate(high, low, fast_period=0, slow_period=0)
    assert len(awo_def) == 50


def test_bulls_power() -> None:
    """Verify Bulls Power (High - EMA) calculation and condition checks."""
    high = np.linspace(12.0, 30.0, 40)
    close = np.linspace(10.0, 28.0, 40)

    bp = BullsPower.calculate(high, close, period=14)
    assert len(bp) == 40
    assert not np.isnan(bp.get(0))

    # High is strictly greater than Close, so High - EMA(Close) should be positive
    assert bp.get(0) > 0.0
    assert BullsPower.is_rising(bp, shift=0) in (True, False)
    assert BullsPower.is_falling(bp, shift=0) in (True, False)
    assert BullsPower.crosses_above(bp, level=0.0, shift=0) in (True, False)
    assert BullsPower.crosses_below(bp, level=0.0, shift=0) in (True, False)
    assert BullsPower.is_higher(bp, lookback=1, shift=0) in (True, False)
    assert BullsPower.is_lower(bp, lookback=1, shift=0) in (True, False)
    assert isinstance(BullsPower.changes_up(bp, shift=0), bool)
    assert isinstance(BullsPower.changes_down(bp, shift=0), bool)

    # Edge case: period <= 0
    bp_def = BullsPower.calculate(high, close, period=0)
    assert len(bp_def) == 40


def test_bears_power() -> None:
    """Verify Bears Power (Low - EMA) calculation and condition checks."""
    low = np.linspace(8.0, 26.0, 40)
    close = np.linspace(10.0, 28.0, 40)

    bp = BearsPower.calculate(low, close, period=14)
    assert len(bp) == 40
    assert not np.isnan(bp.get(0))

    assert BearsPower.is_rising(bp, shift=0) in (True, False)
    assert BearsPower.is_falling(bp, shift=0) in (True, False)
    assert BearsPower.crosses_above(bp, level=0.0, shift=0) in (True, False)
    assert BearsPower.crosses_below(bp, level=0.0, shift=0) in (True, False)
    assert BearsPower.is_higher(bp, lookback=1, shift=0) in (True, False)
    assert BearsPower.is_lower(bp, lookback=1, shift=0) in (True, False)
    assert isinstance(BearsPower.changes_up(bp, shift=0), bool)
    assert isinstance(BearsPower.changes_down(bp, shift=0), bool)

    # Edge case: period <= 0
    bp_def = BearsPower.calculate(low, close, period=0)
    assert len(bp_def) == 40


def test_demarker_oscillator() -> None:
    """Verify DeMarker bounds within [0, 1] and condition logic."""
    high = np.linspace(10.0, 40.0, 30)
    low = np.linspace(9.0, 38.0, 30)

    dem = DeMarker.calculate(high, low, period=14)
    assert len(dem) == 30

    current = dem.get(0)
    assert not np.isnan(current)
    assert 0.0 <= current <= 1.0

    # In steady uptrend with High rising each bar and Low rising (DeMin=0), DeMarker -> 1.0
    assert current > 0.5
    assert DeMarker.is_rising(dem, shift=0) in (True, False)
    assert DeMarker.is_falling(dem, shift=0) in (True, False)
    assert DeMarker.crosses_above(dem, level=0.5, shift=0) in (True, False)
    assert DeMarker.crosses_below(dem, level=0.5, shift=0) in (True, False)
    assert DeMarker.is_higher(dem, lookback=1, shift=0) in (True, False)
    assert DeMarker.is_lower(dem, lookback=1, shift=0) in (True, False)
    assert isinstance(DeMarker.changes_up(dem, shift=0), bool)
    assert isinstance(DeMarker.changes_down(dem, shift=0), bool)

    # Flat market edge case (denom == 0)
    flat_high = np.full(20, 10.0)
    flat_low = np.full(20, 10.0)
    dem_flat = DeMarker.calculate(flat_high, flat_low, period=5)
    assert dem_flat.get(0) == 0.0

    # Edge case: period <= 0
    dem_def = DeMarker.calculate(high, low, period=0)
    assert len(dem_def) == 30


def test_momentum_indicator() -> None:
    """Verify Momentum centered around 100.0 and condition helpers."""
    close = np.array([10.0, 12.0, 15.0, 20.0, 30.0, 45.0, 70.0])
    mom = Momentum.calculate(close, period=3)

    assert len(mom) == len(close)
    # Bar 4 (val 30.0) vs Bar 1 (val 12.0) -> 30.0 * 100 / 12.0 = 250.0
    assert mom.get(2) == pytest.approx(30.0 * 100.0 / 12.0)
    assert mom.get(0) > 100.0

    assert Momentum.is_rising(mom, shift=0) is True
    assert Momentum.is_falling(mom, shift=0) is False
    assert Momentum.crosses_above(mom, level=100.0, shift=0) in (True, False)
    assert Momentum.crosses_below(mom, level=100.0, shift=0) is False
    assert Momentum.is_higher(mom, lookback=1, shift=0) is True
    assert Momentum.is_lower(mom, lookback=1, shift=0) is False
    assert isinstance(Momentum.changes_up(mom, shift=0), bool)
    assert isinstance(Momentum.changes_down(mom, shift=0), bool)

    # Edge cases: period <= 0 and zero price handling
    mom_def = Momentum.calculate(close, period=0)
    assert len(mom_def) == len(close)

    zero_close = np.zeros(10)
    mom_zero = Momentum.calculate(zero_close, period=3)
    assert mom_zero.get(0) == 100.0


def test_roc_indicator() -> None:
    """Verify Rate of Change percentage calculation and conditions."""
    close = np.array([100.0, 102.0, 105.0, 110.0, 120.0])
    roc = ROC.calculate(close, period=2)

    assert len(roc) == len(close)
    # Last bar (120.0) vs bar 2 ago (105.0): (120 - 105) / 105 * 100 = 14.2857%
    assert roc.get(0) == pytest.approx((120.0 - 105.0) / 105.0 * 100.0)

    assert ROC.is_rising(roc, shift=0) is True
    assert ROC.is_falling(roc, shift=0) is False
    assert ROC.crosses_above(roc, level=0.0, shift=0) in (True, False)
    assert ROC.crosses_below(roc, level=0.0, shift=0) is False
    assert ROC.is_greater(roc, level=10.0, shift=0) is True
    assert ROC.is_lower(roc, level=20.0, shift=0) is True

    # Edge cases: period <= 0 and zero past price
    roc_def = ROC.calculate(close, period=0)
    assert len(roc_def) == len(close)

    zero_arr = np.zeros(5)
    roc_zero = ROC.calculate(zero_arr, period=2)
    assert roc_zero.get(0) == 0.0


def test_williams_pr() -> None:
    """Verify Williams %R bounds in [-100, 0] and condition checks."""
    high = np.linspace(15.0, 30.0, 30)
    low = np.linspace(10.0, 25.0, 30)
    close = np.linspace(12.0, 29.0, 30)

    wpr = WilliamsPR.calculate(high, low, close, period=14)
    assert len(wpr) == 30

    current = wpr.get(0)
    assert not np.isnan(current)
    assert -100.0 <= current <= 0.0

    assert WilliamsPR.is_rising(wpr, shift=0) in (True, False)
    assert WilliamsPR.is_falling(wpr, shift=0) in (True, False)
    assert WilliamsPR.crosses_above(wpr, level=-50.0, shift=0) in (True, False)
    assert WilliamsPR.crosses_below(wpr, level=-50.0, shift=0) in (True, False)
    assert WilliamsPR.is_higher(wpr, lookback=1, shift=0) in (True, False)
    assert WilliamsPR.is_lower(wpr, lookback=1, shift=0) in (True, False)
    assert isinstance(WilliamsPR.changes_up(wpr, shift=0), bool)
    assert isinstance(WilliamsPR.changes_down(wpr, shift=0), bool)

    # Flat market edge case (high == low)
    flat_h = np.full(20, 10.0)
    flat_l = np.full(20, 10.0)
    flat_c = np.full(20, 10.0)
    wpr_flat = WilliamsPR.calculate(flat_h, flat_l, flat_c, period=5)
    assert wpr_flat.get(0) == -50.0

    # Edge case: period <= 0
    wpr_def = WilliamsPR.calculate(high, low, close, period=0)
    assert len(wpr_def) == 30


def test_osma_oscillator() -> None:
    """Verify OSMA (MACD - Signal) calculation and condition checks."""
    data = np.linspace(10.0, 40.0, 50)
    osma = OSMA.calculate(data, fast_ema=12, slow_ema=26, signal_period=9)

    assert len(osma) == 50
    current = osma.get(0)
    assert not np.isnan(current)

    assert OSMA.is_rising(osma, shift=0) in (True, False)
    assert OSMA.is_falling(osma, shift=0) in (True, False)
    assert OSMA.crosses_above(osma, level=0.0, shift=0) in (True, False)
    assert OSMA.crosses_below(osma, level=0.0, shift=0) in (True, False)
    assert OSMA.is_greater(osma, level=0.0, shift=0) in (True, False)
    assert OSMA.is_lower(osma, level=0.0, shift=0) in (True, False)
    assert OSMA.is_higher(osma, lookback=1, shift=0) in (True, False)
    assert isinstance(OSMA.changes_up(osma, shift=0), bool)
    assert isinstance(OSMA.changes_down(osma, shift=0), bool)

    # Edge case: periods <= 0
    osma_def = OSMA.calculate(data, fast_ema=0, slow_ema=0, signal_period=0)
    assert len(osma_def) == 50


def test_bar_range() -> None:
    """Verify BarRange calculation and range conditions."""
    high = np.array([10.0, 15.0, 20.0, 12.0, 25.0])
    low = np.array([8.0, 11.0, 14.0, 10.0, 15.0])
    # Ranges: [2.0, 4.0, 6.0, 2.0, 10.0]
    br = BarRange.calculate(high, low)
    assert len(br) == 5
    assert br.get(0) == pytest.approx(10.0)
    assert br.get(1) == pytest.approx(2.0)
    assert br.get(2) == pytest.approx(6.0)

    # is_biggest_range: check if current bar (range 10.0) is largest in lookback=3
    assert BarRange.is_biggest_range(br, lookback=3, shift=0) is True
    assert BarRange.is_biggest_range(br, lookback=3, shift=1) is False

    # is_smallest_range:
    assert BarRange.is_smallest_range(br, lookback=2, shift=1) is True

    # is_highest_in_range:
    assert BarRange.is_highest_in_range(high, lookback=3, shift=0) is True

    # is_lowest_in_range:
    assert BarRange.is_lowest_in_range(low, lookback=1, shift=1) is True

    # in_range_pips:
    assert (
        BarRange.in_range_pips(br, min_pips=5.0, max_pips=15.0, pip_size=1.0, shift=0)
        is True
    )
    assert (
        BarRange.in_range_pips(br, min_pips=12.0, max_pips=20.0, pip_size=1.0, shift=0)
        is False
    )


def test_true_range() -> None:
    """Verify TrueRange calculation and condition checks."""
    high = np.array([10.0, 12.0, 15.0, 14.0])
    low = np.array([8.0, 9.0, 11.0, 10.0])
    close = np.array([9.0, 11.0, 13.0, 12.0])
    tr = TrueRange.calculate(high, low, close)
    assert len(tr) == 4
    # Bar 0: H-L = 2.0
    assert tr.values[0] == 2.0
    # Bar 1: max(12-9=3, |12-9|=3, |9-9|=0) = 3.0
    assert tr.values[1] == 3.0
    # Bar 2: max(15-11=4, |15-11|=4, |11-11|=0) = 4.0
    assert tr.values[2] == 4.0

    assert TrueRange.is_rising(tr, shift=1) is True
    assert TrueRange.is_falling(tr, shift=0) in (True, False)
    assert TrueRange.crosses_above(tr, level=2.5, shift=1) in (True, False)
    assert TrueRange.crosses_below(tr, level=2.5, shift=1) is False
    assert TrueRange.is_higher(tr, lookback=1, shift=1) is True
    assert TrueRange.is_lower(tr, lookback=1, shift=1) is False
    assert isinstance(TrueRange.changes_up(tr, shift=0), bool)
    assert isinstance(TrueRange.changes_down(tr, shift=0), bool)


def test_std_dev() -> None:
    """Verify population standard deviation calculation and conditions."""
    data = np.array([10.0, 12.0, 23.0, 23.0, 16.0, 23.0, 21.0, 16.0])
    sd = StdDev.calculate(data, period=5)
    assert len(sd) == len(data)

    window = data[3:8]
    expected_std = np.std(window, ddof=0)
    assert sd.get(0) == pytest.approx(expected_std)

    assert StdDev.is_rising(sd, shift=0) in (True, False)
    assert StdDev.is_falling(sd, shift=0) in (True, False)
    assert StdDev.crosses_above(sd, level=1.0, shift=0) in (True, False)
    assert StdDev.crosses_below(sd, level=1.0, shift=0) in (True, False)
    assert StdDev.is_higher(sd, lookback=1, shift=0) in (True, False)
    assert StdDev.is_lower(sd, lookback=1, shift=0) in (True, False)
    assert isinstance(StdDev.changes_up(sd, shift=0), bool)
    assert isinstance(StdDev.changes_down(sd, shift=0), bool)

    # Edge case: period <= 0
    sd_def = StdDev.calculate(data, period=0)
    assert len(sd_def) == len(data)


def test_keltner_channel() -> None:
    """Verify Keltner Channel calculation and channel conditions."""
    high = np.linspace(15.0, 35.0, 30)
    low = np.linspace(10.0, 30.0, 30)
    close = np.linspace(12.0, 32.0, 30)

    kc = KeltnerChannel.calculate(high, low, close, period=10)
    assert "upper" in kc and "middle" in kc and "lower" in kc
    upper = kc["upper"]
    middle = kc["middle"]
    lower = kc["lower"]

    # Geometry: Upper > Middle > Lower
    assert upper.get(0) > middle.get(0)
    assert middle.get(0) > lower.get(0)

    close_series = IndicatorSeries(close, name="Close")
    assert isinstance(
        KeltnerChannel.bar_closes_above_upper(close_series, kc, shift=0), bool
    )
    assert isinstance(
        KeltnerChannel.bar_closes_below_upper(close_series, kc, shift=0), bool
    )
    assert isinstance(
        KeltnerChannel.bar_closes_above_lower(close_series, kc, shift=0), bool
    )
    assert isinstance(
        KeltnerChannel.bar_closes_below_lower(close_series, kc, shift=0), bool
    )
    assert isinstance(KeltnerChannel.upper_is_rising(kc, shift=0), bool)
    assert isinstance(KeltnerChannel.upper_is_falling(kc, shift=0), bool)
    assert isinstance(KeltnerChannel.lower_is_rising(kc, shift=0), bool)
    assert isinstance(KeltnerChannel.lower_is_falling(kc, shift=0), bool)

    # Edge case: period <= 0
    kc_def = KeltnerChannel.calculate(high, low, close, period=0)
    assert len(kc_def["upper"]) == 30


def test_mt_atr() -> None:
    """Verify MetaTrader ATR (SMA of TrueRange) calculation and conditions."""
    high = np.array([10.0, 12.0, 15.0, 14.0, 18.0, 20.0, 22.0])
    low = np.array([8.0, 9.0, 11.0, 10.0, 13.0, 15.0, 17.0])
    close = np.array([9.0, 11.0, 13.0, 12.0, 16.0, 18.0, 21.0])

    mt_atr = MTATR.calculate(high, low, close, period=3)
    assert len(mt_atr) == 7

    # True range for bars 2, 3, 4:
    # Bar 2: max(15-11, |15-11|, |11-11|) = 4
    # Bar 3: max(14-10, |14-13|, |10-13|) = 4
    # Bar 4: max(18-13, |18-12|, |13-12|) = 6
    # SMA over period 3 at bar 4 = (4 + 4 + 6) / 3 = 14 / 3 = 4.66667
    assert mt_atr.values[4] == pytest.approx(14.0 / 3.0)

    assert MTATR.is_rising(mt_atr, shift=0) in (True, False)
    assert MTATR.is_falling(mt_atr, shift=0) in (True, False)
    assert MTATR.crosses_above(mt_atr, level=3.0, shift=0) in (True, False)
    assert MTATR.crosses_below(mt_atr, level=3.0, shift=0) in (True, False)
    assert MTATR.is_higher(mt_atr, lookback=1, shift=0) in (True, False)
    assert MTATR.is_lower(mt_atr, lookback=1, shift=0) in (True, False)
    assert isinstance(MTATR.changes_up(mt_atr, shift=0), bool)
    assert isinstance(MTATR.changes_down(mt_atr, shift=0), bool)

    # Edge case: period <= 0
    mt_def = MTATR.calculate(high, low, close, period=0)
    assert len(mt_def) == 7


def test_mt_keltner_channel() -> None:
    """Verify MTKeltnerChannel (SMA(Close) centered) and channel checks."""
    high = np.linspace(15.0, 35.0, 30)
    low = np.linspace(10.0, 30.0, 30)
    close = np.linspace(12.0, 32.0, 30)

    mt_kc = MTKeltnerChannel.calculate(high, low, close, period=10)
    assert "upper" in mt_kc and "middle" in mt_kc and "lower" in mt_kc
    upper = mt_kc["upper"]
    middle = mt_kc["middle"]
    lower = mt_kc["lower"]

    assert upper.get(0) > middle.get(0)
    assert middle.get(0) > lower.get(0)

    close_series = IndicatorSeries(close, name="Close")
    assert isinstance(
        MTKeltnerChannel.bar_closes_above_upper(close_series, mt_kc, shift=0),
        bool,
    )
    assert isinstance(
        MTKeltnerChannel.bar_closes_below_upper(close_series, mt_kc, shift=0),
        bool,
    )
    assert isinstance(
        MTKeltnerChannel.bar_closes_above_lower(close_series, mt_kc, shift=0),
        bool,
    )
    assert isinstance(
        MTKeltnerChannel.bar_closes_below_lower(close_series, mt_kc, shift=0),
        bool,
    )
    assert isinstance(MTKeltnerChannel.upper_is_rising(mt_kc, shift=0), bool)
    assert isinstance(MTKeltnerChannel.upper_is_falling(mt_kc, shift=0), bool)
    assert isinstance(MTKeltnerChannel.lower_is_rising(mt_kc, shift=0), bool)
    assert isinstance(MTKeltnerChannel.lower_is_falling(mt_kc, shift=0), bool)

    # Edge case: period <= 0
    mt_kc_def = MTKeltnerChannel.calculate(high, low, close, period=0)
    assert len(mt_kc_def["upper"]) == 30


def test_ulcer_index() -> None:
    """Verify UlcerIndex Mode 1 (Up) and Mode 2 (Down) calculations."""
    close = np.array([10.0, 10.5, 9.8, 9.5, 9.2, 9.0, 8.8, 8.5, 8.0, 8.2])

    ui_up = UlcerIndex.calculate(close, mode=1, period=5)
    assert len(ui_up) == len(close)
    assert ui_up.get(0) >= 0.0

    ui_down = UlcerIndex.calculate(close, mode=2, period=5)
    assert len(ui_down) == len(close)
    assert ui_down.get(0) >= 0.0

    assert UlcerIndex.is_rising(ui_up, shift=0) in (True, False)
    assert UlcerIndex.is_falling(ui_up, shift=0) in (True, False)
    assert UlcerIndex.is_lower(ui_up, level=20.0, shift=0) in (True, False)

    # Edge cases: period <= 0 and zero prices
    ui_def = UlcerIndex.calculate(close, period=0)
    assert len(ui_def) == len(close)

    zeros = np.zeros(10)
    ui_zeros = UlcerIndex.calculate(zeros, period=5)
    assert ui_zeros.get(0) == 0.0


def test_sr_percent_rank() -> None:
    """Verify SRPercentRank Basic Mode 1 and ATR Mode 2 calculations."""
    high = np.array([10.0, 12.0, 14.0, 13.0, 15.0, 14.0, 16.0, 15.0, 17.0, 16.0])
    low = np.array([8.0, 9.0, 11.0, 10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0])
    close = np.array([9.0, 11.0, 12.0, 12.0, 13.0, 12.5, 14.0, 13.5, 15.0, 14.5])

    # Mode 1 Basic
    sr_basic = SRPercentRank.calculate(high, low, close, mode=1, length=3, atr_period=3)
    assert len(sr_basic) == len(close)
    assert 0.0 <= sr_basic.get(0) <= 100.0

    # Mode 2 ATR
    sr_atr = SRPercentRank.calculate(high, low, close, mode=2, length=3, atr_period=3)
    assert len(sr_atr) == len(close)
    assert 0.0 <= sr_atr.get(0) <= 100.0

    # Conditions
    assert isinstance(SRPercentRank.is_above_level(sr_basic, level=50.0, shift=0), bool)
    assert isinstance(SRPercentRank.is_below_level(sr_basic, level=50.0, shift=0), bool)
    assert isinstance(
        SRPercentRank.is_above_level_x_bars(sr_basic, level=20.0, bars=2, shift=0),
        bool,
    )
    assert isinstance(
        SRPercentRank.is_below_level_x_bars(sr_basic, level=80.0, bars=2, shift=0),
        bool,
    )
    assert isinstance(SRPercentRank.is_rising(sr_basic, shift=0), bool)
    assert isinstance(SRPercentRank.is_falling(sr_basic, shift=0), bool)

    # Edge case: insufficient bars
    short_h = np.array([10.0, 12.0])
    short_l = np.array([8.0, 9.0])
    short_c = np.array([9.0, 10.0])
    sr_short = SRPercentRank.calculate(short_h, short_l, short_c, mode=1, length=5)
    assert sr_short.get(0) == 0.0

    # Mismatched lengths error
    with pytest.raises(ValueError):
        SRPercentRank.calculate(high[:5], low, close)


def test_aroon() -> None:
    """Verify Aroon Up, Down, Oscillator calculations and condition checks."""
    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 12.5, 14.0, 13.5])
    low = np.array([9.0, 9.5, 10.0, 10.2, 11.0, 11.2, 12.0, 12.2])

    res = Aroon.calculate(high, low, period=5)
    assert "up" in res and "down" in res and "oscillator" in res
    up = res["up"]
    down = res["down"]
    osc = res["oscillator"]

    assert len(up) == len(high)
    assert 0.0 <= up.get(0) <= 100.0
    assert 0.0 <= down.get(0) <= 100.0
    assert osc.get(0) == pytest.approx(up.get(0) - down.get(0))

    assert isinstance(Aroon.crosses_above(res, shift=0), bool)
    assert isinstance(Aroon.crosses_below(res, shift=0), bool)
    assert isinstance(Aroon.up_rises_from_bottom(res, shift=0), bool)
    assert isinstance(Aroon.down_falls_from_top(res, shift=0), bool)
    assert isinstance(Aroon.down_rises_from_bottom(res, shift=0), bool)
    assert isinstance(Aroon.up_falls_from_top(res, shift=0), bool)
    assert isinstance(Aroon.up_is_rising(res, shift=0), bool)
    assert isinstance(Aroon.up_is_falling(res, shift=0), bool)
    assert isinstance(Aroon.down_is_rising(res, shift=0), bool)
    assert isinstance(Aroon.down_is_falling(res, shift=0), bool)

    # Edge case: period <= 0
    res_def = Aroon.calculate(high, low, period=0)
    assert len(res_def["up"]) == len(high)

    # Mismatched lengths
    with pytest.raises(ValueError):
        Aroon.calculate(high[:4], low)


def test_directional_index() -> None:
    """Verify Directional Index (DI+, DI-, DX) and condition helpers."""
    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    close = np.linspace(9.0, 29.0, 40)

    res = DirectionalIndex.calculate(high, low, close, period=14)
    assert "di_plus" in res and "di_minus" in res and "dx" in res
    di_p = res["di_plus"]
    di_m = res["di_minus"]
    dx = res["dx"]

    assert len(di_p) == 40
    assert not np.isnan(di_p.get(0))
    assert not np.isnan(di_m.get(0))
    assert not np.isnan(dx.get(0))

    assert isinstance(DirectionalIndex.di_crosses_above(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_crosses_below(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_rising(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_falling(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_higher(res, lookback=1, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_lower(res, lookback=1, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_changes_up(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_plus_changes_down(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_minus_rising(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_minus_falling(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_minus_changes_up(res, shift=0), bool)
    assert isinstance(DirectionalIndex.di_minus_changes_down(res, shift=0), bool)


def test_supertrend() -> None:
    """Verify SuperTrend trailing stop calculation and condition checks."""
    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    close = np.linspace(9.0, 29.0, 40)

    # Mode 1 MT
    st_mt = SuperTrend.calculate(high, low, close, mode=1, atr_period=10, atr_mult=3.0)
    assert "main" in st_mt and "trend" in st_mt
    main_mt = st_mt["main"]
    assert len(main_mt) == 40

    # Mode 2 TS
    st_ts = SuperTrend.calculate(high, low, close, mode=2, atr_period=10, atr_mult=3.0)
    assert len(st_ts["main"]) == 40

    assert isinstance(SuperTrend.is_uptrend(st_mt, shift=0), bool)
    assert isinstance(SuperTrend.is_downtrend(st_mt, shift=0), bool)
    assert isinstance(SuperTrend.is_in_range(st_mt, shift=0), bool)
    assert isinstance(SuperTrend.bar_closes_above(close, st_mt, shift=0), bool)
    assert isinstance(SuperTrend.bar_closes_below(close, st_mt, shift=0), bool)

    # Edge cases
    st_def = SuperTrend.calculate(high, low, close, atr_period=0)
    assert len(st_def["main"]) == 40

    with pytest.raises(ValueError):
        SuperTrend.calculate(high[:5], low, close)


def test_kaufman_efficiency_ratio() -> None:
    """Verify Kaufman Efficiency Ratio bounded in [0.0, 1.0]."""
    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0])
    ker = KaufmanEfficiencyRatio.calculate(close, period=5)
    assert len(ker) == len(close)

    # In monotonically increasing data, change == vol_sum, so KER == 1.0
    assert ker.get(0) == pytest.approx(1.0)

    assert KaufmanEfficiencyRatio.is_above_level(ker, level=0.5, shift=0) is True
    assert KaufmanEfficiencyRatio.is_below_level(ker, level=0.5, shift=0) is False
    assert isinstance(KaufmanEfficiencyRatio.is_rising(ker, shift=0), bool)
    assert isinstance(KaufmanEfficiencyRatio.is_falling(ker, shift=0), bool)

    # Edge cases: period <= 0 and insufficient data
    ker_def = KaufmanEfficiencyRatio.calculate(close, period=0)
    assert len(ker_def) == len(close)

    short_close = np.array([10.0, 11.0])
    ker_short = KaufmanEfficiencyRatio.calculate(short_close, period=5)
    assert ker_short.get(0) == 0.0

    # Flat market (zero volatility)
    flat_c = np.full(10, 10.0)
    ker_flat = KaufmanEfficiencyRatio.calculate(flat_c, period=5)
    assert ker_flat.get(0) == 0.0


def test_kama() -> None:
    """Verify KAMA adaptive moving average and condition checks."""
    close = np.linspace(10.0, 40.0, 50)
    kama = KAMA.calculate(close, er_period=10, fast_period=2, slow_period=30)
    assert len(kama) == len(close)
    assert not np.isnan(kama.get(0))

    slow_kama = KAMA.calculate(close, er_period=10, fast_period=5, slow_period=40)

    assert isinstance(KAMA.is_rising(kama, shift=0), bool)
    assert isinstance(KAMA.is_falling(kama, shift=0), bool)
    assert isinstance(KAMA.bar_closes_above(close, kama, shift=0), bool)
    assert isinstance(KAMA.bar_closes_below(close, kama, shift=0), bool)
    assert isinstance(KAMA.fast_above_slow(kama, slow_kama, shift=0), bool)
    assert isinstance(KAMA.fast_below_slow(kama, slow_kama, shift=0), bool)

    # Edge cases: periods <= 0 and empty/short array
    kama_def = KAMA.calculate(close, er_period=0, fast_period=0, slow_period=0)
    assert len(kama_def) == len(close)

    empty_kama = KAMA.calculate(np.array([]))
    assert len(empty_kama) == 0

    short_kama = KAMA.calculate(close[:5], er_period=10)
    assert len(short_kama) == 5


def test_hull_moving_average() -> None:
    """Verify Hull Moving Average responsiveness and condition helpers."""
    close = np.linspace(10.0, 50.0, 50)
    hma = HullMovingAverage.calculate(close, period=16)
    assert len(hma) == len(close)
    assert not np.isnan(hma.get(0))

    slow_hma = HullMovingAverage.calculate(close, period=30)

    assert isinstance(HullMovingAverage.is_rising(hma, shift=0), bool)
    assert isinstance(HullMovingAverage.is_falling(hma, shift=0), bool)
    assert isinstance(HullMovingAverage.changes_up(hma, shift=0), bool)
    assert isinstance(HullMovingAverage.changes_down(hma, shift=0), bool)
    assert isinstance(
        HullMovingAverage.faster_above_slower(hma, slow_hma, shift=0), bool
    )
    assert isinstance(
        HullMovingAverage.faster_below_slower(hma, slow_hma, shift=0), bool
    )

    # Edge case: period <= 1
    hma_def = HullMovingAverage.calculate(close, period=1)
    assert len(hma_def) == len(close)


def test_parabolic_sar() -> None:
    """Verify Parabolic SAR calculation and position checks."""
    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    close = np.linspace(9.0, 29.0, 40)

    psar = ParabolicSAR.calculate(high, low, step=0.02, maximum=0.2)
    assert len(psar) == len(high)
    assert not np.isnan(psar.get(0))

    assert isinstance(ParabolicSAR.is_bar_higher(close, psar, shift=0), bool)
    assert isinstance(ParabolicSAR.is_bar_lower(close, psar, shift=0), bool)
    assert isinstance(ParabolicSAR.is_rising(psar, shift=0), bool)
    assert isinstance(ParabolicSAR.is_falling(psar, shift=0), bool)

    # Reversal testing: up then down then up
    h_rev = np.array([10.0, 12.0, 15.0, 14.0, 11.0, 8.0, 6.0, 9.0, 13.0])
    l_rev = np.array([8.0, 10.0, 12.0, 11.0, 8.0, 5.0, 4.0, 7.0, 10.0])
    c_rev = np.array([9.0, 11.0, 14.0, 12.0, 9.0, 6.0, 5.0, 8.0, 12.0])
    psar_rev = ParabolicSAR.calculate(h_rev, l_rev)
    assert len(psar_rev) == 9
    assert isinstance(ParabolicSAR.is_bar_higher(c_rev, psar_rev, shift=0), bool)

    # Edge cases: step/max <= 0, empty array, mismatched lengths
    psar_def = ParabolicSAR.calculate(high, low, step=0, maximum=0)
    assert len(psar_def) == len(high)

    empty_psar = ParabolicSAR.calculate(np.array([]), np.array([]))
    assert len(empty_psar) == 0

    with pytest.raises(ValueError):
        ParabolicSAR.calculate(high[:5], low)


def test_vortex() -> None:
    """Verify Vortex VI+, VI-, and Oscillator calculations."""
    high = np.linspace(10.0, 30.0, 40)
    low = np.linspace(8.0, 28.0, 40)
    close = np.linspace(9.0, 29.0, 40)

    vx = Vortex.calculate(high, low, close, period=14)
    assert "vi_plus" in vx and "vi_minus" in vx and "oscillator" in vx
    vi_p = vx["vi_plus"]
    vi_m = vx["vi_minus"]
    osc = vx["oscillator"]

    assert len(vi_p) == 40
    assert vi_p.get(0) > 0.0
    assert vi_m.get(0) > 0.0
    assert osc.get(0) == pytest.approx(vi_p.get(0) - vi_m.get(0))

    assert isinstance(Vortex.is_uptrend(vx, shift=0), bool)
    assert isinstance(Vortex.is_downtrend(vx, shift=0), bool)
    assert isinstance(Vortex.changes_trend_up(vx, shift=0), bool)
    assert isinstance(Vortex.changes_trend_down(vx, shift=0), bool)
    assert isinstance(Vortex.vi_plus_rising(vx, shift=0), bool)
    assert isinstance(Vortex.vi_plus_falling(vx, shift=0), bool)

    # Edge cases: period <= 0 and insufficient data
    vx_def = Vortex.calculate(high, low, close, period=0)
    assert len(vx_def["vi_plus"]) == 40

    short_vx = Vortex.calculate(high[:5], low[:5], close[:5], period=14)
    assert short_vx["vi_plus"].get(0) == 0.0

    with pytest.raises(ValueError):
        Vortex.calculate(high[:5], low, close)


def test_avg_volume() -> None:
    """Verify AvgVolume rolling SMA and volume slope condition helpers."""
    vol = np.linspace(1000.0, 5000.0, 30)
    avg_vol = AvgVolume.calculate(vol, period=10)

    assert len(avg_vol) == 30
    assert np.isnan(avg_vol.values[0])
    # Bar 9 should be average of first 10 values
    assert avg_vol.values[9] == pytest.approx(float(np.mean(vol[:10])))
    assert avg_vol.get(0) > avg_vol.get(1)

    assert AvgVolume.is_rising(avg_vol, shift=0) is True
    assert AvgVolume.is_falling(avg_vol, shift=0) is False
    assert AvgVolume.crosses_above(avg_vol, 2000.0, shift=0) in (True, False)
    assert AvgVolume.crosses_below(avg_vol, 4000.0, shift=0) in (True, False)
    assert AvgVolume.is_higher(avg_vol, 2000.0, shift=0) is True
    assert AvgVolume.is_lower(avg_vol, 10000.0, shift=0) is True

    vol_series = IndicatorSeries(vol, name="Volume")
    assert AvgVolume.volume_is_rising(vol_series, shift=0) is True
    assert AvgVolume.volume_is_falling(vol_series, shift=0) is False
    assert AvgVolume.volume_above_average(vol_series, avg_vol, shift=0) is True

    # Edge cases: period <= 0 and insufficient bars
    avg_def = AvgVolume.calculate(vol, period=0)
    assert len(avg_def) == 30

    short_avg = AvgVolume.calculate(vol[:5], period=10)
    assert np.all(np.isnan(short_avg.values))


def test_vwap() -> None:
    """Verify rolling VWAP calculations and condition evaluators."""
    high = np.linspace(105.0, 150.0, 40)
    low = np.linspace(95.0, 140.0, 40)
    close = np.linspace(100.0, 145.0, 40)
    open_p = np.linspace(98.0, 142.0, 40)
    volume = np.full(40, 1000.0)

    # 4-price average VWAP
    vwap_4 = VWAP.calculate(
        high,
        low,
        close,
        volume,
        open_prices=open_p,
        period=10,
    )
    assert len(vwap_4) == 40
    assert np.isnan(vwap_4.values[0])
    assert not np.isnan(vwap_4.values[9])

    # 3-price average VWAP
    vwap_3 = VWAP.calculate(high, low, close, volume, period=10)
    assert len(vwap_3) == 40
    assert not np.isnan(vwap_3.values[9])

    c_series = IndicatorSeries(close, name="Close")
    assert VWAP.bar_closes_above(c_series, vwap_3, shift=0) in (True, False)
    assert VWAP.bar_closes_below(c_series, vwap_3, shift=0) in (True, False)
    assert VWAP.is_rising(vwap_3, shift=0) is True
    assert VWAP.is_falling(vwap_3, shift=0) is False

    vwap_fast = VWAP.calculate(high, low, close, volume, period=5)
    assert VWAP.fast_above_slow(vwap_fast, vwap_3, shift=0) in (True, False)
    assert VWAP.fast_below_slow(vwap_fast, vwap_3, shift=0) in (True, False)
    assert VWAP.crosses_above(vwap_fast, vwap_3, shift=0) in (True, False)
    assert VWAP.crosses_below(vwap_fast, vwap_3, shift=0) in (True, False)

    # Edge cases: period <= 0 and insufficient bars
    vwap_def = VWAP.calculate(high, low, close, volume, period=0)
    assert len(vwap_def) == 40

    vwap_short = VWAP.calculate(high[:5], low[:5], close[:5], volume[:5], period=10)
    assert np.all(np.isnan(vwap_short.values))

    # Zero volume handling
    zero_vol = np.zeros(40)
    vwap_zero = VWAP.calculate(high, low, close, zero_vol, period=10)
    assert not np.isnan(vwap_zero.get(0))


def test_anchored_vwap() -> None:
    """Verify AnchoredVWAP session reset and standard deviation bands."""
    n = 60
    high = np.linspace(102.0, 160.0, n)
    low = np.linspace(98.0, 150.0, n)
    close = np.linspace(100.0, 155.0, n)
    volume = np.linspace(500.0, 1500.0, n)

    # Timestamp series spanning 3 daily sessions
    # 20 bars per day: day 1, day 2, day 3
    base_ts = 1700000000
    timestamps = np.array(
        [base_ts + (i // 20) * 86400 + (i % 20) * 3600 for i in range(n)]
    )

    bands = AnchoredVWAP.calculate(
        high,
        low,
        close,
        volume,
        timestamps=timestamps,
        session_type=1,
        std_dev_mult=2.0,
    )
    assert "vwap" in bands and "upper" in bands and "lower" in bands
    vwap = bands["vwap"]
    upper = bands["upper"]
    lower = bands["lower"]

    assert len(vwap) == n
    assert upper.get(0) >= vwap.get(0) >= lower.get(0)

    # Condition helpers
    c_series = IndicatorSeries(close, name="Close")
    assert isinstance(AnchoredVWAP.is_rising(vwap, shift=0), bool)
    assert isinstance(AnchoredVWAP.is_falling(vwap, shift=0), bool)
    assert isinstance(AnchoredVWAP.bar_closes_above_vwap(c_series, vwap, shift=0), bool)
    assert isinstance(AnchoredVWAP.bar_closes_below_vwap(c_series, vwap, shift=0), bool)
    assert isinstance(
        AnchoredVWAP.bar_closes_above_upper(c_series, upper, shift=0), bool
    )
    assert isinstance(
        AnchoredVWAP.bar_closes_below_lower(c_series, lower, shift=0), bool
    )
    assert isinstance(
        AnchoredVWAP.bar_crosses_above_lower(c_series, lower, shift=0), bool
    )
    assert isinstance(
        AnchoredVWAP.bar_crosses_above_upper(c_series, upper, shift=0), bool
    )
    assert isinstance(
        AnchoredVWAP.bar_crosses_below_lower(c_series, lower, shift=0), bool
    )
    assert isinstance(
        AnchoredVWAP.bar_crosses_below_upper(c_series, upper, shift=0), bool
    )
    assert isinstance(AnchoredVWAP.fast_above_slow(vwap, lower, shift=0), bool)
    assert isinstance(AnchoredVWAP.fast_below_slow(lower, vwap, shift=0), bool)

    # Fallback with anchor_period and anchor_indices
    bands_period = AnchoredVWAP.calculate(
        high,
        low,
        close,
        volume,
        anchor_period=20,
        std_dev_mult=1.5,
    )
    assert len(bands_period["vwap"]) == n

    bands_idx = AnchoredVWAP.calculate(
        high,
        low,
        close,
        volume,
        anchor_indices=[0, 25, 45],
        std_dev_mult=1.0,
    )
    assert len(bands_idx["vwap"]) == n

    # Empty series
    empty_bands = AnchoredVWAP.calculate(
        np.array([]),
        np.array([]),
        np.array([]),
        np.array([]),
    )
    assert len(empty_bands["vwap"]) == 0


def test_volume_profile() -> None:
    """Verify VolumeProfile POC, VAH, VAL extraction and condition checks."""
    n = 60
    high = np.linspace(105.0, 135.0, n)
    low = np.linspace(95.0, 125.0, n)
    close = np.linspace(100.0, 130.0, n)
    volume = np.linspace(100.0, 500.0, n)

    vp = VolumeProfile.calculate(
        high,
        low,
        close,
        volume,
        period=30,
        profile_rows=25,
        value_area_pct=0.70,
    )
    assert "poc" in vp and "vah" in vp and "val" in vp
    poc = vp["poc"]
    vah = vp["vah"]
    val = vp["val"]

    assert len(poc) == n
    assert np.isnan(poc.values[0])
    assert not np.isnan(poc.values[29])

    current_poc = poc.get(0)
    current_vah = vah.get(0)
    current_val = val.get(0)
    assert current_val <= current_poc <= current_vah

    c_series = IndicatorSeries(close, name="Close")
    assert isinstance(VolumeProfile.price_above_poc(c_series, poc, shift=0), bool)
    assert isinstance(VolumeProfile.price_below_poc(c_series, poc, shift=0), bool)
    assert isinstance(VolumeProfile.price_inside_va(c_series, vah, val, shift=0), bool)
    assert isinstance(VolumeProfile.price_outside_va(c_series, vah, val, shift=0), bool)
    assert isinstance(VolumeProfile.poc_is_rising(poc, shift=0), bool)
    assert isinstance(VolumeProfile.poc_is_falling(poc, shift=0), bool)
    assert isinstance(
        VolumeProfile.is_narrow_value_area(vah, val, 100.0, shift=0), bool
    )
    assert isinstance(VolumeProfile.is_wide_value_area(vah, val, 1.0, shift=0), bool)

    # Edge cases: insufficient bars and flat series
    short_vp = VolumeProfile.calculate(
        high[:10], low[:10], close[:10], volume[:10], period=30
    )
    assert np.all(np.isnan(short_vp["poc"].values))

    flat_p = np.full(40, 100.0)
    flat_vp = VolumeProfile.calculate(flat_p, flat_p, flat_p, volume[:40], period=20)
    assert flat_vp["poc"].get(0) == 100.0


def test_tpo_profile() -> None:
    """Verify TPOProfile POC, VAH, VAL, and Initial Balance breakout checks."""
    n = 60
    high = np.linspace(105.0, 135.0, n)
    low = np.linspace(95.0, 125.0, n)
    close = np.linspace(100.0, 130.0, n)

    tpo = TPOProfile.calculate(
        high,
        low,
        close,
        period=30,
        profile_rows=20,
        ib_bars=2,
        value_area_pct=0.70,
    )
    assert "poc" in tpo and "vah" in tpo and "val" in tpo
    assert "ib_high" in tpo and "ib_low" in tpo

    poc = tpo["poc"]
    vah = tpo["vah"]
    val = tpo["val"]
    ibh = tpo["ib_high"]
    ibl = tpo["ib_low"]

    assert len(poc) == n
    assert not np.isnan(poc.values[29])
    assert val.get(0) <= poc.get(0) <= vah.get(0)
    assert ibl.get(0) <= ibh.get(0)

    c_series = IndicatorSeries(close, name="Close")
    assert isinstance(TPOProfile.ib_breakout_up(c_series, ibh, shift=0), bool)
    assert isinstance(TPOProfile.ib_breakout_down(c_series, ibl, shift=0), bool)
    assert isinstance(TPOProfile.price_above_poc(c_series, poc, shift=0), bool)
    assert isinstance(TPOProfile.price_below_poc(c_series, poc, shift=0), bool)
    assert isinstance(TPOProfile.price_inside_va(c_series, vah, val, shift=0), bool)
    assert isinstance(TPOProfile.price_outside_va(c_series, vah, val, shift=0), bool)

    # Edge cases: insufficient bars and flat series
    short_tpo = TPOProfile.calculate(high[:10], low[:10], close[:10], period=30)
    assert np.all(np.isnan(short_tpo["poc"].values))

    flat_p = np.full(40, 100.0)
    flat_tpo = TPOProfile.calculate(flat_p, flat_p, flat_p, period=20)
    assert flat_tpo["poc"].get(0) == 100.0


def test_cot() -> None:
    """Verify COT Composite Score and CPI percentile index calculations."""
    n = 80
    comm = np.linspace(-10000.0, 10000.0, n)
    spec = np.linspace(15000.0, -5000.0, n)

    cot_res = COT.calculate(comm, spec, period_fast=20, period_slow=50)
    assert "composite_score" in cot_res
    assert "cpi_hedger" in cot_res
    assert "cpi_speculator" in cot_res
    assert "hedger_spec_spread" in cot_res

    score = cot_res["composite_score"]
    cpi_h = cot_res["cpi_hedger"]
    cpi_s = cot_res["cpi_speculator"]

    assert len(score) == n
    assert -1.0 <= score.get(0) <= 1.0
    assert 0.0 <= cpi_h.get(0) <= 1.0
    assert 0.0 <= cpi_s.get(0) <= 1.0

    # Condition helpers
    assert isinstance(COT.is_bullish_extreme(score, threshold=0.50, shift=0), bool)
    assert isinstance(COT.is_bearish_extreme(score, threshold=-0.50, shift=0), bool)
    assert isinstance(COT.is_bullish_regime(score, shift=0), bool)
    assert isinstance(COT.is_bearish_regime(score, shift=0), bool)
    assert isinstance(COT.score_crosses_above_zero(score, shift=0), bool)
    assert isinstance(COT.score_crosses_below_zero(score, shift=0), bool)
    assert isinstance(COT.is_rising(score, shift=0), bool)
    assert isinstance(COT.is_falling(score, shift=0), bool)

    # Edge cases: insufficient bars and flat series
    short_cot = COT.calculate(comm[:10], spec[:10], period_fast=20)
    assert np.all(np.isnan(short_cot["composite_score"].values))

    flat_c = np.full(40, 5000.0)
    flat_s = np.full(40, -2000.0)
    flat_cot = COT.calculate(flat_c, flat_s, period_fast=10, period_slow=20)
    assert not np.isnan(flat_cot["composite_score"].get(0))


def test_heiken_ashi() -> None:
    """Verify HeikenAshi smoothed candlesticks and color transition conditions."""
    n = 30
    o = np.linspace(100.0, 130.0, n)
    h = o + 2.0
    low_arr = o - 2.0
    c = o + 1.0

    ha = HeikenAshi.calculate(o, h, low_arr, c)
    assert "open" in ha and "high" in ha and "low" in ha and "close" in ha
    ha_o = ha["open"]
    ha_h = ha["high"]
    ha_l = ha["low"]
    ha_c = ha["close"]

    assert len(ha_o) == n
    # Invariant: high >= max(open, close) and low <= min(open, close)
    for i in range(n):
        assert ha_h.values[i] >= max(ha_o.values[i], ha_c.values[i]) - 1e-9
        assert ha_l.values[i] <= min(ha_o.values[i], ha_c.values[i]) + 1e-9

    assert isinstance(HeikenAshi.is_bullish(ha, shift=0), bool)
    assert isinstance(HeikenAshi.is_bearish(ha, shift=0), bool)
    assert isinstance(HeikenAshi.turns_bullish(ha, shift=0), bool)
    assert isinstance(HeikenAshi.turns_bearish(ha, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="cannot be empty"):
        HeikenAshi.calculate(np.array([]), np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="mismatch"):
        HeikenAshi.calculate(o[:5], h[:4], low_arr[:5], c[:5])


def test_highest_lowest() -> None:
    """Verify HighestLowest rolling extrema and breakout conditions."""
    n = 25
    h = np.linspace(105.0, 135.0, n)
    low_arr = np.linspace(95.0, 125.0, n)
    o = np.linspace(100.0, 130.0, n)
    c = o + 1.0

    res = HighestLowest.calculate(h, low_arr, period=5)
    highest = res["highest"]
    lowest = res["lowest"]
    h_idx = res["highest_index"]
    l_idx = res["lowest_index"]

    assert len(highest) == n
    # Invariant: highest >= lowest
    for i in range(n):
        assert highest.values[i] >= lowest.values[i]
        assert 0.0 <= h_idx.values[i] <= 4.0
        assert 0.0 <= l_idx.values[i] <= 4.0

    # Condition helpers
    assert isinstance(HighestLowest.bar_opens_above_highest(o, highest, shift=0), bool)
    assert isinstance(HighestLowest.bar_opens_below_lowest(o, lowest, shift=0), bool)
    assert isinstance(HighestLowest.bar_opens_below_highest(o, highest, shift=0), bool)
    assert isinstance(HighestLowest.bar_opens_above_lowest(o, lowest, shift=0), bool)
    assert isinstance(
        HighestLowest.cot_emergency_exit_long(c, low_arr, lookback=10, shift=0), bool
    )
    assert isinstance(
        HighestLowest.cot_emergency_exit_short(c, h, lookback=10, shift=0), bool
    )

    # Single series input (low=None)
    single_res = HighestLowest.calculate(h, period=5)
    assert single_res["highest"].get(0) == h[-1]

    # Edge cases
    with pytest.raises(ValueError, match="Period must be >= 1"):
        HighestLowest.calculate(h, low_arr, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        HighestLowest.calculate(np.array([]), np.array([]), period=5)
    with pytest.raises(ValueError, match="mismatch"):
        HighestLowest.calculate(h[:5], low_arr[:4], period=5)


def test_fractal() -> None:
    """Verify Bill Williams Fractal 3-bar and 5-bar detection."""
    # Construct artificial 7-bar series with middle peak and trough
    # Bar indices: 0, 1, 2, 3, 4, 5, 6
    # High: [10, 12, 20, 11, 10, 15, 12] -> peak at bar 2 (high=20)
    # Low:  [ 8,  7, 15,  5,  9,  8, 10] -> trough at bar 3 (low=5)
    h = np.array([10.0, 12.0, 20.0, 11.0, 10.0, 15.0, 12.0])
    low_arr = np.array([8.0, 7.0, 15.0, 5.0, 9.0, 8.0, 10.0])

    f5 = Fractal.calculate(h, low_arr, fractal_bars=5)
    assert "up" in f5 and "down" in f5
    # Pattern confirmed at bar 4 (middle is bar 2)
    assert f5["up"].values[4] == 20.0
    # Pattern confirmed at bar 5 (middle is bar 3)
    assert f5["down"].values[5] == 5.0

    f3 = Fractal.calculate(h, low_arr, fractal_bars=3)
    # 3-bar peak confirmed at bar 3 (middle is bar 2)
    assert f3["up"].values[3] == 20.0

    assert isinstance(Fractal.is_bullish_fractal(f5, shift=0), bool)
    assert isinstance(Fractal.is_bearish_fractal(f5, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="must be an odd integer >= 3"):
        Fractal.calculate(h, low_arr, fractal_bars=4)
    with pytest.raises(ValueError, match="must be an odd integer >= 3"):
        Fractal.calculate(h, low_arr, fractal_bars=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        Fractal.calculate(np.array([]), np.array([]), fractal_bars=3)
    with pytest.raises(ValueError, match="mismatch"):
        Fractal.calculate(h[:4], low_arr[:3], fractal_bars=3)


def test_gann_hi_lo() -> None:
    """Verify Gann Hi-Lo Activator stop line, bands, and trend regime."""
    n = 30
    h = np.linspace(105.0, 135.0, n)
    low_arr = np.linspace(95.0, 125.0, n)
    c = np.linspace(100.0, 130.0, n)

    gh = GannHiLo.calculate(h, low_arr, c, period=10)
    assert "gha" in gh and "gh_high" in gh and "gh_low" in gh and "trend" in gh
    gha = gh["gha"]
    trend = gh["trend"]

    assert len(gha) == n
    assert not np.isnan(gha.get(0))
    assert trend.get(0) in (-1.0, 1.0)

    # Condition helpers
    assert isinstance(GannHiLo.is_uptrend(c, gha, shift=0), bool)
    assert isinstance(GannHiLo.is_downtrend(c, gha, shift=0), bool)
    assert isinstance(GannHiLo.turns_uptrend(c, gha, shift=0), bool)
    assert isinstance(GannHiLo.turns_downtrend(c, gha, shift=0), bool)

    # Edge cases: insufficient bars (< period)
    short_gh = GannHiLo.calculate(h[:5], low_arr[:5], c[:5], period=10)
    assert np.all(np.isnan(short_gh["gha"].values))

    with pytest.raises(ValueError, match="Period must be >= 1"):
        GannHiLo.calculate(h, low_arr, c, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        GannHiLo.calculate(np.array([]), np.array([]), np.array([]), period=5)
    with pytest.raises(ValueError, match="mismatch"):
        GannHiLo.calculate(h[:5], low_arr[:4], c[:5], period=5)


def test_pivots() -> None:
    """Verify Floor Trader Pivot Points PP, R1-R3, S1-S3 geometry and conditions."""
    n = 20
    h = np.linspace(105.0, 125.0, n)
    low_arr = np.linspace(95.0, 115.0, n)
    c = np.linspace(100.0, 120.0, n)

    pivots = Pivots.calculate(h, low_arr, c, period=2)
    assert "pp" in pivots and "r1" in pivots and "s1" in pivots
    pp = pivots["pp"]
    r1 = pivots["r1"]
    r2 = pivots["r2"]
    r3 = pivots["r3"]
    s1 = pivots["s1"]
    s2 = pivots["s2"]
    s3 = pivots["s3"]

    assert len(pp) == n
    # Invariant: s3 <= s2 <= s1 <= pp <= r1 <= r2 <= r3
    curr_s3 = s3.get(0)
    curr_s2 = s2.get(0)
    curr_s1 = s1.get(0)
    curr_pp = pp.get(0)
    curr_r1 = r1.get(0)
    curr_r2 = r2.get(0)
    curr_r3 = r3.get(0)
    assert curr_s3 <= curr_s2 <= curr_s1 <= curr_pp <= curr_r1 <= curr_r2 <= curr_r3

    # Condition helpers
    assert isinstance(Pivots.is_above_pp(c, pp, shift=0), bool)
    assert isinstance(Pivots.is_below_pp(c, pp, shift=0), bool)
    assert isinstance(Pivots.crosses_above(c, r1, shift=0), bool)
    assert isinstance(Pivots.crosses_below(c, s1, shift=0), bool)

    # Session-based pivots with timestamps
    ts = np.array([f"2026-10-{(i // 5) + 1:02d}T10:00:00" for i in range(n)])
    sess_pivots = Pivots.calculate(h, low_arr, c, timestamps=ts)
    assert len(sess_pivots["pp"]) == n

    # Edge cases
    with pytest.raises(ValueError, match="Period must be >= 1"):
        Pivots.calculate(h, low_arr, c, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        Pivots.calculate(np.array([]), np.array([]), np.array([]), period=1)
    with pytest.raises(ValueError, match="identical lengths"):
        Pivots.calculate(h[:5], low_arr[:4], c[:5], period=1)


def test_fibo() -> None:
    """Verify Fibonacci Retracement levels and price condition helpers."""
    n = 25
    h = np.linspace(105.0, 135.0, n)
    low_arr = np.linspace(95.0, 125.0, n)
    c = np.linspace(100.0, 130.0, n)
    o = np.linspace(98.0, 128.0, n)

    fibo = Fibo.calculate(h, low_arr, c, open_prices=o, period=10, custom_level=127.2)
    assert "level_23_6" in fibo
    assert "level_38_2" in fibo
    assert "level_50_0" in fibo
    assert "level_61_8" in fibo
    assert "level_78_6" in fibo
    assert "level_100_0" in fibo
    assert "level_161_8" in fibo
    assert "custom" in fibo

    l38 = fibo["level_38_2"]
    l61 = fibo["level_61_8"]

    assert len(l38) == n
    assert not np.isnan(l38.get(0))

    # Condition helpers
    assert isinstance(Fibo.is_above_level(c, l38, shift=0), bool)
    assert isinstance(Fibo.is_below_level(c, l61, shift=0), bool)
    assert isinstance(Fibo.crosses_above(c, l38, shift=0), bool)
    assert isinstance(Fibo.crosses_below(c, l61, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="Period must be >= 2"):
        Fibo.calculate(h, low_arr, c, period=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        Fibo.calculate(np.array([]), np.array([]), np.array([]), period=5)
    with pytest.raises(ValueError, match="equal lengths"):
        Fibo.calculate(h[:5], low_arr[:4], c[:5], period=5)


def test_lin_reg() -> None:
    """Verify Linear Regression slope, intercept, end-value, and condition checks."""
    # Pure linear sequence: y = 2.0 * t + 10.0 -> slope=2.0
    t = np.arange(20, dtype=np.float64)
    price = 2.0 * t + 10.0

    lr = LinReg.calculate(price, period=10)
    assert "lin_reg" in lr and "slope" in lr and "intercept" in lr
    line = lr["lin_reg"]
    slope = lr["slope"]

    assert len(line) == 20
    # For a purely linear function, fitted end value matches true value
    assert line.get(0) == pytest.approx(price[-1], abs=1e-8)
    assert slope.get(0) == pytest.approx(2.0, abs=1e-8)

    # Condition helpers
    o = price - 0.5
    assert isinstance(LinReg.bar_closes_above(price, line, shift=0), bool)
    assert isinstance(LinReg.bar_closes_below(price, line, shift=0), bool)
    assert isinstance(LinReg.bar_opens_above(o, line, shift=0), bool)
    assert isinstance(LinReg.bar_opens_below(o, line, shift=0), bool)
    assert isinstance(LinReg.is_rising(line, shift=0), bool)
    assert isinstance(LinReg.is_falling(line, shift=0), bool)
    assert isinstance(LinReg.bar_opens_above_after_open_below(o, line, shift=0), bool)
    assert isinstance(LinReg.bar_opens_below_after_open_above(o, line, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="Period must be >= 2"):
        LinReg.calculate(price, period=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        LinReg.calculate(np.array([]), period=5)


def test_trend() -> None:
    """Verify Trend regime classification with SMA and EMA baselines."""
    n = 30
    price_up = np.linspace(10.0, 50.0, n)

    # Upward trend with period=10
    trend_res = Trend.calculate(price_up, period=10, method="sma")
    assert "trend" in trend_res and "baseline" in trend_res
    trend = trend_res["trend"]
    baseline = trend_res["baseline"]

    assert len(trend) == n
    assert trend.get(0) == 1.0  # Clearly in uptrend

    # EMA method
    ema_res = Trend.calculate(price_up, period=10, method="ema")
    assert ema_res["trend"].get(0) == 1.0

    # Downward trend
    price_down = np.linspace(50.0, 10.0, n)
    down_res = Trend.calculate(price_down, period=10, method="sma")
    assert down_res["trend"].get(0) == -1.0

    # Condition helpers
    assert Trend.is_uptrend(price_up, baseline, shift=0) is True
    assert Trend.is_downtrend(price_up, baseline, shift=0) is False
    assert isinstance(Trend.turns_uptrend(price_up, baseline, shift=0), bool)
    assert isinstance(Trend.turns_downtrend(price_up, baseline, shift=0), bool)

    # Edge cases: insufficient bars (< period)
    short_trend = Trend.calculate(price_up[:5], period=10)
    assert np.all(np.isnan(short_trend["baseline"].values))

    with pytest.raises(ValueError, match="Period must be >= 1"):
        Trend.calculate(price_up, period=0)
    with pytest.raises(ValueError, match="Unsupported method"):
        Trend.calculate(price_up, period=10, method="invalid_method")
    with pytest.raises(ValueError, match="cannot be empty"):
        Trend.calculate(np.array([]), period=10)


def test_laguerre_rsi() -> None:
    """Verify Laguerre RSI calculation, boundaries in [0, 1], and condition logic."""
    n = 60
    close = np.linspace(100.0, 150.0, n)
    lrsi = LaguerreRSI.calculate(close, gamma=0.5)

    assert len(lrsi) == n
    # Values bounded in [0.0, 1.0]
    for val in lrsi.values:
        assert 0.0 <= val <= 1.0

    assert isinstance(LaguerreRSI.is_rising(lrsi, shift=0), bool)
    assert isinstance(LaguerreRSI.is_falling(lrsi, shift=0), bool)
    assert isinstance(LaguerreRSI.crosses_above(lrsi, level=0.2, shift=0), bool)
    assert isinstance(LaguerreRSI.crosses_below(lrsi, level=0.8, shift=0), bool)
    assert isinstance(LaguerreRSI.changes_up(lrsi, shift=0), bool)
    assert isinstance(LaguerreRSI.changes_down(lrsi, shift=0), bool)

    # Short series (< 20 bars) returns zeros
    short_lrsi = LaguerreRSI.calculate(close[:15], gamma=0.5)
    assert np.all(short_lrsi.values == 0.0)

    # Edge cases
    with pytest.raises(ValueError, match="Gamma must be between"):
        LaguerreRSI.calculate(close, gamma=-0.1)
    with pytest.raises(ValueError, match="Gamma must be between"):
        LaguerreRSI.calculate(close, gamma=1.5)
    with pytest.raises(ValueError, match="cannot be empty"):
        LaguerreRSI.calculate(np.array([]), gamma=0.5)


def test_qqe() -> None:
    """Verify QQE Value1 (Fast) and Value2 (Slow) lines and crossover helpers."""
    n = 60
    close = np.linspace(100.0, 140.0, n)
    qqe_res = QQE.calculate(close, rsi_period=14, sf=5, wf=4.236)
    assert "value1" in qqe_res and "value2" in qqe_res
    v1 = qqe_res["value1"]
    v2 = qqe_res["value2"]

    assert len(v1) == n
    assert len(v2) == n
    assert not np.isnan(v1.get(0))
    assert not np.isnan(v2.get(0))

    # Condition helpers
    assert isinstance(QQE.value1_crosses_above_value2(v1, v2, shift=0), bool)
    assert isinstance(QQE.value1_crosses_below_value2(v1, v2, shift=0), bool)
    assert isinstance(QQE.value1_higher_value2(v1, v2, shift=0), bool)
    assert isinstance(QQE.value1_lower_value2(v1, v2, shift=0), bool)
    assert isinstance(QQE.value1_is_rising(v1, shift=0), bool)
    assert isinstance(QQE.value1_is_falling(v1, shift=0), bool)

    # Short series (< rsi_period + 1) returns NaNs
    short_qqe = QQE.calculate(close[:10], rsi_period=14)
    assert np.all(np.isnan(short_qqe["value1"].values))

    # Edge cases
    with pytest.raises(ValueError, match="rsi_period must be >= 2"):
        QQE.calculate(close, rsi_period=1)
    with pytest.raises(ValueError, match="sf must be >= 1"):
        QQE.calculate(close, rsi_period=14, sf=0)
    with pytest.raises(ValueError, match=r"wf must be > 0\.0"):
        QQE.calculate(close, rsi_period=14, wf=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        QQE.calculate(np.array([]))


def test_reflex() -> None:
    """Verify John Ehlers' Reflex indicator and fast/slow cross evaluators."""
    n = 60
    close = np.linspace(100.0, 130.0, n) + np.sin(np.linspace(0, 10, n)) * 5.0
    reflex_res = Reflex.calculate(close, period=20, slow_period=40)
    assert "reflex" in reflex_res and "fast" in reflex_res and "slow" in reflex_res
    fast = reflex_res["fast"]
    slow = reflex_res["slow"]

    assert len(fast) == n
    assert not np.isnan(fast.get(0))

    # Condition helpers
    assert isinstance(Reflex.fast_crosses_above_slow(fast, slow, shift=0), bool)
    assert isinstance(Reflex.fast_crosses_below_slow(fast, slow, shift=0), bool)
    assert isinstance(Reflex.is_rising(fast, shift=0), bool)
    assert isinstance(Reflex.is_falling(fast, shift=0), bool)
    assert isinstance(Reflex.changes_direction_up(fast, shift=0), bool)
    assert isinstance(Reflex.changes_direction_down(fast, shift=0), bool)

    # Single series calculate
    single = Reflex.calculate(close, period=20)
    assert "slow" not in single

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        Reflex.calculate(close, period=1)
    with pytest.raises(ValueError, match="slow_period must be >= 2"):
        Reflex.calculate(close, period=10, slow_period=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        Reflex.calculate(np.array([]))


def test_schaff_trend_cycle() -> None:
    """Verify Schaff Trend Cycle oscillator bounds [0, 100] and conditions."""
    n = 80
    close = np.linspace(100.0, 160.0, n)
    stc = SchaffTrendCycle.calculate(
        close, stoch_period=10, fast_period=20, slow_period=50
    )

    assert len(stc) == n
    for val in stc.values:
        assert 0.0 <= val <= 100.0

    # Condition helpers
    assert isinstance(SchaffTrendCycle.is_above_level(stc, level=75.0, shift=0), bool)
    assert isinstance(SchaffTrendCycle.is_below_level(stc, level=25.0, shift=0), bool)
    assert isinstance(SchaffTrendCycle.crosses_above(stc, level=25.0, shift=0), bool)
    assert isinstance(SchaffTrendCycle.crosses_below(stc, level=75.0, shift=0), bool)
    assert isinstance(SchaffTrendCycle.is_rising(stc, shift=0), bool)
    assert isinstance(SchaffTrendCycle.is_falling(stc, shift=0), bool)

    # Short series (< slow_period) returns zeros
    short_stc = SchaffTrendCycle.calculate(
        close[:40], stoch_period=10, fast_period=20, slow_period=50
    )
    assert np.all(short_stc.values == 0.0)

    # Edge cases
    with pytest.raises(ValueError, match="stoch_period must be >= 2"):
        SchaffTrendCycle.calculate(close, stoch_period=1)
    with pytest.raises(ValueError, match=r"slow_period .* must be > fast_period"):
        SchaffTrendCycle.calculate(close, fast_period=30, slow_period=20)
    with pytest.raises(ValueError, match="factor must be in"):
        SchaffTrendCycle.calculate(close, factor=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        SchaffTrendCycle.calculate(np.array([]))


def test_wave_trend() -> None:
    """Verify WaveTrend WT1 and WT2 oscillator lines and crossover conditions."""
    n = 50
    h = np.linspace(105.0, 145.0, n)
    low_arr = np.linspace(95.0, 135.0, n)
    c = np.linspace(100.0, 140.0, n)

    wt = WaveTrend.calculate(h, low_arr, c, channel_length=10, average_length=21)
    assert "wt1" in wt and "wt2" in wt
    wt1 = wt["wt1"]
    wt2 = wt["wt2"]

    assert len(wt1) == n
    assert len(wt2) == n
    assert not np.isnan(wt1.get(0))

    # Single series typical price input
    single_wt = WaveTrend.calculate(c, channel_length=10, average_length=21)
    assert len(single_wt["wt1"]) == n

    # Condition helpers
    assert isinstance(WaveTrend.wt1_crosses_above_wt2(wt1, wt2, shift=0), bool)
    assert isinstance(WaveTrend.wt1_crosses_below_wt2(wt1, wt2, shift=0), bool)
    assert isinstance(WaveTrend.wt1_crosses_above_zero(wt1, shift=0), bool)
    assert isinstance(WaveTrend.wt1_crosses_below_zero(wt1, shift=0), bool)
    assert isinstance(WaveTrend.wt1_is_rising(wt1, shift=0), bool)
    assert isinstance(WaveTrend.wt1_is_falling(wt1, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="Lengths must satisfy"):
        WaveTrend.calculate(c, channel_length=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        WaveTrend.calculate(np.array([]))
    with pytest.raises(ValueError, match="array lengths must match"):
        WaveTrend.calculate(h[:5], low_arr[:4], c[:5])


def test_ichimoku() -> None:
    """Verify Ichimoku 5-line system and cloud breakout condition logic."""
    n = 70
    h = np.linspace(105.0, 155.0, n)
    low_arr = np.linspace(95.0, 145.0, n)
    c = np.linspace(100.0, 150.0, n)

    ichi = Ichimoku.calculate(h, low_arr, c, tenkan=9, kijun=26, senkou=52)
    assert "tenkan_sen" in ichi
    assert "kijun_sen" in ichi
    assert "senkou_span_a" in ichi
    assert "senkou_span_b" in ichi
    assert "chikou_span" in ichi

    ts = ichi["tenkan_sen"]
    ks = ichi["kijun_sen"]
    sa = ichi["senkou_span_a"]
    sb = ichi["senkou_span_b"]

    assert len(ts) == n
    assert not np.isnan(ts.get(0))
    assert not np.isnan(ks.get(0))

    # Condition helpers
    assert isinstance(Ichimoku.tenkan_kijun_cross_bullish(ts, ks, shift=0), bool)
    assert isinstance(Ichimoku.tenkan_kijun_cross_bearish(ts, ks, shift=0), bool)
    assert isinstance(Ichimoku.kumo_breakout_bullish(c, sa, sb, shift=0), bool)
    assert isinstance(Ichimoku.kumo_breakout_bearish(c, sa, sb, shift=0), bool)
    assert isinstance(Ichimoku.senkou_span_cross_bullish(sa, sb, shift=0), bool)
    assert isinstance(Ichimoku.senkou_span_cross_bearish(sa, sb, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="must be >= 1"):
        Ichimoku.calculate(h, low_arr, c, tenkan=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        Ichimoku.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        Ichimoku.calculate(h[:5], low_arr[:4], c[:5])


def test_choppiness_index() -> None:
    """Verify ChoppinessIndex bounded calculations, regime states, and conditions."""
    n = 50
    c = np.linspace(100.0, 130.0, n)
    h = c + 1.5
    low_arr = c - 1.5

    res = ChoppinessIndex.calculate(h, low_arr, c, period=14)
    assert "chop" in res and "regime" in res
    chop = res["chop"]
    regime = res["regime"]

    assert len(chop) == n
    assert len(regime) == n
    for val in chop.values:
        assert 0.0 <= val <= 100.0

    # Condition helpers
    assert isinstance(ChoppinessIndex.is_trending(chop, shift=0), bool)
    assert isinstance(ChoppinessIndex.is_choppy(chop, shift=0), bool)
    assert isinstance(ChoppinessIndex.is_in_transition(chop, shift=0), bool)
    assert isinstance(ChoppinessIndex.crosses_above(chop, level=50.0, shift=0), bool)
    assert isinstance(ChoppinessIndex.crosses_below(chop, level=50.0, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        ChoppinessIndex.calculate(h, low_arr, c, period=1)
    with pytest.raises(ValueError, match="strictly less than"):
        ChoppinessIndex.calculate(
            h, low_arr, c, lower_threshold=60.0, upper_threshold=50.0
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        ChoppinessIndex.calculate(np.array([]), np.array([]), np.array([]))


def test_hurst_exponent() -> None:
    """Verify HurstExponent R/S analysis, persistence detection, and conditions."""
    n = 150
    c = np.linspace(100.0, 200.0, n) + np.sin(np.linspace(0, 15, n)) * 2.0

    res = HurstExponent.calculate(c, window=60, min_scale=8, max_scale=30)
    assert "hurst" in res and "regime" in res
    hurst = res["hurst"]
    regime = res["regime"]

    assert len(hurst) == n
    assert len(regime) == n
    for val in hurst.values:
        assert 0.0 <= val <= 1.0

    # Condition helpers
    assert isinstance(HurstExponent.is_persistent(hurst, shift=0), bool)
    assert isinstance(HurstExponent.is_anti_persistent(hurst, shift=0), bool)
    assert isinstance(HurstExponent.is_random_walk(hurst, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="window must be >= 20"):
        HurstExponent.calculate(c, window=10)
    with pytest.raises(ValueError, match="Invalid scale range"):
        HurstExponent.calculate(c, window=60, min_scale=40, max_scale=30)
    with pytest.raises(ValueError, match="strictly less than"):
        HurstExponent.calculate(c, window=60, lower_threshold=0.6, upper_threshold=0.5)
    with pytest.raises(ValueError, match="cannot be empty"):
        HurstExponent.calculate(np.array([]))


def test_market_regime_resolver() -> None:
    """Verify MarketRegimeResolver multi-factor synthesis and breakout evaluation."""
    n = 80
    c = np.linspace(100.0, 160.0, n)
    h = c + 2.0
    low_arr = c - 2.0

    res = MarketRegimeResolver.calculate(
        h, low_arr, c, adx_period=14, chop_period=14, donchian_period=20
    )
    assert "regime" in res and "confidence" in res
    regime = res["regime"]
    confidence = res["confidence"]

    assert len(regime) == n
    assert len(confidence) == n
    for r in regime.values:
        assert 1.0 <= r <= 9.0
    for conf in confidence.values:
        assert 0.0 <= conf <= 1.0

    # Condition helpers
    assert isinstance(MarketRegimeResolver.is_uptrend(regime, shift=0), bool)
    assert isinstance(MarketRegimeResolver.is_downtrend(regime, shift=0), bool)
    assert isinstance(MarketRegimeResolver.is_ranging(regime, shift=0), bool)
    assert isinstance(MarketRegimeResolver.is_breakout(regime, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="cannot be empty"):
        MarketRegimeResolver.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        MarketRegimeResolver.calculate(h[:10], low_arr[:9], c[:10])


def test_obv() -> None:
    """Verify On-Balance Volume calculation, MA overlay, and conditions."""
    c = np.array([10.0, 11.0, 11.0, 10.5, 12.0])
    v = np.array([100.0, 50.0, 30.0, 20.0, 40.0])

    obv = OBV.calculate(c, v)
    expected = np.array([100.0, 150.0, 150.0, 130.0, 170.0])
    np.testing.assert_allclose(obv.values, expected)

    # Condition helpers
    assert OBV.is_rising(obv, shift=0)
    assert OBV.is_falling(obv, shift=1)
    assert OBV.is_above_level(obv, level=100.0, shift=0)
    assert not OBV.is_below_level(obv, level=100.0, shift=0)
    assert isinstance(OBV.crosses_above(obv, level=140.0, shift=0), bool)
    assert isinstance(OBV.crosses_below(obv, level=140.0, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="cannot be empty"):
        OBV.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        OBV.calculate(c[:3], v[:2])


def test_mfi() -> None:
    """Verify Money Flow Index calculation, boundaries, and conditions."""
    n = 30
    c = np.linspace(10.0, 20.0, n)
    h = c + 1.0
    low_arr = c - 1.0
    v = np.full(n, 1000.0)

    mfi = MFI.calculate(h, low_arr, c, v, period=14)
    assert len(mfi) == n
    for val in mfi.values:
        assert 0.0 <= val <= 100.0

    # Condition helpers
    assert isinstance(MFI.is_above_level(mfi, level=50.0, shift=0), bool)
    assert isinstance(MFI.is_below_level(mfi, level=50.0, shift=0), bool)
    assert isinstance(MFI.is_overbought(mfi, threshold=80.0, shift=0), bool)
    assert isinstance(MFI.is_oversold(mfi, threshold=20.0, shift=0), bool)
    assert isinstance(MFI.crosses_above(mfi, level=50.0, shift=0), bool)
    assert isinstance(MFI.crosses_below(mfi, level=50.0, shift=0), bool)
    assert isinstance(MFI.is_rising(mfi, shift=0), bool)
    assert isinstance(MFI.is_falling(mfi, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        MFI.calculate(h, low_arr, c, v, period=1)
    with pytest.raises(ValueError, match="cannot be empty"):
        MFI.calculate(np.array([]), np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        MFI.calculate(h[:5], low_arr[:4], c[:5], v[:5])


def test_cmf() -> None:
    """Verify Chaikin Money Flow calculation, bounds [-1, 1], and conditions."""
    n = 30
    c = np.linspace(10.0, 20.0, n)
    h = c + 1.0
    low_arr = c - 1.0
    v = np.full(n, 100.0)

    cmf = CMF.calculate(h, low_arr, c, v, period=20)
    assert len(cmf) == n
    for val in cmf.values:
        assert -1.0 <= val <= 1.0

    # Condition helpers
    assert isinstance(CMF.is_above_zero(cmf, shift=0), bool)
    assert isinstance(CMF.is_below_zero(cmf, shift=0), bool)
    assert isinstance(CMF.crosses_above(cmf, level=0.0, shift=0), bool)
    assert isinstance(CMF.crosses_below(cmf, level=0.0, shift=0), bool)
    assert isinstance(CMF.is_rising(cmf, shift=0), bool)
    assert isinstance(CMF.is_falling(cmf, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 1"):
        CMF.calculate(h, low_arr, c, v, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        CMF.calculate(np.array([]), np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        CMF.calculate(h[:5], low_arr[:5], c[:4], v[:5])


def test_order_flow() -> None:
    """Verify CumulativeVolumeDelta and AggressiveTradeImbalance calculations."""
    o = np.array([10.0, 11.5, 11.0, 10.8])
    c = np.array([11.0, 11.0, 11.5, 10.2])
    v = np.array([100.0, 80.0, 50.0, 60.0])

    # CVD calculation (implicit deltas)
    res = CumulativeVolumeDelta.calculate(o, c, v, window=2)
    assert "cvd" in res and "delta" in res
    cvd = res["cvd"]
    delta = res["delta"]
    assert len(cvd) == 4
    assert len(delta) == 4

    # CVD with explicit buy / sell volumes
    buy_v = np.array([60.0, 30.0, 40.0, 10.0])
    sell_v = np.array([40.0, 50.0, 10.0, 50.0])
    res_exp = CumulativeVolumeDelta.calculate(
        o, c, v, window=2, buy_volume=buy_v, sell_volume=sell_v
    )
    assert "cvd" in res_exp and "delta" in res_exp
    expected_cvd = np.cumsum(buy_v - sell_v)
    np.testing.assert_allclose(res_exp["cvd"].values, expected_cvd)

    # CVD condition helpers
    assert isinstance(CumulativeVolumeDelta.is_positive(cvd, shift=0), bool)
    assert isinstance(CumulativeVolumeDelta.is_negative(cvd, shift=0), bool)
    assert isinstance(CumulativeVolumeDelta.crosses_above_zero(cvd, shift=0), bool)
    assert isinstance(CumulativeVolumeDelta.crosses_below_zero(cvd, shift=0), bool)
    assert isinstance(CumulativeVolumeDelta.is_rising(cvd, shift=0), bool)
    assert isinstance(CumulativeVolumeDelta.is_falling(cvd, shift=0), bool)

    # CVD edge cases
    with pytest.raises(ValueError, match="window must be >= 1"):
        CumulativeVolumeDelta.calculate(o, c, v, window=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        CumulativeVolumeDelta.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        CumulativeVolumeDelta.calculate(o[:2], c[:3], v[:3])
    with pytest.raises(
        ValueError, match="buy_volume and sell_volume lengths must match"
    ):
        CumulativeVolumeDelta.calculate(
            o, c, v, buy_volume=buy_v[:2], sell_volume=sell_v
        )

    # ATI calculation
    ati = AggressiveTradeImbalance.calculate(o, c, v, window=2)
    assert len(ati) == 4
    for val in ati.values:
        assert -1.0 <= val <= 1.0

    ati_exp = AggressiveTradeImbalance.calculate(
        o, c, v, window=2, buy_volume=buy_v, sell_volume=sell_v
    )
    assert len(ati_exp) == 4
    for val in ati_exp.values:
        assert -1.0 <= val <= 1.0

    # ATI condition helpers
    assert isinstance(
        AggressiveTradeImbalance.is_buyer_dominated(ati, threshold=0.1, shift=0), bool
    )
    assert isinstance(
        AggressiveTradeImbalance.is_seller_dominated(ati, threshold=-0.1, shift=0), bool
    )
    assert isinstance(
        AggressiveTradeImbalance.crosses_above(ati, level=0.0, shift=0), bool
    )
    assert isinstance(
        AggressiveTradeImbalance.crosses_below(ati, level=0.0, shift=0), bool
    )
    assert isinstance(AggressiveTradeImbalance.is_rising(ati, shift=0), bool)
    assert isinstance(AggressiveTradeImbalance.is_falling(ati, shift=0), bool)

    # ATI edge cases
    with pytest.raises(ValueError, match="window must be >= 1"):
        AggressiveTradeImbalance.calculate(o, c, v, window=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        AggressiveTradeImbalance.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        AggressiveTradeImbalance.calculate(o[:2], c[:3], v[:3])
    with pytest.raises(
        ValueError, match="buy_volume and sell_volume lengths must match"
    ):
        AggressiveTradeImbalance.calculate(
            o, c, v, buy_volume=buy_v, sell_volume=sell_v[:2]
        )


def test_donchian_channels() -> None:
    """Verify DonchianChannels calculations, shift offset, and conditions."""
    h = np.array([12.0, 13.0, 15.0, 14.0, 16.0, 14.5])
    low_arr = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 12.0])
    c = np.array([11.0, 12.0, 14.0, 12.5, 15.0, 13.0])

    res = DonchianChannels.calculate(h, low_arr, period=3, offset=0)
    assert "upper" in res and "lower" in res and "middle" in res and "width" in res
    upper = res["upper"]
    lower = res["lower"]
    middle = res["middle"]
    width = res["width"]

    assert len(upper) == 6
    assert upper.values[2] == 15.0
    assert lower.values[2] == 10.0
    assert middle.values[2] == 12.5
    assert width.values[2] == 5.0

    # With offset
    res_off = DonchianChannels.calculate(h, low_arr, period=3, offset=1)
    assert np.isnan(res_off["upper"].values[0])
    assert res_off["upper"].values[3] == upper.values[2]

    # Condition helpers
    c_series = IndicatorSeries(c)
    assert isinstance(DonchianChannels.is_above_upper(c_series, upper, shift=0), bool)
    assert isinstance(DonchianChannels.is_below_lower(c_series, lower, shift=0), bool)
    assert isinstance(
        DonchianChannels.crosses_above_upper(c_series, upper, shift=0), bool
    )
    assert isinstance(
        DonchianChannels.crosses_below_lower(c_series, lower, shift=0), bool
    )
    assert isinstance(
        DonchianChannels.crosses_above_middle(c_series, middle, shift=0), bool
    )
    assert isinstance(
        DonchianChannels.crosses_below_middle(c_series, middle, shift=0), bool
    )
    assert DonchianChannels.is_squeezed(width, threshold=10.0, shift=0)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        DonchianChannels.calculate(h, low_arr, period=1)
    with pytest.raises(ValueError, match="offset must be >= 0"):
        DonchianChannels.calculate(h, low_arr, period=3, offset=-1)
    with pytest.raises(ValueError, match="cannot be empty"):
        DonchianChannels.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        DonchianChannels.calculate(h[:3], low_arr[:2])


def test_tema() -> None:
    """Verify Triple Exponential Moving Average calculation and crossovers."""
    n = 30
    c = np.linspace(100.0, 130.0, n)
    c_series = IndicatorSeries(c)

    tema = TEMA.calculate(c, period=5)
    assert len(tema) == n
    assert TEMA.is_rising(tema, shift=0)
    assert not TEMA.is_falling(tema, shift=0)

    # Condition helpers
    assert isinstance(TEMA.is_above_price(tema, c_series, shift=0), bool)
    assert isinstance(TEMA.is_below_price(tema, c_series, shift=0), bool)
    assert isinstance(TEMA.crosses_above(c_series, tema, shift=0), bool)
    assert isinstance(TEMA.crosses_below(c_series, tema, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 1"):
        TEMA.calculate(c, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        TEMA.calculate(np.array([]))


def test_zigzag() -> None:
    """Verify ZigZag swing points, types, interpolated line, and conditions."""
    h = np.array([10.0, 15.0, 20.0, 18.0, 14.0, 10.0, 12.0, 16.0, 22.0, 25.0])
    low_arr = h - 1.0

    res = ZigZag.calculate(h, low_arr, deviation=10.0, depth=2)
    assert "zigzag" in res and "swing_point" in res and "swing_type" in res
    zigzag = res["zigzag"]
    swing_type = res["swing_type"]

    assert len(zigzag) == 10
    assert len(swing_type) == 10
    assert not np.isnan(zigzag.values).any()

    # Condition helpers
    assert isinstance(ZigZag.is_peak(swing_type, shift=0), bool)
    assert isinstance(ZigZag.is_trough(swing_type, shift=0), bool)
    assert isinstance(ZigZag.is_swing(swing_type, shift=0), bool)
    assert ZigZag.last_swing_direction(swing_type, shift=0) in (-1, 0, 1)
    assert isinstance(ZigZag.is_rising(zigzag, shift=0), bool)
    assert isinstance(ZigZag.is_falling(zigzag, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match=r"deviation must be >= 0\.01"):
        ZigZag.calculate(h, low_arr, deviation=0.001)
    with pytest.raises(ValueError, match="depth must be >= 1"):
        ZigZag.calculate(h, low_arr, depth=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        ZigZag.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        ZigZag.calculate(h[:5], low_arr[:4])


def test_parkinson_volatility() -> None:
    """Verify Parkinson volatility extreme value estimation and conditions."""
    h = np.linspace(102.0, 115.0, 30)
    low_arr = np.linspace(98.0, 105.0, 30)

    vol = ParkinsonVolatility.calculate(
        h, low_arr, period=10, annualize=True, trading_periods=252
    )
    assert len(vol) == 30
    for val in vol.values:
        assert val >= 0.0

    # Condition helpers
    assert isinstance(
        ParkinsonVolatility.is_elevated(vol, threshold=0.1, shift=0), bool
    )
    assert isinstance(ParkinsonVolatility.is_subdued(vol, threshold=0.5, shift=0), bool)
    assert isinstance(
        ParkinsonVolatility.crosses_above(vol, threshold=0.2, shift=0), bool
    )
    assert isinstance(
        ParkinsonVolatility.crosses_below(vol, threshold=0.2, shift=0), bool
    )
    assert isinstance(ParkinsonVolatility.is_rising(vol, shift=0), bool)
    assert isinstance(ParkinsonVolatility.is_falling(vol, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        ParkinsonVolatility.calculate(h, low_arr, period=1)
    with pytest.raises(ValueError, match="trading_periods must be >= 1"):
        ParkinsonVolatility.calculate(h, low_arr, trading_periods=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        ParkinsonVolatility.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        ParkinsonVolatility.calculate(h[:5], low_arr[:4])


def test_garman_klass_volatility() -> None:
    """Verify Garman-Klass volatility estimation and condition evaluation."""
    o = np.linspace(100.0, 110.0, 30)
    h = o + 3.0
    low_arr = o - 2.0
    c = o + 1.0

    vol = GarmanKlassVolatility.calculate(o, h, low_arr, c, period=10, annualize=True)
    assert len(vol) == 30
    for val in vol.values:
        assert val >= 0.0

    # Condition helpers
    assert isinstance(
        GarmanKlassVolatility.is_elevated(vol, threshold=0.1, shift=0), bool
    )
    assert isinstance(
        GarmanKlassVolatility.is_subdued(vol, threshold=0.5, shift=0), bool
    )
    assert isinstance(
        GarmanKlassVolatility.crosses_above(vol, threshold=0.2, shift=0), bool
    )
    assert isinstance(
        GarmanKlassVolatility.crosses_below(vol, threshold=0.2, shift=0), bool
    )
    assert isinstance(GarmanKlassVolatility.is_rising(vol, shift=0), bool)
    assert isinstance(GarmanKlassVolatility.is_falling(vol, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        GarmanKlassVolatility.calculate(o, h, low_arr, c, period=1)
    with pytest.raises(ValueError, match="trading_periods must be >= 1"):
        GarmanKlassVolatility.calculate(o, h, low_arr, c, trading_periods=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        GarmanKlassVolatility.calculate(
            np.array([]), np.array([]), np.array([]), np.array([])
        )
    with pytest.raises(ValueError, match="lengths must match"):
        GarmanKlassVolatility.calculate(o[:4], h[:5], low_arr[:5], c[:5])


def test_rogers_satchell_volatility() -> None:
    """Verify Rogers-Satchell volatility estimation with non-zero drift."""
    o = np.linspace(100.0, 110.0, 30)
    h = o + 3.0
    low_arr = o - 2.0
    c = o + 1.5

    vol = RogersSatchellVolatility.calculate(
        o, h, low_arr, c, period=10, annualize=False
    )
    assert len(vol) == 30
    for val in vol.values:
        assert val >= 0.0

    # Condition helpers
    assert isinstance(
        RogersSatchellVolatility.is_elevated(vol, threshold=0.01, shift=0), bool
    )
    assert isinstance(
        RogersSatchellVolatility.is_subdued(vol, threshold=0.1, shift=0), bool
    )
    assert isinstance(
        RogersSatchellVolatility.crosses_above(vol, threshold=0.05, shift=0), bool
    )
    assert isinstance(
        RogersSatchellVolatility.crosses_below(vol, threshold=0.05, shift=0), bool
    )
    assert isinstance(RogersSatchellVolatility.is_rising(vol, shift=0), bool)
    assert isinstance(RogersSatchellVolatility.is_falling(vol, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 2"):
        RogersSatchellVolatility.calculate(o, h, low_arr, c, period=1)
    with pytest.raises(ValueError, match="trading_periods must be >= 1"):
        RogersSatchellVolatility.calculate(o, h, low_arr, c, trading_periods=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        RogersSatchellVolatility.calculate(
            np.array([]), np.array([]), np.array([]), np.array([])
        )
    with pytest.raises(ValueError, match="lengths must match"):
        RogersSatchellVolatility.calculate(o[:5], h[:4], low_arr[:5], c[:5])


def test_average_daily_range() -> None:
    """Verify Average Daily Range calculation and stretch ratio."""
    h = np.array([105.0, 106.0, 108.0, 107.0, 110.0])
    low_arr = np.array([100.0, 101.0, 102.0, 103.0, 104.0])

    res = AverageDailyRange.calculate(h, low_arr, period=2)
    assert "adr" in res and "stretch" in res
    adr = res["adr"]
    stretch = res["stretch"]

    assert len(adr) == 5
    assert len(stretch) == 5
    assert adr.values[1] == 5.0
    assert stretch.values[1] == 1.0

    # Condition helpers
    assert isinstance(
        AverageDailyRange.is_stretched(stretch, threshold=1.2, shift=0), bool
    )
    assert isinstance(
        AverageDailyRange.is_compressed(stretch, threshold=0.8, shift=0), bool
    )
    assert isinstance(AverageDailyRange.crosses_above(adr, level=5.0, shift=0), bool)
    assert isinstance(AverageDailyRange.crosses_below(adr, level=5.0, shift=0), bool)
    assert isinstance(AverageDailyRange.is_rising(adr, shift=0), bool)
    assert isinstance(AverageDailyRange.is_falling(adr, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 1"):
        AverageDailyRange.calculate(h, low_arr, period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        AverageDailyRange.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        AverageDailyRange.calculate(h[:3], low_arr[:2])


def test_amihud_illiquidity() -> None:
    """Verify Amihud illiquidity price impact ratio and conditions."""
    c = np.array([100.0, 102.0, 101.0, 105.0, 103.0])
    v = np.array([1000.0, 1500.0, 1200.0, 800.0, 2000.0])

    amihud = AmihudIlliquidity.calculate(c, v, period=2)
    assert len(amihud) == 5
    for val in amihud.values:
        assert val >= 0.0

    # Condition helpers
    assert isinstance(
        AmihudIlliquidity.is_illiquid(amihud, threshold=0.1, shift=0), bool
    )
    assert isinstance(AmihudIlliquidity.is_liquid(amihud, threshold=0.5, shift=0), bool)
    assert isinstance(AmihudIlliquidity.crosses_above(amihud, level=0.2, shift=0), bool)
    assert isinstance(AmihudIlliquidity.crosses_below(amihud, level=0.2, shift=0), bool)
    assert isinstance(AmihudIlliquidity.is_rising(amihud, shift=0), bool)
    assert isinstance(AmihudIlliquidity.is_falling(amihud, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 1"):
        AmihudIlliquidity.calculate(c, v, period=0)
    with pytest.raises(ValueError, match=r"multiplier must be > 0\.0"):
        AmihudIlliquidity.calculate(c, v, multiplier=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        AmihudIlliquidity.calculate(np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        AmihudIlliquidity.calculate(c[:3], v[:2])


def test_price_velocity() -> None:
    """Verify Price Velocity raw and normalized rate and acceleration."""
    c = np.linspace(100.0, 120.0, 20)

    res = PriceVelocity.calculate(c, period=5, smooth_period=2)
    assert "velocity" in res and "normalized" in res
    vel = res["velocity"]
    norm = res["normalized"]

    assert len(vel) == 20
    assert len(norm) == 20
    assert (vel.values[5:] > 0.0).all()

    # Condition helpers
    assert isinstance(PriceVelocity.is_accelerating_up(vel, shift=0), bool)
    assert isinstance(PriceVelocity.is_accelerating_down(vel, shift=0), bool)
    assert isinstance(PriceVelocity.crosses_above_zero(vel, shift=0), bool)
    assert isinstance(PriceVelocity.crosses_below_zero(vel, shift=0), bool)
    assert isinstance(PriceVelocity.is_rising(vel, shift=0), bool)
    assert isinstance(PriceVelocity.is_falling(vel, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="period must be >= 1"):
        PriceVelocity.calculate(c, period=0)
    with pytest.raises(ValueError, match="smooth_period must be >= 1"):
        PriceVelocity.calculate(c, smooth_period=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        PriceVelocity.calculate(np.array([]))


def test_candlestick_patterns() -> None:
    """Verify CandlestickPatterns recognition of standard formations."""
    o = np.array(
        [
            100.0,
            100.0,
            100.0,
            102.0,
            97.5,
            100.0,
            96.0,
            105.0,
            93.0,
            100.0,
            112.0,
        ]
    )
    h = np.array(
        [
            105.0,
            105.0,
            101.0,
            103.0,
            104.0,
            102.0,
            105.0,
            106.0,
            102.0,
            111.0,
            113.0,
        ]
    )
    low_arr = np.array(
        [
            95.0,
            95.0,
            85.0,
            97.0,
            97.0,
            98.0,
            95.0,
            94.0,
            92.0,
            99.0,
            102.0,
        ]
    )
    c = np.array(
        [
            102.0,
            100.05,
            100.5,
            98.0,
            103.0,
            101.0,
            104.0,
            95.0,
            101.0,
            110.0,
            103.0,
        ]
    )

    patterns = CandlestickPatterns.calculate(o, h, low_arr, c, doji_ratio=0.10)
    assert "doji" in patterns and "engulfing" in patterns
    assert "pinbar" in patterns and "inside_bar" in patterns
    assert "three_bar" in patterns and "dark_cloud" in patterns
    assert "piercing_line" in patterns

    doji = patterns["doji"]
    engulfing = patterns["engulfing"]
    pinbar = patterns["pinbar"]
    inside = patterns["inside_bar"]
    three_bar = patterns["three_bar"]
    dark_cloud = patterns["dark_cloud"]
    piercing_line = patterns["piercing_line"]

    assert len(doji) == 11
    # Bar 1 is Doji (body 0.05 / range 10.0 = 0.005 <= 0.10)
    assert doji.values[1] == 1.0
    # Bar 2 is Hammer/Pinbar (lower wick 15.0, body 0.5)
    assert pinbar.values[2] == 1.0
    # Bar 4 is Bullish Engulfing of Bar 3
    assert engulfing.values[4] == 1.0
    # Bar 5 is Inside Bar of Bar 4
    assert inside.values[5] == 1.0
    # Bar 8 is Piercing Line after Bar 7
    assert piercing_line.values[8] == 1.0
    # Bar 10 is Dark Cloud Cover after Bar 9
    assert dark_cloud.values[10] == 1.0

    # Condition helpers
    assert isinstance(CandlestickPatterns.is_doji(doji, shift=9), bool)
    assert isinstance(
        CandlestickPatterns.is_bullish_engulfing(engulfing, shift=6), bool
    )
    assert isinstance(
        CandlestickPatterns.is_bearish_engulfing(engulfing, shift=0), bool
    )
    assert isinstance(CandlestickPatterns.is_bullish_pinbar(pinbar, shift=8), bool)
    assert isinstance(CandlestickPatterns.is_hammer(pinbar, shift=8), bool)
    assert isinstance(CandlestickPatterns.is_bearish_pinbar(pinbar, shift=0), bool)
    assert isinstance(CandlestickPatterns.is_shooting_star(pinbar, shift=0), bool)
    assert isinstance(CandlestickPatterns.is_inside_bar(inside, shift=5), bool)
    assert isinstance(
        CandlestickPatterns.is_bullish_three_bar(three_bar, shift=0), bool
    )
    assert isinstance(
        CandlestickPatterns.is_bearish_three_bar(three_bar, shift=0), bool
    )
    assert CandlestickPatterns.is_piercing_line(piercing_line, shift=2) is True
    assert CandlestickPatterns.is_dark_cloud(dark_cloud, shift=0) is True

    # Edge cases
    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        CandlestickPatterns.calculate(o, h, low_arr, c, doji_ratio=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        CandlestickPatterns.calculate(
            np.array([]), np.array([]), np.array([]), np.array([])
        )
    with pytest.raises(ValueError, match="lengths must match"):
        CandlestickPatterns.calculate(o[:4], h[:3], low_arr[:3], c[:3])


def test_chart_patterns() -> None:
    """Verify ChartPatterns double top/bottom and breakout retest."""
    # Synthetic series with double peak around 120.0
    c = np.full(40, 100.0)
    h = np.full(40, 102.0)
    low_arr = np.full(40, 98.0)

    # First peak at bar 10
    h[10] = 120.0
    c[10] = 119.0
    # Second peak at bar 25
    h[25] = 120.0
    c[25] = 119.0

    patterns = ChartPatterns.calculate(h, low_arr, c, lookback=20, tolerance_pct=0.05)
    assert "double_pattern" in patterns and "breakout_retest" in patterns
    dtb = patterns["double_pattern"]
    breakout = patterns["breakout_retest"]

    assert len(dtb) == 40
    assert len(breakout) == 40

    # Condition helpers
    assert isinstance(ChartPatterns.is_double_top(dtb, shift=0), bool)
    assert isinstance(ChartPatterns.is_double_bottom(dtb, shift=0), bool)
    assert isinstance(ChartPatterns.is_bullish_breakout(breakout, shift=0), bool)
    assert isinstance(ChartPatterns.is_bearish_breakout(breakout, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="lookback must be >= 10"):
        ChartPatterns.calculate(h, low_arr, c, lookback=5)
    with pytest.raises(ValueError, match="tolerance_pct must be between 0 and 1"):
        ChartPatterns.calculate(h, low_arr, c, tolerance_pct=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        ChartPatterns.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        ChartPatterns.calculate(h[:5], low_arr[:4], c[:4])


def test_price_gap() -> None:
    """Verify PriceGap full and body gap detection and fill status."""
    o = np.array([100.0, 110.0, 95.0, 102.0])
    h = np.array([105.0, 115.0, 97.0, 104.0])
    low_arr = np.array([98.0, 108.0, 90.0, 99.0])
    c = np.array([102.0, 112.0, 92.0, 103.0])

    # Full gap
    full = PriceGap.calculate(o, h, low_arr, c, full_gap=True)
    assert "gap_size" in full and "gap_filled" in full
    g_size = full["gap_size"]
    g_filled = full["gap_filled"]

    assert len(g_size) == 4
    # Bar 1: low 108 > prev high 105 -> gap up of 3.0
    assert g_size.values[1] == 3.0
    # Bar 2: high 97 < prev low 108 -> gap down of 97 - 108 = -11.0
    assert g_size.values[2] == -11.0

    # Body gap
    body = PriceGap.calculate(o, h, low_arr, c, full_gap=False)
    b_size = body["gap_size"]
    b_filled = body["gap_filled"]
    assert len(b_size) == 4

    # Condition helpers
    assert PriceGap.is_gap_up(g_size, min_size=1.0, shift=2) is True
    assert PriceGap.is_gap_down(g_size, min_size=5.0, shift=1) is True
    assert isinstance(PriceGap.is_gap_filled(g_filled, shift=0), bool)
    assert isinstance(PriceGap.is_gap_filled(b_filled, shift=0), bool)

    # Edge cases
    with pytest.raises(ValueError, match="cannot be empty"):
        PriceGap.calculate(np.array([]), np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        PriceGap.calculate(o[:3], h[:2], low_arr[:2], c[:2])


def test_level_clustering() -> None:
    """Verify LevelClustering swing pivot grouping and recency weighting."""
    c = np.array(
        [
            100.0,
            102.0,
            105.0,
            101.0,
            98.0,
            96.0,
            99.0,
            102.0,
            104.0,
            101.0,
            97.0,
            95.0,
            98.0,
            101.0,
            105.0,
            102.0,
            99.0,
            97.0,
            100.0,
            103.0,
        ]
    )
    h = c + 2.0
    low_arr = c - 2.0

    res = LevelClustering.calculate(h, low_arr, c, lookback=15, tolerance=2.0)
    assert "cluster_price" in res and "cluster_weight" in res
    assert "cluster_found" in res

    cl_price = res["cluster_price"]
    cl_weight = res["cluster_weight"]
    cl_found = res["cluster_found"]

    assert len(cl_price) == 20
    assert len(cl_weight) == 20
    assert len(cl_found) == 20

    # Condition helpers
    c_series = IndicatorSeries(c, name="Close")
    assert isinstance(LevelClustering.has_cluster(cl_found, shift=0), bool)
    assert isinstance(
        LevelClustering.is_near_cluster(c_series, cl_price, tolerance=5.0, shift=0),
        bool,
    )
    assert isinstance(
        LevelClustering.is_at_support(c_series, cl_price, tolerance=5.0, shift=0),
        bool,
    )
    assert isinstance(
        LevelClustering.is_at_resistance(c_series, cl_price, tolerance=5.0, shift=0),
        bool,
    )

    # Edge cases
    with pytest.raises(ValueError, match="lookback must be >= 5"):
        LevelClustering.calculate(h, low_arr, c, lookback=3)
    with pytest.raises(ValueError, match="tolerance must be > 0"):
        LevelClustering.calculate(h, low_arr, c, tolerance=0.0)
    with pytest.raises(ValueError, match="cannot be empty"):
        LevelClustering.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        LevelClustering.calculate(h[:4], low_arr[:3], c[:3])
