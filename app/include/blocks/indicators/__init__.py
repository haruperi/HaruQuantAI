"""Canonical indicators, loaded individually on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.include.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    from app.include.blocks.indicators.momentum.bears_power import BearsPower
    from app.include.blocks.indicators.momentum.bulls_power import BullsPower
    from app.include.blocks.indicators.momentum.cci import CCI
    from app.include.blocks.indicators.momentum.demarker import DeMarker
    from app.include.blocks.indicators.momentum.laguerre_rsi import LaguerreRSI
    from app.include.blocks.indicators.momentum.macd import MACD
    from app.include.blocks.indicators.momentum.momentum import Momentum
    from app.include.blocks.indicators.momentum.osma import OSMA
    from app.include.blocks.indicators.momentum.price_velocity import PriceVelocity
    from app.include.blocks.indicators.momentum.qqe import QQE
    from app.include.blocks.indicators.momentum.reflex import Reflex
    from app.include.blocks.indicators.momentum.roc import ROC
    from app.include.blocks.indicators.momentum.rsi import RSI
    from app.include.blocks.indicators.momentum.schaff_trend_cycle import (
        SchaffTrendCycle,
    )
    from app.include.blocks.indicators.momentum.stochastic import Stochastic
    from app.include.blocks.indicators.momentum.wave_trend import WaveTrend
    from app.include.blocks.indicators.momentum.williams_pr import WilliamsPR
    from app.include.blocks.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )
    from app.include.blocks.indicators.price_action.chart_patterns import ChartPatterns
    from app.include.blocks.indicators.price_action.fibo import Fibo
    from app.include.blocks.indicators.price_action.fractal import Fractal
    from app.include.blocks.indicators.price_action.heiken_ashi import HeikenAshi
    from app.include.blocks.indicators.price_action.highest_lowest import HighestLowest
    from app.include.blocks.indicators.price_action.level_clustering import (
        LevelClustering,
    )
    from app.include.blocks.indicators.price_action.pivots import Pivots
    from app.include.blocks.indicators.price_action.price_gap import PriceGap
    from app.include.blocks.indicators.price_action.zigzag import ZigZag
    from app.include.blocks.indicators.regime.choppiness import ChoppinessIndex
    from app.include.blocks.indicators.regime.hurst import HurstExponent
    from app.include.blocks.indicators.regime.regime_resolver import (
        MarketRegimeResolver,
    )
    from app.include.blocks.indicators.trend.adx import ADX
    from app.include.blocks.indicators.trend.aroon import Aroon
    from app.include.blocks.indicators.trend.directional_index import DirectionalIndex
    from app.include.blocks.indicators.trend.donchian_channel import DonchianChannels
    from app.include.blocks.indicators.trend.ema import EMA
    from app.include.blocks.indicators.trend.gann_hi_lo import GannHiLo
    from app.include.blocks.indicators.trend.hull_moving_average import (
        HullMovingAverage,
    )
    from app.include.blocks.indicators.trend.ichimoku import Ichimoku
    from app.include.blocks.indicators.trend.kama import KAMA
    from app.include.blocks.indicators.trend.kaufman_efficiency_ratio import (
        KaufmanEfficiencyRatio,
    )
    from app.include.blocks.indicators.trend.lin_reg import LinReg
    from app.include.blocks.indicators.trend.lwma import LWMA
    from app.include.blocks.indicators.trend.parabolic_sar import ParabolicSAR
    from app.include.blocks.indicators.trend.sma import SMA
    from app.include.blocks.indicators.trend.smma import SMMA
    from app.include.blocks.indicators.trend.supertrend import SuperTrend
    from app.include.blocks.indicators.trend.tema import TEMA
    from app.include.blocks.indicators.trend.trend import Trend
    from app.include.blocks.indicators.trend.vortex import Vortex
    from app.include.blocks.indicators.volatility.adr import AverageDailyRange
    from app.include.blocks.indicators.volatility.amihud import AmihudIlliquidity
    from app.include.blocks.indicators.volatility.atr import ATR
    from app.include.blocks.indicators.volatility.bar_range import BarRange
    from app.include.blocks.indicators.volatility.bb_range import BBRange
    from app.include.blocks.indicators.volatility.bb_width_ratio import BBWidthRatio
    from app.include.blocks.indicators.volatility.biggest_range import BiggestRange
    from app.include.blocks.indicators.volatility.bollinger_bands import BollingerBands
    from app.include.blocks.indicators.volatility.garman_klass import (
        GarmanKlassVolatility,
    )
    from app.include.blocks.indicators.volatility.highest_in_range import HighestInRange
    from app.include.blocks.indicators.volatility.keltner_channel import KeltnerChannel
    from app.include.blocks.indicators.volatility.lowest_in_range import LowestInRange
    from app.include.blocks.indicators.volatility.mt_atr import MTATR
    from app.include.blocks.indicators.volatility.mt_keltner_channel import (
        MTKeltnerChannel,
    )
    from app.include.blocks.indicators.volatility.parkinson import ParkinsonVolatility
    from app.include.blocks.indicators.volatility.rogers_satchell import (
        RogersSatchellVolatility,
    )
    from app.include.blocks.indicators.volatility.smallest_range import SmallestRange
    from app.include.blocks.indicators.volatility.sr_percent_rank import SRPercentRank
    from app.include.blocks.indicators.volatility.std_dev import StdDev
    from app.include.blocks.indicators.volatility.true_range import TrueRange
    from app.include.blocks.indicators.volatility.ulcer_index import UlcerIndex
    from app.include.blocks.indicators.volume.aggressive_trade_imbalance import (
        AggressiveTradeImbalance,
    )
    from app.include.blocks.indicators.volume.anchored_vwap import AnchoredVWAP
    from app.include.blocks.indicators.volume.avg_volume import AvgVolume
    from app.include.blocks.indicators.volume.cmf import CMF
    from app.include.blocks.indicators.volume.cot import COT
    from app.include.blocks.indicators.volume.cumulative_volume_delta import (
        CumulativeVolumeDelta,
    )
    from app.include.blocks.indicators.volume.mfi import MFI
    from app.include.blocks.indicators.volume.obv import OBV
    from app.include.blocks.indicators.volume.tpo_profile import TPOProfile
    from app.include.blocks.indicators.volume.volume_profile import VolumeProfile
    from app.include.blocks.indicators.volume.vwap import VWAP

_EXPORTS = {
    "BiggestRange": "app.include.blocks.indicators.volatility.biggest_range",
    "SmallestRange": "app.include.blocks.indicators.volatility.smallest_range",
    "HighestInRange": "app.include.blocks.indicators.volatility.highest_in_range",
    "LowestInRange": "app.include.blocks.indicators.volatility.lowest_in_range",
    "BBRange": "app.include.blocks.indicators.volatility.bb_range",
    "BBWidthRatio": "app.include.blocks.indicators.volatility.bb_width_ratio",
    "ADX": "app.include.blocks.indicators.trend.adx",
    "ATR": "app.include.blocks.indicators.volatility.atr",
    ("AggressiveTradeImbalance"): (
        "app.include.blocks.indicators.volume.aggressive_trade_imbalance"
    ),
    "AmihudIlliquidity": "app.include.blocks.indicators.volatility.amihud",
    "AnchoredVWAP": "app.include.blocks.indicators.volume.anchored_vwap",
    "Aroon": "app.include.blocks.indicators.trend.aroon",
    "AverageDailyRange": "app.include.blocks.indicators.volatility.adr",
    "AvgVolume": "app.include.blocks.indicators.volume.avg_volume",
    "AwesomeOscillator": "app.include.blocks.indicators.momentum.awesome_oscillator",
    "BarRange": "app.include.blocks.indicators.volatility.bar_range",
    "BearsPower": "app.include.blocks.indicators.momentum.bears_power",
    "BollingerBands": "app.include.blocks.indicators.volatility.bollinger_bands",
    "BullsPower": "app.include.blocks.indicators.momentum.bulls_power",
    "CCI": "app.include.blocks.indicators.momentum.cci",
    "CMF": "app.include.blocks.indicators.volume.cmf",
    "COT": "app.include.blocks.indicators.volume.cot",
    ("CandlestickPatterns"): (
        "app.include.blocks.indicators.price_action.candlestick_patterns"
    ),
    "ChartPatterns": "app.include.blocks.indicators.price_action.chart_patterns",
    "ChoppinessIndex": "app.include.blocks.indicators.regime.choppiness",
    ("CumulativeVolumeDelta"): (
        "app.include.blocks.indicators.volume.cumulative_volume_delta"
    ),
    "DeMarker": "app.include.blocks.indicators.momentum.demarker",
    "DirectionalIndex": "app.include.blocks.indicators.trend.directional_index",
    "DonchianChannels": "app.include.blocks.indicators.trend.donchian_channel",
    "EMA": "app.include.blocks.indicators.trend.ema",
    "Fibo": "app.include.blocks.indicators.price_action.fibo",
    "Fractal": "app.include.blocks.indicators.price_action.fractal",
    "GannHiLo": "app.include.blocks.indicators.trend.gann_hi_lo",
    "GarmanKlassVolatility": "app.include.blocks.indicators.volatility.garman_klass",
    "HeikenAshi": "app.include.blocks.indicators.price_action.heiken_ashi",
    "HighestLowest": "app.include.blocks.indicators.price_action.highest_lowest",
    "HullMovingAverage": "app.include.blocks.indicators.trend.hull_moving_average",
    "HurstExponent": "app.include.blocks.indicators.regime.hurst",
    "Ichimoku": "app.include.blocks.indicators.trend.ichimoku",
    "KAMA": "app.include.blocks.indicators.trend.kama",
    ("KaufmanEfficiencyRatio"): (
        "app.include.blocks.indicators.trend.kaufman_efficiency_ratio"
    ),
    "KeltnerChannel": "app.include.blocks.indicators.volatility.keltner_channel",
    "LWMA": "app.include.blocks.indicators.trend.lwma",
    "LaguerreRSI": "app.include.blocks.indicators.momentum.laguerre_rsi",
    "LevelClustering": "app.include.blocks.indicators.price_action.level_clustering",
    "LinReg": "app.include.blocks.indicators.trend.lin_reg",
    "MACD": "app.include.blocks.indicators.momentum.macd",
    "MFI": "app.include.blocks.indicators.volume.mfi",
    "MTATR": "app.include.blocks.indicators.volatility.mt_atr",
    "MTKeltnerChannel": "app.include.blocks.indicators.volatility.mt_keltner_channel",
    "MarketRegimeResolver": "app.include.blocks.indicators.regime.regime_resolver",
    "Momentum": "app.include.blocks.indicators.momentum.momentum",
    "OBV": "app.include.blocks.indicators.volume.obv",
    "OSMA": "app.include.blocks.indicators.momentum.osma",
    "ParabolicSAR": "app.include.blocks.indicators.trend.parabolic_sar",
    "ParkinsonVolatility": "app.include.blocks.indicators.volatility.parkinson",
    "Pivots": "app.include.blocks.indicators.price_action.pivots",
    "PriceGap": "app.include.blocks.indicators.price_action.price_gap",
    "PriceVelocity": "app.include.blocks.indicators.momentum.price_velocity",
    "QQE": "app.include.blocks.indicators.momentum.qqe",
    "ROC": "app.include.blocks.indicators.momentum.roc",
    "RSI": "app.include.blocks.indicators.momentum.rsi",
    "Reflex": "app.include.blocks.indicators.momentum.reflex",
    ("RogersSatchellVolatility"): (
        "app.include.blocks.indicators.volatility.rogers_satchell"
    ),
    "SMA": "app.include.blocks.indicators.trend.sma",
    "SMMA": "app.include.blocks.indicators.trend.smma",
    "SRPercentRank": "app.include.blocks.indicators.volatility.sr_percent_rank",
    "SchaffTrendCycle": "app.include.blocks.indicators.momentum.schaff_trend_cycle",
    "StdDev": "app.include.blocks.indicators.volatility.std_dev",
    "Stochastic": "app.include.blocks.indicators.momentum.stochastic",
    "SuperTrend": "app.include.blocks.indicators.trend.supertrend",
    "TEMA": "app.include.blocks.indicators.trend.tema",
    "TPOProfile": "app.include.blocks.indicators.volume.tpo_profile",
    "Trend": "app.include.blocks.indicators.trend.trend",
    "TrueRange": "app.include.blocks.indicators.volatility.true_range",
    "UlcerIndex": "app.include.blocks.indicators.volatility.ulcer_index",
    "VWAP": "app.include.blocks.indicators.volume.vwap",
    "VolumeProfile": "app.include.blocks.indicators.volume.volume_profile",
    "Vortex": "app.include.blocks.indicators.trend.vortex",
    "WaveTrend": "app.include.blocks.indicators.momentum.wave_trend",
    "WilliamsPR": "app.include.blocks.indicators.momentum.williams_pr",
    "ZigZag": "app.include.blocks.indicators.price_action.zigzag",
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
