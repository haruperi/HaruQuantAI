"""
Indicators tools exposed to HaruQuantAI agents.

This package exposes approved, deterministic, read-only indicator AI Tools.
Only functions imported and listed in ``__all__`` are official AI Tools for the
``tools.indicators`` domain.

The package initializer contains no business logic. Implementations live in
focused modules.
"""

# custom/currency_strength.py tools
from tools.indicators.custom.currency_strength import (
    calculate_currency_strength,
    calculate_pair_strength,
    currency_strength_indicator,
    get_top_pairs,
)

# custom/smc.py tools
from tools.indicators.custom.smc import (
    bos_choch,
    fvg,
    ob,
    previous_high_low,
    swing_highs_lows,
)

# momentum.py tools
from tools.indicators.momentum import rsi

# statistical.py tools
from tools.indicators.statistical import calculate_hurst, hurst

# trend.py tools
from tools.indicators.trend import ema, sma, wma

# volatility.py tools
from tools.indicators.volatility import adr, atr, bbands

# volume.py tools
from tools.indicators.volume import accumulation_distribution

phl = previous_high_low

__all__ = [
    # trend.py tools
    "ema",
    "sma",
    "wma",
    # momentum.py tools
    "rsi",
    # volatility.py tools
    "adr",
    "atr",
    "bbands",
    # volume.py tools
    "accumulation_distribution",
    # statistical.py tools
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
