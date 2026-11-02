"""Formulas extension package conforming to StrategyQuant SQ.Formulas snippets.

Description:
    Exports formula catalogs and evaluation models for StrategyQuant formula snippets
    including close sizing and price level calculations.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-FORMULAS-EXPORTS: Canonical formula models and evaluation exports.
Python API Usage:
    from app.extend.formulas import evaluate_price_level, price_offset_pips
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_strategy_control_features.py --no-cov
"""

from __future__ import annotations

from app.extend.formulas.catalog import FormulaCatalog
from app.extend.formulas.close_size.full_position import FullPosition
from app.extend.formulas.price_level import (
    PriceFormulaMode,
    evaluate_price_level,
    price_offset_atr,
    price_offset_percent,
    price_offset_pips,
)

__all__ = [
    "FormulaCatalog",
    "FullPosition",
    "PriceFormulaMode",
    "evaluate_price_level",
    "price_offset_atr",
    "price_offset_percent",
    "price_offset_pips",
]
