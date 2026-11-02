"""Money Management extension package conforming to StrategyQuant snippets.

Description:
    Exports the BasePositionSizer contract, all 12 concrete donor
    MoneyManagement position sizing classes, and low-level position sizing
    algorithms and evaluation models.
Purpose:
    FEAT-MONEY-MANAGEMENT: StrategyQuant donor-faithful money management algorithms.
Key Capabilities:
    - FR-MM-EXPORTS: Canonical money management exports.
Python API Usage:
    from app.extend.money_management import RiskFixedPctOfAccount, evaluate_sizing
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py --no-cov
"""

from __future__ import annotations

from app.extend.money_management.base import BasePositionSizer
from app.extend.money_management.sizers import (
    ATRRiskBasedSizing,
    CryptoFixedAmount,
    CryptoFixedBalancePct,
    CryptoSizeByPrice,
    FixedAmount,
    FixedSize,
    PickerFixedAmount,
    PickerRiskFixedPctOfAccount,
    RiskFixedBalancePct,
    RiskFixedPctOfAccount,
    SimpleMartingaleMM,
    StocksSizeByPrice,
)
from app.extend.money_management.sizing import (
    MAX_PERCENT,
    SizingMethod,
    evaluate_sizing,
    fixed_lots,
    margin_percent,
    normalize_lots,
    risk_cash,
    risk_percent,
    volatility_risk,
)

__all__ = [
    "MAX_PERCENT",
    "ATRRiskBasedSizing",
    "BasePositionSizer",
    "CryptoFixedAmount",
    "CryptoFixedBalancePct",
    "CryptoSizeByPrice",
    "FixedAmount",
    "FixedSize",
    "PickerFixedAmount",
    "PickerRiskFixedPctOfAccount",
    "RiskFixedBalancePct",
    "RiskFixedPctOfAccount",
    "SimpleMartingaleMM",
    "SizingMethod",
    "StocksSizeByPrice",
    "evaluate_sizing",
    "fixed_lots",
    "margin_percent",
    "normalize_lots",
    "risk_cash",
    "risk_percent",
    "volatility_risk",
]
