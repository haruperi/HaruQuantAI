"""Formulas extension package conforming to StrategyQuant SQ.Formulas snippets.

Description:
    Exports formula catalogs, modular subpackages (CloseSize, Price, Range,
    RangeLevel, Size, SLPT), base blocks, and price level calculations matching
    StrategyQuant SQ.Formulas.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-FORMULAS-EXPORTS: Canonical formula models and evaluation exports.
Python API Usage:
    from app.extend.formulas import FormulaCatalog, FormulaBlock, evaluate_price_level
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from app.extend.formulas import (
    close_size,
    price,
    range_level,
    size,
    slpt,
)
from app.extend.formulas import (
    range as formula_range,
)
from app.extend.formulas.base import (
    ORDER_NOT_DEFINED,
    FormulaBlock,
    MMFormulaBlock,
)
from app.extend.formulas.catalog import (
    FormulaCatalog,
    PriceFormulas,
    RangeFormulas,
    RangeLevelFormulas,
    SizeFormulas,
    SLPTFormulas,
)
from app.extend.formulas.close_size.full_position import FullPosition
from app.extend.formulas.price_level import (
    PriceFormulaMode,
    evaluate_price_level,
    price_offset_atr,
    price_offset_percent,
    price_offset_pips,
)

__all__ = [
    "ORDER_NOT_DEFINED",
    "FormulaBlock",
    "FormulaCatalog",
    "FullPosition",
    "MMFormulaBlock",
    "PriceFormulaMode",
    "PriceFormulas",
    "RangeFormulas",
    "RangeLevelFormulas",
    "SLPTFormulas",
    "SizeFormulas",
    "close_size",
    "evaluate_price_level",
    "formula_range",
    "price",
    "price_offset_atr",
    "price_offset_percent",
    "price_offset_pips",
    "range_level",
    "size",
    "slpt",
]
