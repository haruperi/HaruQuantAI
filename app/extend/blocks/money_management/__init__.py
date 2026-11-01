"""Money management strategy blocks and position sizers.

Description:
    Exports the BasePositionSizer contract and all 12 concrete donor
    MoneyManagement position sizing classes.
Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Provide canonical MoneyManagement exports.
Key Capabilities:
    - FR-mm-sizer-compute: Expose BasePositionSizer and 12 concrete sizers.
Python API Usage:
    from app.extend.blocks.money_management import RiskFixedPctOfAccount
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from app.extend.blocks.money_management.base import BasePositionSizer
from app.extend.blocks.money_management.sizers import (
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

__all__ = [
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
    "StocksSizeByPrice",
]
