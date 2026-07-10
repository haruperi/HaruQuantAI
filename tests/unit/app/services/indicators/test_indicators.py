import numpy as np
import pandas as pd
import pytest
from app.services.indicators import (
    BaseIndicator,
    atr,
    bollinger_bands,
    cmf,
    doji,
    ema,
    engulfing,
    hull_moving_average,
    inside_bar,
    macd,
    mfi,
    obv,
    pinbar,
    price_volume_distribution,
    rsi,
    sma,
    smc,
    standard_deviation,
    williams_r,
    wma,
)
from app.services.indicators.candles.doji import Doji
from app.services.indicators.candles.engulfing import Engulfing
from app.services.indicators.candles.inside_bar import InsideBar
from app.services.indicators.candles.pinbar import Pinbar
from app.services.indicators.custom.hull_moving_average import HullMovingAverage
from app.services.indicators.custom.smc import SMC
from app.services.indicators.momentum.macd import MACD
from app.services.indicators.momentum.rsi import RSI
from app.services.indicators.momentum.will_r import WilliamsR
from app.services.indicators.trend.bollinger_bands import BollingerBands
from app.services.indicators.trend.ema import EMA
from app.services.indicators.trend.sma import SMA
from app.services.indicators.trend.wma import WMA
from app.services.indicators.volatility.atr import ATR
from app.services.indicators.volatility.standard_deviation import StandardDeviation
from app.services.indicators.volume.cmf import CMF
from app.services.indicators.volume.mfi import MFI
from app.services.indicators.volume.obv import OBV
from app.services.indicators.volume.price_volume_distribution import (
    PriceVolumeDistribution,
)


