"""Temporary migration bridge to app.core.trading.blocks.series."""

from __future__ import annotations

import sys

from app.core.trading.blocks import series as _implementation
from app.core.trading.blocks.series import *  # noqa: F403
from app.core.trading.blocks.series import (
    COMPUTED_PRICE_INPUTS,
    BarData,
    IndicatorSeries,
    computed_price,
    resolve_shift_value,
    round_value,
)

__all__ = [
    "COMPUTED_PRICE_INPUTS",
    "BarData",
    "IndicatorSeries",
    "computed_price",
    "resolve_shift_value",
    "round_value",
]

sys.modules[__name__] = _implementation
