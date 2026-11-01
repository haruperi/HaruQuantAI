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

from app.extend.trading_options.options import (
    BaseTradingOption,
    DontTradeOnWeekends,
    ExitAtEndOfDay,
    ExitOnFriday,
    LimitTimeRange,
    MaxDistanceFromMarket,
    MaxTradesPerDay,
    MinMaxSLPT,
    UseInitialSLPT,
)

__all__ = [
    "BaseTradingOption",
    "DontTradeOnWeekends",
    "ExitAtEndOfDay",
    "ExitOnFriday",
    "LimitTimeRange",
    "MaxDistanceFromMarket",
    "MaxTradesPerDay",
    "MinMaxSLPT",
    "UseInitialSLPT",
]
