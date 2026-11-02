"""Concrete donor-faithful TradingOptions session and order gate evaluators.

Description:
    Facade exporting all 8 StrategyQuant TradingOptions snippet classes:
    DontTradeOnWeekends, ExitAtEndOfDay, ExitOnFriday, LimitTimeRange,
    MaxDistanceFromMarket, MaxTradesPerDay, MinMaxSLPT, and UseInitialSLPT.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Complete the 8-class TradingOptions
    extension cohort under app/extend/trading_options.

Key Capabilities:
    - FR-trading-option-evaluate: Re-export session entry/exit gates, weekend/Friday
      cutoffs, maximum trades per day, order distance bounds, and SL/PT clamping.

Python API Usage:
    from app.extend.trading_options.options import LimitTimeRange, MinMaxSLPT

CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

from app.extend.trading_options.base import (
    BaseTradingOption,
    TradingOption,
    _in_time_window,
    _parse_hhmm,
)
from app.extend.trading_options.dont_trade_on_weekends import DontTradeOnWeekends
from app.extend.trading_options.exit_at_end_of_day import ExitAtEndOfDay
from app.extend.trading_options.exit_on_friday import ExitOnFriday
from app.extend.trading_options.limit_time_range import LimitTimeRange
from app.extend.trading_options.max_distance_from_market import (
    MaxDistanceFromMarket,
)
from app.extend.trading_options.max_trades_per_day import MaxTradesPerDay
from app.extend.trading_options.min_max_slpt import MinMaxSLPT
from app.extend.trading_options.use_initial_slpt import UseInitialSLPT

__all__ = [
    "BaseTradingOption",
    "DontTradeOnWeekends",
    "ExitAtEndOfDay",
    "ExitOnFriday",
    "LimitTimeRange",
    "MaxDistanceFromMarket",
    "MaxTradesPerDay",
    "MinMaxSLPT",
    "TradingOption",
    "UseInitialSLPT",
    "_in_time_window",
    "_parse_hhmm",
]
