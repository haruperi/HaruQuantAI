"""Functions extension package conforming to StrategyQuant SQ.Functions snippets.

Description:
    Exports core calculation and domain utility functions including
    OrderFunctions, ComparatorByProfit, DailyEquityComputer, and StatFunctions,
    alongside trade scope filtering and price normalization utilities.

Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions.

Key Capabilities:
    - FR-FUNCTIONS-EXPORTS: Canonical functions module exports.

Python API Usage:
    from app.extend.functions import (
        ComparatorByProfit,
        DailyEquityComputer,
        OrderFunctions,
        StatFunctions,
        TradeFilter,
        normalize_price,
    )

CLI Usage:
    uv run pytest tests/extend/test_functions.py --no-cov
"""

from __future__ import annotations

from app.extend.functions.comparator_by_profit import (
    PL_TYPE_MONEY,
    PL_TYPE_PERCENT,
    PL_TYPE_PIPS,
    ComparatorByProfit,
)
from app.extend.functions.daily_equity_computer import DailyEquityComputer
from app.extend.functions.order_functions import (
    OrderFunctions,
    TradeFilter,
    aware_timestamp,
    bars_since,
    normalize_price,
    pip_size,
)
from app.extend.functions.stat_functions import StatFunctions

__all__ = [
    "PL_TYPE_MONEY",
    "PL_TYPE_PERCENT",
    "PL_TYPE_PIPS",
    "ComparatorByProfit",
    "DailyEquityComputer",
    "OrderFunctions",
    "StatFunctions",
    "TradeFilter",
    "aware_timestamp",
    "bars_since",
    "normalize_price",
    "pip_size",
]
