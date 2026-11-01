"""Unit tests for FormulaCatalog and the 18 formula definitions."""

from __future__ import annotations

from app.extend.formulas.catalog import (
    FormulaCatalog,
    PriceFormulas,
    RangeFormulas,
    RangeLevelFormulas,
    SizeFormulas,
    SLPTFormulas,
)


def test_price_use_formula() -> None:
    """Test Price/UseFormula across arithmetic operators."""
    assert PriceFormulas.use_formula("+", 10.0, 5.0) == 15.0
    assert PriceFormulas.use_formula("-", 10.0, 5.0) == 5.0
    assert PriceFormulas.use_formula("*", 10.0, 5.0) == 50.0
    assert PriceFormulas.use_formula("/", 10.0, 5.0) == 2.0
    assert PriceFormulas.use_formula("/", 10.0, 0.0) == 0.0


def test_range_formulas() -> None:
    """Test Range formulas: ATRBasedValue, FixedValue, None, PriceRange."""
    assert RangeFormulas.atr_based_value(0.0015, 2.0) == 0.0030
    assert round(RangeFormulas.fixed_value(20.0, 0.0001), 6) == 0.0020
    assert RangeFormulas.none() == 0.0
    assert round(RangeFormulas.price_range(1.1050, 1.1000), 6) == 0.0050


def test_range_level_formulas() -> None:
    """Test RangeLevel formulas for entry stop/limit levels."""
    # ATR offset
    level = RangeLevelFormulas.atr_based_value(1.1000, 1, 0.0020, 1.5)
    assert round(level, 6) == 1.1030

    # Fixed pips offset (short)
    level_short = RangeLevelFormulas.fixed_value(1.1000, -1, 10.0, 0.0001)
    assert round(level_short, 6) == 1.0990

    # None and PriceLevel
    assert RangeLevelFormulas.none(1.1200) == 1.1200
    assert RangeLevelFormulas.price_level(1.1250) == 1.1250

    # PriceRange offset
    level_pr = RangeLevelFormulas.price_range(1.1000, 1, 1.1050, 1.1010)
    assert round(level_pr, 6) == 1.1040


def test_slpt_formulas() -> None:
    """Test SLPT formulas: ATRBasedValue, FixedValue, None, PctValue, PriceLevel, ValueFromFormula."""
    assert SLPTFormulas.atr_based_value(0.0010, 2.5) == 0.0025
    assert round(SLPTFormulas.fixed_value(30.0, 0.0001), 6) == 0.0030
    assert SLPTFormulas.none() == 0.0
    assert SLPTFormulas.pct_value(100.0, 2.5) == 2.5
    assert SLPTFormulas.price_level(1.1500) == 1.1500
    assert SLPTFormulas.value_from_formula(45.0) == 45.0


def test_size_formulas() -> None:
    """Test Size formulas: DefineOwnSize, UseGlobalMM."""
    assert SizeFormulas.define_own_size(0.5) == 0.5
    assert SizeFormulas.define_own_size(0.001) == 0.01  # clamped to min lot
    assert SizeFormulas.use_global_mm() == -1.0


def test_formula_catalog_evaluate() -> None:
    """Test central FormulaCatalog evaluation dispatcher."""
    val = FormulaCatalog.evaluate(
        "Range", "atr_based_value", atr_value=0.0020, coef=3.0
    )
    assert val == 0.0060

    val2 = FormulaCatalog.evaluate("Size", "use_global_mm")
    assert val2 == -1.0
