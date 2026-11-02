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
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

from app.extend.money_management.atr_risk_based_sizing import ATRRiskBasedSizing
from app.extend.money_management.base import (
    BasePositionSizer,
    clamp_lots,
    round_down,
    round_lots,
)
from app.extend.money_management.crypto_fixed_amount import CryptoFixedAmount
from app.extend.money_management.crypto_fixed_balance_pct import (
    CryptoFixedBalancePct,
)
from app.extend.money_management.crypto_size_by_price import CryptoSizeByPrice
from app.extend.money_management.fixed_amount import FixedAmount
from app.extend.money_management.fixed_size import FixedSize
from app.extend.money_management.picker_fixed_amount import PickerFixedAmount
from app.extend.money_management.picker_risk_fixed_pct_of_account import (
    PickerRiskFixedPctOfAccount,
)
from app.extend.money_management.risk_fixed_balance_pct import (
    RiskFixedBalancePct,
)
from app.extend.money_management.risk_fixed_pct_of_account import (
    RiskFixedPctOfAccount,
)
from app.extend.money_management.simple_martingale_mm import SimpleMartingaleMM
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
from app.extend.money_management.stocks_size_by_price import StocksSizeByPrice

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
    "clamp_lots",
    "evaluate_sizing",
    "fixed_lots",
    "margin_percent",
    "normalize_lots",
    "risk_cash",
    "risk_percent",
    "round_down",
    "round_lots",
    "volatility_risk",
]
