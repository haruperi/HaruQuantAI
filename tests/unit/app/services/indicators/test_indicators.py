import pytest
import pandas as pd
import numpy as np
from app.services.indicators.base import BaseIndicator
from app.services.indicators.trend.ema import EMA
from app.services.indicators.trend.sma import SMA
from app.services.indicators.trend.wma import WMA
from app.services.indicators.trend.bollinger_bands import BollingerBands
from app.services.indicators.momentum.rsi import RSI
from app.services.indicators.momentum.macd import MACD
from app.services.indicators.momentum.will_r import WilliamsR
from app.services.indicators.volume.obv import OBV
from app.services.indicators.volume.mfi import MFI
from app.services.indicators.volume.cmf import CMF
from app.services.indicators.volume.price_volume_distribution import PriceVolumeDistribution
from app.services.indicators.volatility.atr import ATR
from app.services.indicators.volatility.standard_deviation import StandardDeviation
from app.services.indicators.candles.engulfing import Engulfing
from app.services.indicators.candles.pinbar import Pinbar
from app.services.indicators.candles.doji import Doji
from app.services.indicators.candles.inside_bar import InsideBar
from app.services.indicators.custom.smc import SMC
from app.services.indicators.custom.hull_moving_average import HullMovingAverage

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
    
    df = pd.DataFrame({
        "open": open_val,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    }, index=dates)
    return df

def test_base_inheritance():
    # Verify all indicators inherit from BaseIndicator
    indicators = [
        EMA(), SMA(), WMA(), BollingerBands(),
        RSI(), MACD(), WilliamsR(),
        OBV(), MFI(), CMF(), PriceVolumeDistribution(),
        ATR(), StandardDeviation(),
        Engulfing(), Pinbar(), Doji(), InsideBar(),
        SMC(), HullMovingAverage()
    ]
    for ind in indicators:
        assert isinstance(ind, BaseIndicator)

def test_trend_indicators(sample_ohlcv_data):
    # Test EMA
    ema = EMA()
    df_ema = ema.calculate(sample_ohlcv_data, period=10)
    assert "ema_10" in df_ema.columns
    assert len(df_ema) == len(sample_ohlcv_data)
    
    # Test SMA
    sma = SMA()
    df_sma = sma.calculate(sample_ohlcv_data, period=10)
    assert "sma_10" in df_sma.columns
    
    # Test WMA
    wma = WMA()
    df_wma = wma.calculate(sample_ohlcv_data, period=10)
    assert "wma_10" in df_wma.columns
    
    # Test Bollinger Bands
    bb = BollingerBands()
    df_bb = bb.calculate(sample_ohlcv_data, period=20, std_dev=2.0)
    assert "bb_middle_20" in df_bb.columns
    assert "bb_upper_20_2.0" in df_bb.columns
    assert "bb_lower_20_2.0" in df_bb.columns

def test_momentum_indicators(sample_ohlcv_data):
    # Test RSI
    rsi = RSI()
    df_rsi = rsi.calculate(sample_ohlcv_data, period=14)
    assert "rsi_14" in df_rsi.columns
    
    # Test MACD
    macd = MACD()
    df_macd = macd.calculate(sample_ohlcv_data, fast_period=12, slow_period=26, signal_period=9)
    assert "macd_12_26" in df_macd.columns
    assert "macd_signal_12_26_9" in df_macd.columns
    assert "macd_hist_12_26_9" in df_macd.columns
    
    # Test Williams %R
    will_r = WilliamsR()
    df_wr = will_r.calculate(sample_ohlcv_data, period=14)
    assert "will_r_14" in df_wr.columns

def test_volume_indicators(sample_ohlcv_data):
    # Test OBV
    obv = OBV()
    df_obv = obv.calculate(sample_ohlcv_data)
    assert "obv" in df_obv.columns
    
    # Test MFI
    mfi = MFI()
    df_mfi = mfi.calculate(sample_ohlcv_data, period=14)
    assert "mfi_14" in df_mfi.columns
    
    # Test CMF
    cmf = CMF()
    df_cmf = cmf.calculate(sample_ohlcv_data, period=20)
    assert "cmf_20" in df_cmf.columns
    
    # Test Price Volume Distribution
    pvd = PriceVolumeDistribution()
    df_pvd = pvd.calculate(sample_ohlcv_data, period=20, bins=10)
    assert "pvd_poc_20" in df_pvd.columns

def test_volatility_indicators(sample_ohlcv_data):
    # Test ATR
    atr = ATR()
    df_atr = atr.calculate(sample_ohlcv_data, period=14)
    assert "atr_14" in df_atr.columns
    
    # Test Standard Deviation
    std = StandardDeviation()
    df_std = std.calculate(sample_ohlcv_data, period=20)
    assert "std_20" in df_std.columns

def test_candles_indicators(sample_ohlcv_data):
    # Test Engulfing
    eng = Engulfing()
    df_eng = eng.calculate(sample_ohlcv_data)
    assert "candle_engulfing" in df_eng.columns
    assert set(df_eng["candle_engulfing"].unique()).issubset({-1, 0, 1})
    
    # Test Pinbar
    pb = Pinbar()
    df_pb = pb.calculate(sample_ohlcv_data)
    assert "candle_pinbar" in df_pb.columns
    assert set(df_pb["candle_pinbar"].unique()).issubset({-1, 0, 1})
    
    # Test Doji
    doji = Doji()
    df_doji = doji.calculate(sample_ohlcv_data, threshold=0.1)
    assert "candle_doji" in df_doji.columns
    assert set(df_doji["candle_doji"].unique()).issubset({0, 1})
    
    # Test Inside Bar
    ib = InsideBar()
    df_ib = ib.calculate(sample_ohlcv_data)
    assert "candle_inside_bar" in df_ib.columns
    assert set(df_ib["candle_inside_bar"].unique()).issubset({0, 1})

def test_custom_indicators(sample_ohlcv_data):
    # Test SMC
    smc = SMC()
    df_smc = smc.calculate(sample_ohlcv_data, swing_length=10)
    assert "fvg" in df_smc.columns
    assert "fvg_top" in df_smc.columns
    assert "fvg_bottom" in df_smc.columns
    assert "fvg_mitigated" in df_smc.columns
    assert "swing_high_low" in df_smc.columns
    assert "swing_level" in df_smc.columns
    assert "bos" in df_smc.columns
    assert "choch" in df_smc.columns
    assert "structure_level" in df_smc.columns
    assert "structure_broken" in df_smc.columns
    
    # Test Hull Moving Average
    hma = HullMovingAverage()
    df_hma = hma.calculate(sample_ohlcv_data, period=9)
    assert "hma_9" in df_hma.columns


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

