"""Formula evaluators catalog for Price, Range, RangeLevel, SLPT, and Size.

Description:
    Implements the 18 standard formula evaluation snippets from the SQ donor
    catalog, covering price arithmetic combinations, ATR and fixed pip ranges,
    entry order trigger price levels, Stop-Loss / Profit-Target distances,
    and position sizing specifications.

Purpose:
    FEAT-FORMULAS-CATALOG: Standardized formula evaluators for StrategyQuant snippets.

Key Capabilities:
    - FR-formulas-price: Price arithmetic evaluation.
    - FR-formulas-range: Fixed pip, ATR, and high-low price range calculators.
    - FR-formulas-range-level: Entry stop/limit trigger level positioning.
    - FR-formulas-slpt: Stop Loss and Profit Target distance evaluators.
    - FR-formulas-size: Fixed lot sizing and global money management sentinels.

Python API Usage:
    from app.extend.formulas.catalog import FormulaCatalog

    val = FormulaCatalog.evaluate(
        "Range", "atr_based_value", atr_value=0.0015, coef=2.0
    )

CLI Usage:
    python -c "from app.extend.formulas.catalog import FormulaCatalog; print(1)"
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_PIP_SIZE: float = 0.0001
_DEFAULT_COEF: float = 1.0
_MIN_LOT_SIZE: float = 0.01
_PERCENT_SCALE: float = 100.0
_EPSILON: float = 1e-12


class PriceFormulas:
    """Evaluators for price combination formulas."""

    @staticmethod
    def use_formula(op: str, val1: float, val2: float) -> float:
        """Evaluate arithmetic combination of two price/indicator operands.

        Args:
            op: Operator symbol ('+', '-', '*', '/').
            val1: Left operand.
            val2: Right operand.

        Returns:
            Calculated numeric result.
        """
        logger.debug("Evaluating Price/UseFormula: %f %s %f", val1, op, val2)
        if op == "+":
            return val1 + val2
        if op == "-":
            return val1 - val2
        if op == "*":
            return val1 * val2
        if op == "/":
            return val1 / val2 if abs(val2) > _EPSILON else 0.0
        return val1


class RangeFormulas:
    """Evaluators for pip and price range offsets."""

    @staticmethod
    def atr_based_value(atr_value: float, coef: float = _DEFAULT_COEF) -> float:
        """Calculate range as coef * atr_value."""
        return coef * atr_value

    @staticmethod
    def fixed_value(fixed_pips: float, pip_size: float = _DEFAULT_PIP_SIZE) -> float:
        """Calculate range as fixed_pips * pip_size."""
        return fixed_pips * pip_size

    @staticmethod
    def none() -> float:
        """Zero range sentinel."""
        return 0.0

    @staticmethod
    def price_range(high: float, low: float) -> float:
        """Calculate range as abs(high - low)."""
        return abs(high - low)


class RangeLevelFormulas:
    """Evaluators for entry trigger price levels."""

    @staticmethod
    def atr_based_value(
        price_level: float,
        direction: int,
        atr_value: float,
        coef: float = _DEFAULT_COEF,
    ) -> float:
        """Trigger price offset by ATR range."""
        return price_level + (direction * (coef * atr_value))

    @staticmethod
    def fixed_value(
        price_level: float,
        direction: int,
        fixed_pips: float,
        pip_size: float = _DEFAULT_PIP_SIZE,
    ) -> float:
        """Trigger price offset by fixed pips."""
        return price_level + (direction * (fixed_pips * pip_size))

    @staticmethod
    def none(price_level: float) -> float:
        """Unmodified base price level."""
        return price_level

    @staticmethod
    def price_level(price: float) -> float:
        """Direct price level."""
        return price

    @staticmethod
    def price_range(
        price_level: float, direction: int, high: float, low: float
    ) -> float:
        """Trigger price offset by bar range."""
        return price_level + (direction * abs(high - low))


class SLPTFormulas:
    """Evaluators for Stop Loss and Profit Target distances."""

    @staticmethod
    def atr_based_value(atr_value: float, coef: float = _DEFAULT_COEF) -> float:
        """SL/PT distance as coef * atr_value."""
        return coef * atr_value

    @staticmethod
    def fixed_value(fixed_pips: float, pip_size: float = _DEFAULT_PIP_SIZE) -> float:
        """SL/PT distance as fixed_pips * pip_size."""
        return fixed_pips * pip_size

    @staticmethod
    def none() -> float:
        """Unused SL/PT sentinel distance."""
        return 0.0

    @staticmethod
    def pct_value(entry_price: float, pct: float) -> float:
        """SL/PT distance as entry_price * (pct / 100.0)."""
        return entry_price * (pct / _PERCENT_SCALE)

    @staticmethod
    def price_level(price: float) -> float:
        """Explicit SL/PT target price level."""
        return price

    @staticmethod
    def value_from_formula(val: float) -> float:
        """Evaluated formula SL/PT value."""
        return val


class SizeFormulas:
    """Evaluators for position sizing and money management."""

    @staticmethod
    def define_own_size(lots: float) -> float:
        """Explicit lot size."""
        return max(_MIN_LOT_SIZE, lots)

    @staticmethod
    def use_global_mm() -> float:
        """Sentinel (-1.0) indicating global money management applies."""
        return -1.0


class FormulaCatalog:
    """Central registry of all 18 standard formula evaluators."""

    PRICE_FORMULAS = PriceFormulas
    RANGE_FORMULAS = RangeFormulas
    RANGE_LEVEL_FORMULAS = RangeLevelFormulas
    SLPT_FORMULAS = SLPTFormulas
    SIZE_FORMULAS = SizeFormulas

    @classmethod
    def evaluate(cls, category: str, formula_name: str, **kwargs: Any) -> float:
        """Evaluate named formula within specified category."""
        cat_map = {
            "Price": cls.PRICE_FORMULAS,
            "Range": cls.RANGE_FORMULAS,
            "RangeLevel": cls.RANGE_LEVEL_FORMULAS,
            "SLPT": cls.SLPT_FORMULAS,
            "Size": cls.SIZE_FORMULAS,
        }
        target_cat = cat_map.get(category)
        if target_cat is None:
            raise ValueError(f"Unknown formula category: {category}")

        method = getattr(target_cat, formula_name, None)
        if method is None:
            raise ValueError(
                f"Unknown formula '{formula_name}' in category '{category}'"
            )

        res = method(**kwargs)
        return float(res)
