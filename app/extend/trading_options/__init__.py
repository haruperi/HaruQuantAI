"""TradingOptions session and order gate blocks.

Description:
    Exports all 8 concrete StrategyQuant TradingOptions classes.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Provide canonical TradingOptions exports.

Key Capabilities:
    - FR-trading-option-evaluate: Expose all 8 TradingOptions evaluators.

Python API Usage:
    from app.extend.trading_options import DontTradeOnWeekends, LimitTimeRange

CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

from app.extend.trading_options.base import BaseTradingOption, TradingOption
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
]
