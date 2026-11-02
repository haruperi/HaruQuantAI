"""Concrete donor-faithful MoneyManagement position sizer blocks façade.

Description:
    Provides backward-compatible re-exports of all 12 StrategyQuant
    MoneyManagement snippet classes from their modular implementations:
    FixedSize, FixedAmount, RiskFixedPctOfAccount, RiskFixedBalancePct,
    ATRRiskBasedSizing, StocksSizeByPrice, CryptoFixedAmount,
    CryptoFixedBalancePct, CryptoSizeByPrice, PickerFixedAmount,
    PickerRiskFixedPctOfAccount, and SimpleMartingaleMM.
Purpose:
    FEAT-MONEY-MANAGEMENT: Unified façade for money management snippet classes.
Key Capabilities:
    - FR-MM-EXPORTS: Canonical imports across modular money management snippets.
Python API Usage:
    from app.extend.money_management.sizers import RiskFixedPctOfAccount
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --no-cov
"""

from __future__ import annotations

from app.extend.money_management import (
    atr_risk_based_sizing as _atr_mod,
)
from app.extend.money_management import (
    crypto_fixed_amount as _cfa_mod,
)
from app.extend.money_management import (
    crypto_fixed_balance_pct as _cfbp_mod,
)
from app.extend.money_management import (
    crypto_size_by_price as _csbp_mod,
)
from app.extend.money_management import (
    fixed_amount as _fa_mod,
)
from app.extend.money_management import (
    fixed_size as _fs_mod,
)
from app.extend.money_management import (
    picker_fixed_amount as _pfa_mod,
)
from app.extend.money_management import (
    picker_risk_fixed_pct_of_account as _prfpoa_mod,
)
from app.extend.money_management import (
    risk_fixed_balance_pct as _rfbp_mod,
)
from app.extend.money_management import (
    risk_fixed_pct_of_account as _rfpoa_mod,
)
from app.extend.money_management import (
    simple_martingale_mm as _smm_mod,
)
from app.extend.money_management import (
    stocks_size_by_price as _ssbp_mod,
)
from app.extend.money_management.base import (
    clamp_lots as _clamp_lots,
)
from app.extend.money_management.base import (
    round_down as _round_down,
)


class ATRRiskBasedSizing(_atr_mod.ATRRiskBasedSizing):
    """Facade re-export for ATRRiskBasedSizing."""


class CryptoFixedAmount(_cfa_mod.CryptoFixedAmount):
    """Facade re-export for CryptoFixedAmount."""


class CryptoFixedBalancePct(_cfbp_mod.CryptoFixedBalancePct):
    """Facade re-export for CryptoFixedBalancePct."""


class CryptoSizeByPrice(_csbp_mod.CryptoSizeByPrice):
    """Facade re-export for CryptoSizeByPrice."""


class FixedAmount(_fa_mod.FixedAmount):
    """Facade re-export for FixedAmount."""


class FixedSize(_fs_mod.FixedSize):
    """Facade re-export for FixedSize."""


class PickerFixedAmount(_pfa_mod.PickerFixedAmount):
    """Facade re-export for PickerFixedAmount."""


class PickerRiskFixedPctOfAccount(_prfpoa_mod.PickerRiskFixedPctOfAccount):
    """Facade re-export for PickerRiskFixedPctOfAccount."""


class RiskFixedBalancePct(_rfbp_mod.RiskFixedBalancePct):
    """Facade re-export for RiskFixedBalancePct."""


class RiskFixedPctOfAccount(_rfpoa_mod.RiskFixedPctOfAccount):
    """Facade re-export for RiskFixedPctOfAccount."""


class SimpleMartingaleMM(_smm_mod.SimpleMartingaleMM):
    """Facade re-export for SimpleMartingaleMM."""


class StocksSizeByPrice(_ssbp_mod.StocksSizeByPrice):
    """Facade re-export for StocksSizeByPrice."""


__all__ = [
    "ATRRiskBasedSizing",
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
    "StocksSizeByPrice",
    "_clamp_lots",
    "_round_down",
]
