"""Top-level indicators package unifying all canonical indicator families."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    from app.extend.blocks.indicators.momentum.bears_power import BearsPower
    from app.extend.blocks.indicators.momentum.bulls_power import BullsPower
    from app.extend.blocks.indicators.momentum.cci import CCI
    from app.extend.blocks.indicators.momentum.demarker import DeMarker
    from app.extend.blocks.indicators.momentum.laguerre_rsi import LaguerreRSI
    from app.extend.blocks.indicators.momentum.macd import MACD
    from app.extend.blocks.indicators.momentum.momentum import Momentum
    from app.extend.blocks.indicators.momentum.osma import OSMA
    from app.extend.blocks.indicators.momentum.price_velocity import PriceVelocity
    from app.extend.blocks.indicators.momentum.qqe import QQE
    from app.extend.blocks.indicators.momentum.reflex import Reflex
    from app.extend.blocks.indicators.momentum.roc import ROC
    from app.extend.blocks.indicators.momentum.rsi import RSI
    from app.extend.blocks.indicators.momentum.schaff_trend_cycle import (
        SchaffTrendCycle,
    )
    from app.extend.blocks.indicators.momentum.stochastic import Stochastic
    from app.extend.blocks.indicators.momentum.wave_trend import WaveTrend
    from app.extend.blocks.indicators.momentum.williams_pr import WilliamsPR
    from app.extend.blocks.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )
    from app.extend.blocks.indicators.price_action.chart_patterns import ChartPatterns
    from app.extend.blocks.indicators.price_action.fibo import Fibo
    from app.extend.blocks.indicators.price_action.fractal import Fractal
    from app.extend.blocks.indicators.price_action.heiken_ashi import HeikenAshi
    from app.extend.blocks.indicators.price_action.highest_lowest import HighestLowest
    from app.extend.blocks.indicators.price_action.level_clustering import (
        LevelClustering,
    )
    from app.extend.blocks.indicators.price_action.pivots import Pivots
    from app.extend.blocks.indicators.price_action.price_gap import PriceGap
    from app.extend.blocks.indicators.price_action.zigzag import ZigZag
    from app.extend.blocks.indicators.regime.choppiness import ChoppinessIndex
    from app.extend.blocks.indicators.regime.hurst import HurstExponent
    from app.extend.blocks.indicators.regime.regime_resolver import (
        MarketRegimeResolver,
    )
    from app.extend.blocks.indicators.trend.adx import ADX
    from app.extend.blocks.indicators.trend.aroon import Aroon
    from app.extend.blocks.indicators.trend.directional_index import DirectionalIndex
    from app.extend.blocks.indicators.trend.donchian_channel import DonchianChannels
    from app.extend.blocks.indicators.trend.ema import EMA
    from app.extend.blocks.indicators.trend.gann_hi_lo import GannHiLo
    from app.extend.blocks.indicators.trend.hull_moving_average import (
        HullMovingAverage,
    )
    from app.extend.blocks.indicators.trend.ichimoku import Ichimoku
    from app.extend.blocks.indicators.trend.kama import KAMA
    from app.extend.blocks.indicators.trend.kaufman_efficiency_ratio import (
        KaufmanEfficiencyRatio,
    )
    from app.extend.blocks.indicators.trend.lin_reg import LinReg
    from app.extend.blocks.indicators.trend.lwma import LWMA
    from app.extend.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    from app.extend.blocks.indicators.trend.sma import SMA
    from app.extend.blocks.indicators.trend.smma import SMMA
    from app.extend.blocks.indicators.trend.supertrend import SuperTrend
    from app.extend.blocks.indicators.trend.tema import TEMA
    from app.extend.blocks.indicators.trend.trend import Trend
    from app.extend.blocks.indicators.trend.vortex import Vortex
    from app.extend.blocks.indicators.volatility.adr import AverageDailyRange
    from app.extend.blocks.indicators.volatility.amihud import AmihudIlliquidity
    from app.extend.blocks.indicators.volatility.atr import ATR
    from app.extend.blocks.indicators.volatility.bar_range import BarRange
    from app.extend.blocks.indicators.volatility.bb_range import BBRange
    from app.extend.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
    from app.extend.blocks.indicators.volatility.biggest_range import BiggestRange
    from app.extend.blocks.indicators.volatility.bollinger_bands import BollingerBands
    from app.extend.blocks.indicators.volatility.garman_klass import (
        GarmanKlassVolatility,
    )
    from app.extend.blocks.indicators.volatility.highest_in_range import HighestInRange
    from app.extend.blocks.indicators.volatility.keltner_channel import KeltnerChannel
    from app.extend.blocks.indicators.volatility.lowest_in_range import LowestInRange
    from app.extend.blocks.indicators.volatility.mt_atr import MTATR
    from app.extend.blocks.indicators.volatility.mt_keltner_channel import (
        MTKeltnerChannel,
    )
    from app.extend.blocks.indicators.volatility.parkinson import ParkinsonVolatility
    from app.extend.blocks.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )
    from app.extend.blocks.indicators.volatility.smallest_range import SmallestRange
    from app.extend.blocks.indicators.volatility.sr_percent_rank import SRPercentRank
    from app.extend.blocks.indicators.volatility.std_dev import StdDev
    from app.extend.blocks.indicators.volatility.true_range import TrueRange
    from app.extend.blocks.indicators.volatility.ulcer_index import UlcerIndex
    from app.extend.blocks.indicators.volume.aggressive_trade_imbalance import (
        AggressiveTradeImbalance,
    )
    from app.extend.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    from app.extend.blocks.indicators.volume.avg_volume import AvgVolume
    from app.extend.blocks.indicators.volume.cmf import CMF
    from app.extend.blocks.indicators.volume.cot import COT
    from app.extend.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    from app.extend.blocks.indicators.volume.mfi import MFI
    from app.extend.blocks.indicators.volume.obv import OBV
    from app.extend.blocks.indicators.volume.tpo_profile import TPOProfile
    from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
    from app.extend.blocks.indicators.volume.vwap import VWAP

_EXPORTS = {
    "BiggestRange": "app.extend.blocks.indicators.volatility.biggest_range",
    "SmallestRange": "app.extend.blocks.indicators.volatility.smallest_range",
    "HighestInRange": "app.extend.blocks.indicators.volatility.highest_in_range",
    "LowestInRange": "app.extend.blocks.indicators.volatility.lowest_in_range",
    "BBRange": "app.extend.blocks.indicators.volatility.bb_range",
    "BBWidthRatio": "app.extend.blocks.indicators.volatility.bb_width_ratio",
    "ADX": "app.extend.blocks.indicators.trend.adx",
    "ATR": "app.extend.blocks.indicators.volatility.atr",
    ("AggressiveTradeImbalance"): (
        "app.extend.blocks.indicators.volume.aggressive_trade_imbalance"
    ),
    "AmihudIlliquidity": "app.extend.blocks.indicators.volatility.amihud",
    "AnchoredVWAP": "app.extend.blocks.indicators.volume.anchored_vwap",
    "Aroon": "app.extend.blocks.indicators.trend.aroon",
    "AverageDailyRange": "app.extend.blocks.indicators.volatility.adr",
    "AvgVolume": "app.extend.blocks.indicators.volume.avg_volume",
    "AwesomeOscillator": "app.extend.blocks.indicators.momentum.awesome_oscillator",
    "BarRange": "app.extend.blocks.indicators.volatility.bar_range",
    "BearsPower": "app.extend.blocks.indicators.momentum.bears_power",
    "BollingerBands": "app.extend.blocks.indicators.volatility.bollinger_bands",
    "BullsPower": "app.extend.blocks.indicators.momentum.bulls_power",
    "CCI": "app.extend.blocks.indicators.momentum.cci",
    "CMF": "app.extend.blocks.indicators.volume.cmf",
    "COT": "app.extend.blocks.indicators.volume.cot",
    ("CandlestickPatterns"): (
        "app.extend.blocks.indicators.price_action.candlestick_patterns"
    ),
    "ChartPatterns": "app.extend.blocks.indicators.price_action.chart_patterns",
    "ChoppinessIndex": "app.extend.blocks.indicators.regime.choppiness",
    ("CumulativeVolumeDelta"): (
        "app.extend.blocks.indicators.volume.cumulative_volume_delta"
    ),
    "DeMarker": "app.extend.blocks.indicators.momentum.demarker",
    "DirectionalIndex": "app.extend.blocks.indicators.trend.directional_index",
    "DonchianChannels": "app.extend.blocks.indicators.trend.donchian_channel",
    "EMA": "app.extend.blocks.indicators.trend.ema",
    "Fibo": "app.extend.blocks.indicators.price_action.fibo",
    "Fractal": "app.extend.blocks.indicators.price_action.fractal",
    "GannHiLo": "app.extend.blocks.indicators.trend.gann_hi_lo",
    "GarmanKlassVolatility": "app.extend.blocks.indicators.volatility.garman_klass",
    "HeikenAshi": "app.extend.blocks.indicators.price_action.heiken_ashi",
    "HighestLowest": "app.extend.blocks.indicators.price_action.highest_lowest",
    "HullMovingAverage": "app.extend.blocks.indicators.trend.hull_moving_average",
    "HurstExponent": "app.extend.blocks.indicators.regime.hurst",
    "Ichimoku": "app.extend.blocks.indicators.trend.ichimoku",
    "KAMA": "app.extend.blocks.indicators.trend.kama",
    ("KaufmanEfficiencyRatio"): (
        "app.extend.blocks.indicators.trend.kaufman_efficiency_ratio"
    ),
    "KeltnerChannel": "app.extend.blocks.indicators.volatility.keltner_channel",
    "LWMA": "app.extend.blocks.indicators.trend.lwma",
    "LaguerreRSI": "app.extend.blocks.indicators.momentum.laguerre_rsi",
    "LevelClustering": "app.extend.blocks.indicators.price_action.level_clustering",
    "LinReg": "app.extend.blocks.indicators.trend.lin_reg",
    "MACD": "app.extend.blocks.indicators.momentum.macd",
    "MFI": "app.extend.blocks.indicators.volume.mfi",
    "MTATR": "app.extend.blocks.indicators.volatility.mt_atr",
    "MTKeltnerChannel": "app.extend.blocks.indicators.volatility.mt_keltner_channel",
    "MarketRegimeResolver": "app.extend.blocks.indicators.regime.regime_resolver",
    "Momentum": "app.extend.blocks.indicators.momentum.momentum",
    "OBV": "app.extend.blocks.indicators.volume.obv",
    "OSMA": "app.extend.blocks.indicators.momentum.osma",
    "ParabolicSAR": "app.extend.blocks.indicators.trend.parabolic_sar",
    "ParkinsonVolatility": "app.extend.blocks.indicators.volatility.parkinson",
    "Pivots": "app.extend.blocks.indicators.price_action.pivots",
    "PriceGap": "app.extend.blocks.indicators.price_action.price_gap",
    "PriceVelocity": "app.extend.blocks.indicators.momentum.price_velocity",
    "QQE": "app.extend.blocks.indicators.momentum.qqe",
    "ROC": "app.extend.blocks.indicators.momentum.roc",
    "RSI": "app.extend.blocks.indicators.momentum.rsi",
    "Reflex": "app.extend.blocks.indicators.momentum.reflex",
    ("RogersSatchellVolatility"): (
        "app.extend.blocks.indicators.volatility.rogers_satchell"
    ),
    "SMA": "app.extend.blocks.indicators.trend.sma",
    "SMMA": "app.extend.blocks.indicators.trend.smma",
    "SRPercentRank": "app.extend.blocks.indicators.volatility.sr_percent_rank",
    "SchaffTrendCycle": "app.extend.blocks.indicators.momentum.schaff_trend_cycle",
    "StdDev": "app.extend.blocks.indicators.volatility.std_dev",
    "Stochastic": "app.extend.blocks.indicators.momentum.stochastic",
    "SuperTrend": "app.extend.blocks.indicators.trend.supertrend",
    "TEMA": "app.extend.blocks.indicators.trend.tema",
    "TPOProfile": "app.extend.blocks.indicators.volume.tpo_profile",
    "Trend": "app.extend.blocks.indicators.trend.trend",
    "TrueRange": "app.extend.blocks.indicators.volatility.true_range",
    "UlcerIndex": "app.extend.blocks.indicators.volatility.ulcer_index",
    "VWAP": "app.extend.blocks.indicators.volume.vwap",
    "VolumeProfile": "app.extend.blocks.indicators.volume.volume_profile",
    "Vortex": "app.extend.blocks.indicators.trend.vortex",
    "WaveTrend": "app.extend.blocks.indicators.momentum.wave_trend",
    "WilliamsPR": "app.extend.blocks.indicators.momentum.williams_pr",
    "ZigZag": "app.extend.blocks.indicators.price_action.zigzag",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "ADX",
    "ATR",
    "CCI",
    "CMF",
    "COT",
    "EMA",
    "KAMA",
    "LWMA",
    "MACD",
    "MFI",
    "MTATR",
    "OBV",
    "OSMA",
    "QQE",
    "ROC",
    "RSI",
    "SMA",
    "SMMA",
    "TEMA",
    "VWAP",
    "AggressiveTradeImbalance",
    "AmihudIlliquidity",
    "AnchoredVWAP",
    "Aroon",
    "AverageDailyRange",
    "AvgVolume",
    "AwesomeOscillator",
    "BBRange",
    "BBWidthRatio",
    "BarRange",
    "BearsPower",
    "BiggestRange",
    "BollingerBands",
    "BullsPower",
    "CandlestickPatterns",
    "ChartPatterns",
    "ChoppinessIndex",
    "CumulativeVolumeDelta",
    "DeMarker",
    "DirectionalIndex",
    "DonchianChannels",
    "Fibo",
    "Fractal",
    "GannHiLo",
    "GarmanKlassVolatility",
    "HeikenAshi",
    "HighestInRange",
    "HighestLowest",
    "HullMovingAverage",
    "HurstExponent",
    "Ichimoku",
    "KaufmanEfficiencyRatio",
    "KeltnerChannel",
    "LaguerreRSI",
    "LevelClustering",
    "LinReg",
    "LowestInRange",
    "MTKeltnerChannel",
    "MarketRegimeResolver",
    "Momentum",
    "ParabolicSAR",
    "ParkinsonVolatility",
    "Pivots",
    "PriceGap",
    "PriceVelocity",
    "Reflex",
    "RogersSatchellVolatility",
    "SRPercentRank",
    "SchaffTrendCycle",
    "SmallestRange",
    "StdDev",
    "Stochastic",
    "SuperTrend",
    "TPOProfile",
    "Trend",
    "TrueRange",
    "UlcerIndex",
    "VolumeProfile",
    "Vortex",
    "WaveTrend",
    "WilliamsPR",
    "ZigZag",
]
