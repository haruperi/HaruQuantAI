"""StrategyQuant SQ.Strategies snippet collection and execution framework.

Description:
    Exports all 13 StrategyQuant donor strategy implementations alongside the
    core Strategy base execution framework, multi-chart market data structures,
    trading interface, indicator adapters, and order lifecycle enumerations.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful strategy snippets package.

Key Capabilities:
    - FR-STRAT-EXPORTS: Canonical imports across all modular strategy snippet modules.

Python API Usage:
    from app.extend.strategies import Strategy, CCIReverse, CompleteStrategySample

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from app.extend.strategies.base import (
    ChartData,
    DataSeries,
    ILiveOrder,
    IndicatorResult,
    Indicators,
    ITradingEvent,
    ITradingEventListener,
    Log,
    MarketDataManager,
    OrderBuilder,
    OrderCloseTypes,
    OrderTypes,
    Parameter,
    Strategy,
    Trader,
    UpdateEventTypes,
)
from app.extend.strategies.cci_reverse import CCIReverse
from app.extend.strategies.complete_strategy_sample import (
    CompleteStrategySample,
)
from app.extend.strategies.live_test_strategy_1 import LiveTestStrategy1
from app.extend.strategies.market_data_chart_data_1_test_strategy_1 import (
    FullData,
    MarketDataChartData1TestStrategy1,
)
from app.extend.strategies.market_data_test_strategy import (
    MarketDataTestStrategy,
)
from app.extend.strategies.robustness_test_strategy import (
    RobustnessTestStrategy,
)
from app.extend.strategies.test_indy_strategy import TestIndyStrategy
from app.extend.strategies.test_ohlc_daily_strategy import (
    TestOHLCDailyStrategy,
)
from app.extend.strategies.test_special_strategy import TestSpecialStrategy
from app.extend.strategies.test_strategy import TestStrategy
from app.extend.strategies.test_strategy_1 import TestStrategy1
from app.extend.strategies.test_strategy_ask_bid import TestStrategyAskBid
from app.extend.strategies.variables_strategy_test import (
    VariablesStrategyTest,
)

__all__ = [
    "CCIReverse",
    "ChartData",
    "CompleteStrategySample",
    "DataSeries",
    "FullData",
    "ILiveOrder",
    "ITradingEvent",
    "ITradingEventListener",
    "IndicatorResult",
    "Indicators",
    "LiveTestStrategy1",
    "Log",
    "MarketDataChartData1TestStrategy1",
    "MarketDataManager",
    "MarketDataTestStrategy",
    "OrderBuilder",
    "OrderCloseTypes",
    "OrderTypes",
    "Parameter",
    "RobustnessTestStrategy",
    "Strategy",
    "TestIndyStrategy",
    "TestOHLCDailyStrategy",
    "TestSpecialStrategy",
    "TestStrategy",
    "TestStrategy1",
    "TestStrategyAskBid",
    "Trader",
    "UpdateEventTypes",
    "VariablesStrategyTest",
]
