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
    from app.extend.trading import (
        ATMStrategy,
        NoneCommission,
        PercentageBasedCommission,
        NoScaling,
        schedule_bar_validity,
    )

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py --no-cov
"""

from app.extend.trading.atm import (
    ATMBracket,
    ATMStrategy,
)
from app.extend.trading.commissions import (
    BaseCommissionModel,
    CommissionsMethod,
    CommissionsMethodsList,
    NoneCommission,
    NoneMethod,
    PercentageBased,
    PercentageBasedCommission,
    PerTrade,
    PerTradeCommission,
    SizeBased,
    SizeBasedCommission,
    Stockpicker,
    StockpickerCommission,
    get_order_close_price,
    get_order_open_price,
    get_order_size,
    is_pending_order,
)
from app.extend.trading.scaling import (
    NoScaling,
    ScalingMethod,
    ScalingMethodsList,
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
    "CommissionsMethod",
    "CommissionsMethodsList",
    "NoScaling",
    "NoneCommission",
    "NoneMethod",
    "PerTrade",
    "PerTradeCommission",
    "PercentageBased",
    "PercentageBasedCommission",
    "ScalingMethod",
    "ScalingMethodsList",
    "SizeBased",
    "SizeBasedCommission",
    "Stockpicker",
    "StockpickerCommission",
    "get_order_close_price",
    "get_order_open_price",
    "get_order_size",
    "is_pending_order",
    "parse_timeframe_delta",
    "schedule_bar_validity",
]