@pytest.fixture
def sample_ohlcv_data():
    np.random.seed(42)
    rows = 120  # increased size for lookback ranges like SMC swing_length
    dates = pd.date_range(start="2026-01-01", periods=rows, freq="1D")

    close = np.cumprod(1.0 + np.random.normal(0, 0.01, rows)) * 100.0
    open_val = close + np.random.normal(0, 0.5, rows)
    high = np.maximum(open_val, close) + np.random.uniform(0.1, 2.0, rows)
    low = np.minimum(open_val, close) - np.random.uniform(0.1, 2.0, rows)
    volume = np.random.uniform(1000, 5000, rows)

    df = pd.DataFrame(
        {"open": open_val, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )
    return df


def test_base_inheritance():
    # Verify all indicators inherit from BaseIndicator
    indicators = [
        EMA(),
        SMA(),
        WMA(),
        BollingerBands(),
        RSI(),
        MACD(),
        WilliamsR(),
        OBV(),
        MFI(),
        CMF(),
        PriceVolumeDistribution(),
        ATR(),
        StandardDeviation(),
        Engulfing(),
        Pinbar(),
        Doji(),
        InsideBar(),
        SMC(),
        HullMovingAverage(),
    ]
    for ind in indicators:
        assert isinstance(ind, BaseIndicator)


def test_trend_indicators(sample_ohlcv_data):
    # Test EMA
    res_ema = ema.calculate(sample_ohlcv_data, period=10)
    assert isinstance(res_ema, pd.Series)
    assert res_ema.name == "ema_10"
    assert len(res_ema) == len(sample_ohlcv_data)

    # Test SMA
    res_sma = sma.calculate(sample_ohlcv_data, period=10)
    assert isinstance(res_sma, pd.Series)
    assert res_sma.name == "sma_10"

    # Test WMA
    res_wma = wma.calculate(sample_ohlcv_data, period=10)
    assert isinstance(res_wma, pd.Series)
    assert res_wma.name == "wma_10"

    # Test Bollinger Bands
    res_bb = bollinger_bands.calculate(sample_ohlcv_data, period=20, std_dev=2.0)
    assert isinstance(res_bb, pd.DataFrame)
    assert "bb_middle_20" in res_bb.columns
    assert "bb_upper_20_2.0" in res_bb.columns
    assert "bb_lower_20_2.0" in res_bb.columns


def test_momentum_indicators(sample_ohlcv_data):
    # Test RSI
    res_rsi = rsi.calculate(sample_ohlcv_data, period=14)
    assert isinstance(res_rsi, pd.Series)
    assert res_rsi.name == "rsi_14"

    # Test MACD
    res_macd = macd.calculate(
        sample_ohlcv_data, fast_period=12, slow_period=26, signal_period=9
    )
    assert isinstance(res_macd, pd.DataFrame)
    assert "macd_12_26" in res_macd.columns
    assert "macd_signal_12_26_9" in res_macd.columns
    assert "macd_hist_12_26_9" in res_macd.columns

    # Test Williams %R
    res_wr = williams_r.calculate(sample_ohlcv_data, period=14)
    assert isinstance(res_wr, pd.Series)
    assert res_wr.name == "will_r_14"


def test_volume_indicators(sample_ohlcv_data):
    # Test OBV
    res_obv = obv.calculate(sample_ohlcv_data)
    assert isinstance(res_obv, pd.Series)
    assert res_obv.name == "obv"

    # Test MFI
    res_mfi = mfi.calculate(sample_ohlcv_data, period=14)
    assert isinstance(res_mfi, pd.Series)
    assert res_mfi.name == "mfi_14"

    # Test CMF
    res_cmf = cmf.calculate(sample_ohlcv_data, period=20)
    assert isinstance(res_cmf, pd.Series)
    assert res_cmf.name == "cmf_20"

    # Test Price Volume Distribution
    res_pvd = price_volume_distribution.calculate(sample_ohlcv_data, period=20, bins=10)
    assert isinstance(res_pvd, pd.Series)
    assert res_pvd.name == "pvd_poc_20"


def test_volatility_indicators(sample_ohlcv_data):
    # Test ATR
    res_atr = atr.calculate(sample_ohlcv_data, period=14)
    assert isinstance(res_atr, pd.Series)
    assert res_atr.name == "atr_14"

    # Test Standard Deviation
    res_std = standard_deviation.calculate(sample_ohlcv_data, period=20)
    assert isinstance(res_std, pd.Series)
    assert res_std.name == "std_20"


def test_candles_indicators(sample_ohlcv_data):
    # Test Engulfing
    res_eng = engulfing.calculate(sample_ohlcv_data)
    assert isinstance(res_eng, pd.Series)
    assert res_eng.name == "candle_engulfing"
    assert set(res_eng.unique()).issubset({-1, 0, 1})

    # Test Pinbar
    res_pb = pinbar.calculate(sample_ohlcv_data)
    assert isinstance(res_pb, pd.Series)
    assert res_pb.name == "candle_pinbar"
    assert set(res_pb.unique()).issubset({-1, 0, 1})

    # Test Doji
    res_doji = doji.calculate(sample_ohlcv_data, threshold=0.1)
    assert isinstance(res_doji, pd.Series)
    assert res_doji.name == "candle_doji"
    assert set(res_doji.unique()).issubset({0, 1})

    # Test Inside Bar
    res_ib = inside_bar.calculate(sample_ohlcv_data)
    assert isinstance(res_ib, pd.Series)
    assert res_ib.name == "candle_inside_bar"
    assert set(res_ib.unique()).issubset({0, 1})


def test_custom_indicators(sample_ohlcv_data):
    # Test SMC
    res_smc = smc.calculate(sample_ohlcv_data, swing_length=10)
    assert isinstance(res_smc, pd.DataFrame)
    assert "fvg" in res_smc.columns
    assert "fvg_top" in res_smc.columns
    assert "fvg_bottom" in res_smc.columns
    assert "fvg_mitigated" in res_smc.columns
    assert "swing_high_low" in res_smc.columns
    assert "swing_level" in res_smc.columns
    assert "bos" in res_smc.columns
    assert "choch" in res_smc.columns
    assert "structure_level" in res_smc.columns
    assert "structure_broken" in res_smc.columns

    # Test Hull Moving Average
    res_hma = hull_moving_average.calculate(sample_ohlcv_data, period=9)
    assert isinstance(res_hma, pd.Series)
    assert res_hma.name == "hma_9"


def test_indicator_validation_errors(sample_ohlcv_data):
    # Test column not found raise ValueError
    with pytest.raises(ValueError, match="Column 'non_existent' not found"):
        SMA().calculate(sample_ohlcv_data, column="non_existent")

    with pytest.raises(ValueError, match="Column 'non_existent' not found"):
        EMA().calculate(sample_ohlcv_data, column="non_existent")

    with pytest.raises(ValueError, match="Column 'non_existent' not found"):
        StandardDeviation().calculate(sample_ohlcv_data, column="non_existent")

    # Test period < 1 raise ValueError
    with pytest.raises(ValueError, match="Period must be greater than or equal to 1"):
        SMA().calculate(sample_ohlcv_data, period=0)

    with pytest.raises(ValueError, match="Period must be greater than or equal to 1"):
        EMA().calculate(sample_ohlcv_data, period=0)

    with pytest.raises(ValueError, match="Period must be greater than or equal to 1"):
        StandardDeviation().calculate(sample_ohlcv_data, period=0)


def test_base_indicator_helpers() -> None:
    from app.services.strategy.contracts import AccountSnapshot
    from app.services.indicators.base import (
        arithmetic_average,
        balance_scaled_volume,
        crossed_above,
        crossed_below,
        pips_to_price,
        weighted_average,
    )

    # Crossovers
    assert crossed_above(1.0, 1.0, 1.2, 1.1) is True
    assert crossed_above(1.0, 1.1, 1.0, 1.1) is False
    assert crossed_below(1.0, 1.0, 0.8, 0.9) is True
    assert crossed_below(1.0, 0.9, 1.0, 0.9) is False

    # Pips to price
    assert pips_to_price(10.0, 0.0001) == 0.01
    assert pips_to_price(10.0, 0.0001, 1.0) == 0.001

    # Scaling volume
    assert balance_scaled_volume(10000.0, 10000.0, 0.1, None) == 0.1

    # Scaling volume with AccountSnapshot bounds & steps
    acc = AccountSnapshot(
        balance=10000.0, volume_min=0.1, volume_max=5.0, volume_step=0.1
    )
    assert balance_scaled_volume(10000.0, 10000.0, 0.1, acc) == 0.1
    # Test min clamp
    assert balance_scaled_volume(1000.0, 10000.0, 0.1, acc) == 0.1
    # Test max clamp
    assert balance_scaled_volume(100000.0, 10000.0, 1.0, acc) == 5.0

    # Scaling volume validation exceptions
    with pytest.raises(
        ValueError, match="Balance and volume scaling inputs must be positive"
    ):
        balance_scaled_volume(10.0, -10.0, 0.1, None)
    with pytest.raises(
        ValueError, match="Balance and volume scaling inputs must be positive"
    ):
        balance_scaled_volume(10.0, 10.0, -0.1, None)

    # Arithmetic average
    assert arithmetic_average([1.0, 2.0, 3.0]) == 2.0
    with pytest.raises(ValueError, match="Cannot average an empty sequence"):
        arithmetic_average([])

    # Weighted average
    assert weighted_average([10.0, 20.0], [1.0, 3.0]) == 17.5
    with pytest.raises(
        ValueError, match="Weighted average requires non-empty aligned sequences"
    ):
        weighted_average([1.0], [1.0, 2.0])
    with pytest.raises(
        ValueError, match="Weighted average requires non-empty aligned sequences"
    ):
        weighted_average([], [])
    with pytest.raises(
        ValueError, match="Weighted average quantities must sum to a positive value"
    ):
        weighted_average([1.0, 2.0], [0.0, -1.0])
