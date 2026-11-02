"""Momentum indicator package exports and lazy loading registry.

Description:
    Momentum indicator package exports and lazy loading registry.
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative momentum indicator library.
Key Capabilities:
    - FR-indicator-momentum: Momentum indicator exports.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.momentum import RSI, MACD, StochRSI
CLI Usage:
    uv run pytest tests/extend/blocks/test_tradingview_indicators.py --no-cov
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.extend.blocks.indicators.momentum.accelerator_oscillator import (
        AcceleratorOscillator,
    )
    from app.extend.blocks.indicators.momentum.awesome_oscillator import (
        AwesomeOscillator,
    )
    from app.extend.blocks.indicators.momentum.balance_of_power import (
        BalanceOfPower,
    )
    from app.extend.blocks.indicators.momentum.bears_power import BearsPower
    from app.extend.blocks.indicators.momentum.bulls_power import BullsPower
    from app.extend.blocks.indicators.momentum.cci import CCI
    from app.extend.blocks.indicators.momentum.chande_momentum_oscillator import (
        ChandeMomentumOscillator,
    )
    from app.extend.blocks.indicators.momentum.connors_rsi import ConnorsRSI
    from app.extend.blocks.indicators.momentum.coppock_curve import CoppockCurve
    from app.extend.blocks.indicators.momentum.demarker import DeMarker
    from app.extend.blocks.indicators.momentum.detrended_price_oscillator import (
        DetrendedPriceOscillator,
    )
    from app.extend.blocks.indicators.momentum.fisher_transform import (
        FisherTransform,
    )
    from app.extend.blocks.indicators.momentum.know_sure_thing import (
        KnowSureThing,
    )
    from app.extend.blocks.indicators.momentum.laguerre_rsi import LaguerreRSI
    from app.extend.blocks.indicators.momentum.macd import MACD
    from app.extend.blocks.indicators.momentum.momentum import Momentum
    from app.extend.blocks.indicators.momentum.osma import OSMA
    from app.extend.blocks.indicators.momentum.price_oscillator import (
        PercentagePriceOscillator,
    )
    from app.extend.blocks.indicators.momentum.price_velocity import (
        PriceVelocity,
    )
    from app.extend.blocks.indicators.momentum.qqe import QQE
    from app.extend.blocks.indicators.momentum.rank_correlation_index import (
        RankCorrelationIndex,
    )
    from app.extend.blocks.indicators.momentum.reflex import Reflex
    from app.extend.blocks.indicators.momentum.relative_vigor_index import (
        RelativeVigorIndex,
    )
    from app.extend.blocks.indicators.momentum.roc import ROC
    from app.extend.blocks.indicators.momentum.rsi import RSI
    from app.extend.blocks.indicators.momentum.schaff_trend_cycle import (
        SchaffTrendCycle,
    )
    from app.extend.blocks.indicators.momentum.smi_ergodic import SMIErgodic
    from app.extend.blocks.indicators.momentum.stochastic import Stochastic
    from app.extend.blocks.indicators.momentum.stochastic_rsi import (
        StochasticRSI,
    )
    from app.extend.blocks.indicators.momentum.trix import TRIX
    from app.extend.blocks.indicators.momentum.true_strength_indicator import (
        TrueStrengthIndicator,
    )
    from app.extend.blocks.indicators.momentum.ultimate_oscillator import (
        UltimateOscillator,
    )
    from app.extend.blocks.indicators.momentum.wave_trend import WaveTrend
    from app.extend.blocks.indicators.momentum.williams_pr import WilliamsPR

_EXPORTS: dict[str, str] = {
    ("AcceleratorOscillator"): (
        "app.extend.blocks.indicators.momentum.accelerator_oscillator"
    ),
    "AwesomeOscillator": ("app.extend.blocks.indicators.momentum.awesome_oscillator"),
    "BalanceOfPower": ("app.extend.blocks.indicators.momentum.balance_of_power"),
    "BearsPower": "app.extend.blocks.indicators.momentum.bears_power",
    "BullsPower": "app.extend.blocks.indicators.momentum.bulls_power",
    "CCI": "app.extend.blocks.indicators.momentum.cci",
    ("ChandeMomentumOscillator"): (
        "app.extend.blocks.indicators.momentum.chande_momentum_oscillator"
    ),
    "ConnorsRSI": "app.extend.blocks.indicators.momentum.connors_rsi",
    "CoppockCurve": "app.extend.blocks.indicators.momentum.coppock_curve",
    "DeMarker": "app.extend.blocks.indicators.momentum.demarker",
    ("DetrendedPriceOscillator"): (
        "app.extend.blocks.indicators.momentum.detrended_price_oscillator"
    ),
    "FisherTransform": ("app.extend.blocks.indicators.momentum.fisher_transform"),
    "KnowSureThing": "app.extend.blocks.indicators.momentum.know_sure_thing",
    "LaguerreRSI": "app.extend.blocks.indicators.momentum.laguerre_rsi",
    "MACD": "app.extend.blocks.indicators.momentum.macd",
    "Momentum": "app.extend.blocks.indicators.momentum.momentum",
    "OSMA": "app.extend.blocks.indicators.momentum.osma",
    ("PercentagePriceOscillator"): (
        "app.extend.blocks.indicators.momentum.price_oscillator"
    ),
    "PriceVelocity": "app.extend.blocks.indicators.momentum.price_velocity",
    "QQE": "app.extend.blocks.indicators.momentum.qqe",
    "ROC": "app.extend.blocks.indicators.momentum.roc",
    "RSI": "app.extend.blocks.indicators.momentum.rsi",
    ("RankCorrelationIndex"): (
        "app.extend.blocks.indicators.momentum.rank_correlation_index"
    ),
    "Reflex": "app.extend.blocks.indicators.momentum.reflex",
    ("RelativeVigorIndex"): (
        "app.extend.blocks.indicators.momentum.relative_vigor_index"
    ),
    "SMIErgodic": "app.extend.blocks.indicators.momentum.smi_ergodic",
    ("SchaffTrendCycle"): ("app.extend.blocks.indicators.momentum.schaff_trend_cycle"),
    "Stochastic": "app.extend.blocks.indicators.momentum.stochastic",
    "StochasticRSI": "app.extend.blocks.indicators.momentum.stochastic_rsi",
    "TRIX": "app.extend.blocks.indicators.momentum.trix",
    ("TrueStrengthIndicator"): (
        "app.extend.blocks.indicators.momentum.true_strength_indicator"
    ),
    ("UltimateOscillator"): (
        "app.extend.blocks.indicators.momentum.ultimate_oscillator"
    ),
    "WaveTrend": "app.extend.blocks.indicators.momentum.wave_trend",
    "WilliamsPR": "app.extend.blocks.indicators.momentum.williams_pr",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


__all__ = [
    "CCI",
    "MACD",
    "OSMA",
    "QQE",
    "ROC",
    "RSI",
    "TRIX",
    "AcceleratorOscillator",
    "AwesomeOscillator",
    "BalanceOfPower",
    "BearsPower",
    "BullsPower",
    "ChandeMomentumOscillator",
    "ConnorsRSI",
    "CoppockCurve",
    "DeMarker",
    "DetrendedPriceOscillator",
    "FisherTransform",
    "KnowSureThing",
    "LaguerreRSI",
    "Momentum",
    "PercentagePriceOscillator",
    "PriceVelocity",
    "RankCorrelationIndex",
    "Reflex",
    "RelativeVigorIndex",
    "SMIErgodic",
    "SchaffTrendCycle",
    "Stochastic",
    "StochasticRSI",
    "TrueStrengthIndicator",
    "UltimateOscillator",
    "WaveTrend",
    "WilliamsPR",
]
