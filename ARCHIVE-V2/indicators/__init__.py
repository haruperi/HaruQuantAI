"""Technical indicators and helper functions module."""

from app.services.indicators.base import (
    BaseIndicator,
    arithmetic_average,
    balance_scaled_volume,
    crossed_above,
    crossed_below,
    pips_to_price,
    weighted_average,
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

# Singletons (instantiated behind the scenes)
atr = ATR()
cmf = CMF()
ema = EMA()
macd = MACD()
mfi = MFI()
obv = OBV()
rsi = RSI()
sma = SMA()
smc = SMC()
wma = WMA()
bollinger_bands = BollingerBands()
doji = Doji()
engulfing = Engulfing()
hull_moving_average = HullMovingAverage()
inside_bar = InsideBar()
pinbar = Pinbar()
price_volume_distribution = PriceVolumeDistribution()
standard_deviation = StandardDeviation()
williams_r = WilliamsR()

__all__ = [
    "BaseIndicator",
    # Singletons
    "atr",
    "cmf",
    "ema",
    "macd",
    "mfi",
    "obv",
    "rsi",
    "sma",
    "smc",
    "wma",
    "bollinger_bands",
    "doji",
    "engulfing",
    "hull_moving_average",
    "inside_bar",
    "pinbar",
    "price_volume_distribution",
    "standard_deviation",
    "williams_r",
    # Helpers
    "arithmetic_average",
    "balance_scaled_volume",
    "crossed_above",
    "crossed_below",
    "pips_to_price",
    "weighted_average",
]
