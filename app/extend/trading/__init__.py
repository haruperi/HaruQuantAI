"""Trading commission, position scaling, ATM, and validity models.

Description:
    Exports concrete commission models, scaling classes, ATM multi-bracket strategy
    specifications, and pending order validity scheduling for the Trading extension
    cohort conforming to StrategyQuant SQ.Trading snippets.
Purpose:
    FEAT-TRADING: Provide canonical Trading exports.
Key Capabilities:
    - FR-TRADING-EXPORTS: Expose commission, scaling, ATM, and validity classes.
Python API Usage:
    from app.extend.trading import ATMStrategy, schedule_bar_validity
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_strategy_control_features.py --no-cov
"""

from app.extend.trading.atm import (
    ATMBracket,
    ATMStrategy,
)
from app.extend.trading.commissions import (
    BaseCommissionModel,
    NoneCommission,
    NoScaling,
    PercentageBasedCommission,
    PerTradeCommission,
    SizeBasedCommission,
    StockpickerCommission,
)
from app.extend.trading.validity import (
    TIMEFRAME_PATTERNS,
    parse_timeframe_delta,
    schedule_bar_validity,
)

__all__ = [
    "TIMEFRAME_PATTERNS",
    "ATMBracket",
    "ATMStrategy",
    "BaseCommissionModel",
    "NoScaling",
    "NoneCommission",
    "PerTradeCommission",
    "PercentageBasedCommission",
    "SizeBasedCommission",
    "StockpickerCommission",
    "parse_timeframe_delta",
    "schedule_bar_validity",
]
