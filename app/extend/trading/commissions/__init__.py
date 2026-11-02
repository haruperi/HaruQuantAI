"""Trading commission calculation methods conforming to StrategyQuant SQ.

Description:
    Exposes all concrete StrategyQuant commission snippets (None, PercentageBased,
    PerTrade, SizeBased, Stockpicker) alongside the CommissionsMethod base contract
    and CommissionsMethodsList singleton registry.

Purpose:
    FEAT-TRADING-COMMISSIONS: Canonical exports for SQ Trading Commissions.

Key Capabilities:
    - FR-TRADING-COMMISSIONS-EXPORTS: Unified exports of all commission methods.

Python API Usage:
    from app.extend.trading.commissions import (
        BaseCommissionModel,
        CommissionsMethod,
        CommissionsMethodsList,
        NoneCommission,
        PercentageBasedCommission,
        PerTradeCommission,
        SizeBasedCommission,
        StockpickerCommission,
    )

CLI Usage:
    uv run pytest tests/extend/test_trading_catalog.py --no-cov
"""

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
    get_order_close_price,
    get_order_open_price,
    get_order_size,
    is_pending_order,
)
from app.extend.trading.commissions.none import (
    NoneCommission,
    NoneMethod,
)
from app.extend.trading.commissions.per_trade import (
    PerTrade,
    PerTradeCommission,
)
from app.extend.trading.commissions.percentage_based import (
    PercentageBased,
    PercentageBasedCommission,
)
from app.extend.trading.commissions.size_based import (
    SizeBased,
    SizeBasedCommission,
)
from app.extend.trading.commissions.stockpicker import (
    Stockpicker,
    StockpickerCommission,
)
from app.extend.trading.scaling.no_scaling import (
    NoScaling,
)

BaseCommissionModel = CommissionsMethod

__all__ = [
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
    "SizeBased",
    "SizeBasedCommission",
    "Stockpicker",
    "StockpickerCommission",
    "get_order_close_price",
    "get_order_open_price",
    "get_order_size",
    "is_pending_order",
]
