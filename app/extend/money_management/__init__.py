"""Money Management extension package conforming to StrategyQuant snippets.

Description:
    Exports position sizing algorithms and evaluation models for StrategyQuant
    MoneyManagement snippets.
Purpose:
    FEAT-MONEY-MANAGEMENT: StrategyQuant donor-faithful money management algorithms.
Key Capabilities:
    - FR-MM-EXPORTS: Canonical money management exports.
Python API Usage:
    from app.extend.money_management import evaluate_sizing, fixed_lots
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_strategy_control_features.py --no-cov
"""

from __future__ import annotations

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
    "SizingMethod",
    "evaluate_sizing",
    "fixed_lots",
    "margin_percent",
    "normalize_lots",
    "risk_cash",
    "risk_percent",
    "volatility_risk",
]
