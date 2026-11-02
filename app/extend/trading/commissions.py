"""Concrete donor-faithful Trading commission and scaling models.

Description:
    Exposes StrategyQuant Trading extension cohort classes:
    NoneCommission (Commissions/None.java), PercentageBasedCommission
    (Commissions/PercentageBased.java), PerTradeCommission
    (Commissions/PerTrade.java), SizeBasedCommission (Commissions/SizeBased.java),
    StockpickerCommission (Commissions/Stockpicker.java), and NoScaling
    (Scaling/NoScaling.java) backed by modular subpackages.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Backward-compatible facade for Trading cohort.

Key Capabilities:
    - FR-TRADING-COMMISSION-FACADE: Provide unified re-exports for commissions
      and scaling models.

Python API Usage:
    from app.extend.trading.commissions import PercentageBasedCommission, NoScaling

CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

from app.extend.trading.commissions.base import (
    CommissionsMethod,
    CommissionsMethodsList,
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
from app.extend.trading.scaling.base import (
    ScalingMethod,
    ScalingMethodsList,
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
    "ScalingMethod",
    "ScalingMethodsList",
    "SizeBased",
    "SizeBasedCommission",
    "Stockpicker",
    "StockpickerCommission",
]
