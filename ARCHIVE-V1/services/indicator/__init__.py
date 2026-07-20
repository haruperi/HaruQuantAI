"""Indicator service tool exports.

Purpose:
    Expose deterministic, agent-facing indicator tools from focused indicator
    modules without placing implementation logic in this package initializer.

Classes and functions:
    None: This module only imports and exports functions implemented elsewhere.
"""

from __future__ import annotations

# _common.py tools
from app.services.indicator._common import indicator, list_indicators, run_indicators

# custom/currency_strength.py tools
from app.services.indicator.custom.currency_strength import (
    calculate_currency_strength,
    calculate_pair_strength,
    currency_strength_indicator,
    get_top_pairs,
)

# custom/smc.py tools
from app.services.indicator.custom.smc import (
    bos_choch,
    fvg,
    ob,
    previous_high_low,
    swing_highs_lows,
)

# momentum/*.py tools
from app.services.indicator.momentum.rsi import rsi

# statistical/*.py tools
from app.services.indicator.statistical.hurst import calculate_hurst, hurst

# trend/*.py tools
from app.services.indicator.trend.ema import ema
from app.services.indicator.trend.sma import sma
from app.services.indicator.trend.wma import wma

# volatility/*.py tools
from app.services.indicator.volatility.atr import atr
from app.services.indicator.volatility.bbands import bbands

# volume/*.py tools
from app.services.indicator.volume.accumulation_distribution import (
    accumulation_distribution,
)
from app.services.utils.logger import logger
from app.services.utils.standard import standardize_domain_exports

phl = previous_high_low

__all__ = [
    # _common.py tools
    "indicator",
    "list_indicators",
    "run_indicators",
    # trend/*.py tools
    "ema",
    "sma",
    "wma",
    # momentum/*.py tools
    "rsi",
    # volatility/*.py tools
    "atr",
    "bbands",
    # volume/*.py tools
    "accumulation_distribution",
    # statistical/*.py tools
    "calculate_hurst",
    "hurst",
    # custom/currency_strength.py tools
    "calculate_currency_strength",
    "calculate_pair_strength",
    "currency_strength_indicator",
    "get_top_pairs",
    # custom/smc.py tools
    "bos_choch",
    "fvg",
    "ob",
    "previous_high_low",
    "phl",
    "swing_highs_lows",
]


standardize_domain_exports(globals(), __all__, tool_category="indicator")
