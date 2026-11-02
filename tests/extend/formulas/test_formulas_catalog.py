"""Unit tests for FormulaCatalog and the 19 StrategyQuant formula definitions."""

from __future__ import annotations

from typing import Any, override

import pytest
from app.core.data.contracts import SymbolInfo, SymbolPrice
from app.extend.formulas import (
    ORDER_NOT_DEFINED,
    FormulaBlock,
    FormulaCatalog,
    FullPosition,
    MMFormulaBlock,
    PriceFormulas,
    RangeFormulas,
    RangeLevelFormulas,
    SizeFormulas,
    SLPTFormulas,
    close_size,
    evaluate_price_level,
    price,
    price_offset_atr,
    price_offset_percent,
    price_offset_pips,
    range_level,
    size,
    slpt,
)
from app.extend.formulas import (
    range as formula_range,
)


class MockStrategy:
    """Mock strategy supporting pip conversions, ATR lookup, quotes, and MM."""

    def __init__(
        self, atr: float = 0.0020, bid: float = 1.1000, ask: float = 1.1002
    ) -> None:
        self._atr = atr
        self._bid = bid
        self._ask = ask
        self.mm_called = False

    def convert_pips_to_real_price(self, symbol: str, pips: float) -> float:
        _ = symbol
        return pips * 0.0001

    def get_atr_value(self, symbol: str, period: int) -> float:
        _ = (symbol, period)
        return self._atr

    def decisionBid(self, symbol: str, bars_ago: int) -> float:  # noqa: N802
        _ = (symbol, bars_ago)
        return self._bid

    def decisionAsk(self, symbol: str, bars_ago: int) -> float:  # noqa: N802
        _ = (symbol, bars_ago)
        return self._ask

    def get_global_mm_method(self) -> MockMM:
        return MockMM()


class MockJavaStrategy:
    """Mock strategy using Java-style method names for fallback branches."""

    def __init__(self, atr: float = 0.0018) -> None:
        self._atr = atr

    def convertPipsToRealPrice(self, symbol: str, pips: float) -> float:  # noqa: N802
        _ = symbol
        return pips * 0.0001

    def getATRValue(  # noqa: N802
        self, symbol: str, period: int, bars_ago: int
    ) -> float:
        _ = (symbol, period, bars_ago)
        return self._atr

    def getGlobalMMMethod(self) -> MockJavaMM:  # noqa: N802
        return MockJavaMM()


class MockJavaMM:
    """Mock Java-style MoneyManagement method."""

    def computeTradeSize(self, *args: Any, **kwargs: Any) -> float:  # noqa: N802
        _ = (args, kwargs)
        return 3.0


class MockSettingsStrategy:
    """Mock strategy returning MM from get_settings()."""

    def __init__(self, mm: Any) -> None:
        self._mm = mm

    def get_settings(self) -> dict[str, Any]:
        return {"MoneyManagement": self._mm}


class MockMM:
    """Mock MoneyManagement method."""

    def compute_trade_size(
        self,
        strategy: object,
        symbol: str,
        order_type: int,
        price: float,
        sl: float,
    ) -> float:
        _ = (strategy, symbol, order_type, price, sl)
        return 2.5


def test_price_use_formula() -> None:
    """Test Price/UseFormula across arithmetic operators."""
    assert PriceFormulas.use_formula("+", 10.0, 5.0) == 15.0
    assert PriceFormulas.use_formula("-", 10.0, 5.0) == 5.0
    assert PriceFormulas.use_formula("*", 10.0, 5.0) == 50.0
    assert PriceFormulas.use_formula("/", 10.0, 5.0) == 2.0
    assert PriceFormulas.use_formula("/", 10.0, 0.0) == 0.0
    assert PriceFormulas.use_formula("unknown", 10.0, 5.0) == 10.0


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

    with pytest.raises(ValueError, match=r"Unknown formula category: Unknown"):
        FormulaCatalog.evaluate("Unknown", "some_func")

    with pytest.raises(
        ValueError, match=r"Unknown formula 'unknown' in category 'Range'"
    ):
        FormulaCatalog.evaluate("Range", "unknown")


# Modular Formula Block Class Tests


def test_close_size_full_position() -> None:
    """Test CloseSize.FullPosition snippet class."""
    fp = close_size.FullPosition()
    assert isinstance(fp, FullPosition)
    assert fp.name == "Full position"
    assert fp.group == "CloseSize"
    assert fp.order == 100
    assert fp.evaluate_formula(None, "EURUSD", 1.1000, 1) == 0.0


def test_price_use_formula_class() -> None:
    """Test Price.UseFormula snippet class."""
    uf_scalar = price.UseFormula(value=1.1250)
    assert uf_scalar.name == "Use formula"
    assert uf_scalar.group == "Price"
    assert uf_scalar.order == 400
    assert uf_scalar.price_level is True
    assert uf_scalar.evaluate_formula(None, "EURUSD", 1.1000, 1) == 1.1250
    assert uf_scalar.is_boolean_value() is False

    # Block with evaluate_block
    class NestedBlock:
        def evaluate_block(self) -> float:
            return 1.1350

    uf_block = price.UseFormula(value=NestedBlock())
    assert uf_block.evaluate_formula(None, "EURUSD", 1.1000, 1) == 1.1350

    # Sub-block with evaluate_formula
    class NestedFormula:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return price + 0.0050

    uf_sub = price.UseFormula(value=NestedFormula())
    assert uf_sub.evaluate_formula(None, "EURUSD", 1.1000, 1) == 1.1050

    # Callable
    uf_callable = price.UseFormula(value=lambda: 1.1400)
    assert uf_callable.evaluate_formula(None, "EURUSD", 1.1000, 1) == 1.1400

    # Boolean test
    uf_bool = price.UseFormula(value=True)
    assert uf_bool.is_boolean_value() is True

    class NestedBool:
        def is_boolean_value(self) -> bool:
            return True

    assert price.UseFormula(value=NestedBool()).is_boolean_value() is True


def test_range_snippet_classes() -> None:
    """Test all Range snippet classes."""
    strat = MockStrategy(atr=0.0025)
    java_strat = MockJavaStrategy(atr=0.0018)

    # None
    none_formula = formula_range.NoneRange()
    assert none_formula.name == "None"
    assert none_formula.group == "Range"
    assert none_formula.none_value is True
    assert none_formula.evaluate_formula(strat, "EURUSD", 1.10, 1) == ORDER_NOT_DEFINED

    # FixedValue
    fixed = formula_range.FixedValue(value=25.0)
    assert fixed.evaluate_formula(strat, "EURUSD", 1.10, 1) == 0.0025
    assert (
        formula_range.FixedValue(value=0.0).evaluate_formula(strat, "EURUSD", 1.10, 1)
        == 0.0
    )
    assert (
        formula_range.FixedValue(value=10.0).evaluate_formula(None, "EURUSD", 1.10, 1)
        == 0.0010
    )
    assert (
        formula_range.FixedValue(value=15.0).evaluate_formula(
            java_strat, "EURUSD", 1.10, 1
        )
        == 0.0015
    )

    # ATRBasedValue
    atr_formula = formula_range.ATRBasedValue(value=2.0, atr_period=14)
    assert atr_formula.evaluate_formula(strat, "EURUSD", 1.10, 1) == 0.0050
    assert (
        formula_range.ATRBasedValue(value=0.0).evaluate_formula(
            strat, "EURUSD", 1.10, 1
        )
        == 0.0
    )
    assert formula_range.ATRBasedValue(value=2.0, atr_period=14).evaluate_formula(
        java_strat, "EURUSD", 1.10, 1
    ) == round(2.0 * 0.0018, 5)

    # PriceRange
    pr = formula_range.PriceRange(value=30.0)
    assert pr.evaluate_formula(strat, "EURUSD", 1.10, 1) == 0.0030
    assert (
        formula_range.PriceRange(value=10.0).evaluate_formula(None, "EURUSD", 1.10, 1)
        == 0.0010
    )
    assert (
        formula_range.PriceRange(value=10.0).evaluate_formula(
            java_strat, "EURUSD", 1.10, 1
        )
        == 0.0010
    )

    class NestedPips:
        def evaluate_block(self) -> float:
            return 20.0

    assert (
        formula_range.PriceRange(value=NestedPips()).evaluate_formula(
            strat, "EURUSD", 1.10, 1
        )
        == 0.0020
    )

    class NestedFormulaPips:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return 25.0

    assert (
        formula_range.PriceRange(value=NestedFormulaPips()).evaluate_formula(
            strat, "EURUSD", 1.10, 1
        )
        == 0.0025
    )

    assert (
        round(
            formula_range.PriceRange(value=lambda: 12.0).evaluate_formula(
                strat, "EURUSD", 1.10, 1
            ),
            6,
        )
        == 0.0012
    )


def test_range_level_snippet_classes() -> None:
    """Test all RangeLevel snippet classes."""
    strat = MockStrategy(atr=0.0020, bid=1.1000, ask=1.1002)
    java_strat = MockJavaStrategy(atr=0.0018)

    # None
    none_rl = range_level.NoneRangeLevel()
    assert none_rl.evaluate_formula(strat, "EURUSD", 1.10, 1) == ORDER_NOT_DEFINED

    # FixedValue
    fixed_rl = range_level.FixedValue(value=20.0)
    # Long: decisionBid (1.1000) - (20 * 0.0001) = 1.0980
    assert round(fixed_rl.evaluate_formula(strat, "EURUSD", 1.1000, 1), 6) == 1.0980
    # Short: decisionAsk (1.1002) + (20 * 0.0001) = 1.1022
    assert round(fixed_rl.evaluate_formula(strat, "EURUSD", 1.1000, -1), 6) == 1.1022
    # Without strategy (using price)
    assert round(fixed_rl.evaluate_formula(None, "EURUSD", 1.1000, 1), 6) == 1.0980
    # Java strategy
    assert (
        round(fixed_rl.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 6) == 1.0980
    )

    # ATRBasedValue
    atr_rl = range_level.ATRBasedValue(value=1.5, atr_period=14)
    # Long: 1.1000 - (1.5 * 0.0020) = 1.0970
    assert round(atr_rl.evaluate_formula(strat, "EURUSD", 1.1000, 1), 5) == 1.0970
    # Short: 1.1000 + (1.5 * 0.0020) = 1.1030
    assert round(atr_rl.evaluate_formula(strat, "EURUSD", 1.1000, -1), 5) == 1.1030
    assert (
        range_level.ATRBasedValue(value=0.0).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == ORDER_NOT_DEFINED
    )
    assert round(atr_rl.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 5) == round(
        1.1000 - 1.5 * 0.0018, 5
    )

    # PriceRange
    pr_rl = range_level.PriceRange(value=15.0)
    assert round(pr_rl.evaluate_formula(strat, "EURUSD", 1.1000, 1), 6) == 1.0985
    assert round(pr_rl.evaluate_formula(strat, "EURUSD", 1.1000, -1), 6) == 1.1015
    assert round(pr_rl.evaluate_formula(None, "EURUSD", 1.1000, 1), 6) == 1.0985
    assert round(pr_rl.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 6) == 1.0985

    class NestedPips:
        def evaluate_block(self) -> float:
            return 10.0

    assert (
        round(
            range_level.PriceRange(value=NestedPips()).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.0990
    )

    class NestedFormulaPips:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return 5.0

    assert (
        round(
            range_level.PriceRange(value=NestedFormulaPips()).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.0995
    )

    assert (
        round(
            range_level.PriceRange(value=lambda: 2.0).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.0998
    )

    # PriceLevel
    pl_rl = range_level.PriceLevel(value=1.1250)
    assert pl_rl.evaluate_formula(strat, "EURUSD", 1.1000, 1) == 1.1250

    class NestedPriceBlock:
        def evaluate_block(self) -> float:
            return 1.1300

    assert (
        range_level.PriceLevel(value=NestedPriceBlock()).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1300
    )

    class NestedPriceFormula:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return 1.1350

    assert (
        range_level.PriceLevel(value=NestedPriceFormula()).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1350
    )

    assert (
        range_level.PriceLevel(value=lambda: 1.1400).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1400
    )


def test_size_snippet_classes() -> None:
    """Test Size snippet classes."""
    strat = MockStrategy()
    java_strat = MockJavaStrategy()

    # DefineOwnSize
    dos = size.DefineOwnSize(value=0.75)
    assert dos.name == "Define own size"
    assert dos.compute_size(strat, "EURUSD", 0, 1.1000, 1.0950) == 0.75

    # Clamping below 0.01
    dos_small = size.DefineOwnSize(value=0.001)
    assert dos_small.value == 0.01

    # UseGlobalMM with mock strategy
    ugmm = size.UseGlobalMM()
    assert ugmm.compute_size(strat, "EURUSD", 0, 1.1000, 1.0950) == 2.5
    # With Java strategy
    assert ugmm.compute_size(java_strat, "EURUSD", 0, 1.1000, 1.0950) == 3.0
    # With Settings Strategy
    settings_strat = MockSettingsStrategy(MockMM())
    assert ugmm.compute_size(settings_strat, "EURUSD", 0, 1.1000, 1.0950) == 2.5
    # Without MM set in settings
    no_mm_strat = MockSettingsStrategy(None)
    assert ugmm.compute_size(no_mm_strat, "EURUSD", 0, 1.1000, 1.0950) == 1.0
    # Without strategy defaults to 1.0
    assert ugmm.compute_size(None, "EURUSD", 0, 1.1000, 1.0950) == 1.0


def test_slpt_snippet_classes() -> None:
    """Test all SLPT snippet classes."""
    strat = MockStrategy(atr=0.0015)
    java_strat = MockJavaStrategy(atr=0.0018)

    # None
    none_slpt = slpt.NoneSLPT()
    assert none_slpt.evaluate_formula(strat, "EURUSD", 1.10, 1) == ORDER_NOT_DEFINED

    # FixedValue
    fv = slpt.FixedValue(value=30.0)
    assert round(fv.evaluate_formula(strat, "EURUSD", 1.1000, 1), 6) == 1.1030
    assert round(fv.evaluate_formula(strat, "EURUSD", 1.1000, -1), 6) == 1.0970
    assert round(fv.evaluate_formula(None, "EURUSD", 1.1000, 1), 6) == 1.1030
    assert round(fv.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 6) == 1.1030

    # PctValue
    pv = slpt.PctValue(value=2.0)
    # 2% of 100.0 = 2.0
    assert pv.evaluate_formula(strat, "EURUSD", 100.0, 1) == 102.0
    assert pv.evaluate_formula(strat, "EURUSD", 100.0, -1) == 98.0

    # ATRBasedValue
    atr_slpt = slpt.ATRBasedValue(value=2.0, atr_period=20)
    # 1.1000 + (2.0 * 0.0015) = 1.1030
    assert round(atr_slpt.evaluate_formula(strat, "EURUSD", 1.1000, 1), 5) == 1.1030
    assert round(atr_slpt.evaluate_formula(strat, "EURUSD", 1.1000, -1), 5) == 1.0970
    assert round(
        atr_slpt.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 5
    ) == round(1.1000 + 2.0 * 0.0018, 5)

    # ValueFromFormula
    vff = slpt.ValueFromFormula(value=25.0)
    assert round(vff.evaluate_formula(strat, "EURUSD", 1.1000, 1), 6) == 1.1025
    assert round(vff.evaluate_formula(strat, "EURUSD", 1.1000, -1), 6) == 1.0975
    assert round(vff.evaluate_formula(None, "EURUSD", 1.1000, 1), 6) == 1.1025
    assert round(vff.evaluate_formula(java_strat, "EURUSD", 1.1000, 1), 6) == 1.1025

    class NestedPips:
        def evaluate_block(self) -> float:
            return 10.0

    assert (
        round(
            slpt.ValueFromFormula(value=NestedPips()).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.1010
    )

    class NestedFormulaPips:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return 5.0

    assert (
        round(
            slpt.ValueFromFormula(value=NestedFormulaPips()).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.1005
    )

    assert (
        round(
            slpt.ValueFromFormula(value=lambda: 2.0).evaluate_formula(
                strat, "EURUSD", 1.1000, 1
            ),
            6,
        )
        == 1.1002
    )

    # PriceLevel
    pl_slpt = slpt.PriceLevel(value=1.1500)
    assert pl_slpt.evaluate_formula(strat, "EURUSD", 1.1000, 1) == 1.1500

    class NestedPriceBlock:
        def evaluate_block(self) -> float:
            return 1.1600

    assert (
        slpt.PriceLevel(value=NestedPriceBlock()).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1600
    )

    class NestedPriceFormula:
        def evaluate_formula(
            self, strategy: Any, symbol: str, price: float, direction: int
        ) -> float:
            return 1.1700

    assert (
        slpt.PriceLevel(value=NestedPriceFormula()).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1700
    )

    assert (
        slpt.PriceLevel(value=lambda: 1.1800).evaluate_formula(
            strat, "EURUSD", 1.1000, 1
        )
        == 1.1800
    )


def test_base_formula_block() -> None:
    """Test abstract base FormulaBlock and MMFormulaBlock."""

    class CustomFormula(FormulaBlock):
        @override
        def evaluate_formula(
            self, strategy: object, symbol: str, price: float, direction: int
        ) -> float:
            return price + 1.0

    cf = CustomFormula("Custom", "Test", 50, price_level=False, none_value=False)
    assert cf.name == "Custom"
    assert cf.group == "Test"
    assert cf.order == 50
    assert cf.is_boolean_value() is False
    assert cf.evaluate_formula(None, "EURUSD", 10.0, 1) == 11.0

    class CustomMM(MMFormulaBlock):
        @override
        def compute_size(
            self,
            strategy: object,
            symbol: str,
            order_type: int,
            price: float,
            sl: float,
        ) -> float:
            return 1.5

    cmm = CustomMM("CustomMM", "Size", 150)
    assert cmm.name == "CustomMM"
    assert cmm.compute_size(None, "EURUSD", 0, 1.0, 0.5) == 1.5


def test_price_level_module() -> None:
    """Test helper functions in price_level.py module."""
    # price_offset_pips
    res_long = price_offset_pips(1.1000, 1, 20.0, 0.0001)
    assert round(res_long, 6) == 1.1020

    res_short = price_offset_pips(1.1000, -1, 20.0, 0.0001)
    assert round(res_short, 6) == 1.0980

    res_prot = price_offset_pips(1.1000, 1, 20.0, 0.0001, is_protective=True)
    assert round(res_prot, 6) == 1.0980

    with pytest.raises(ValueError, match=r"base_price must be finite and positive"):
        price_offset_pips(-1.0, 1, 10.0, 0.0001)

    with pytest.raises(
        ValueError, match=r"direction must be 1 \(Long\) or -1 \(Short\)"
    ):
        price_offset_pips(1.1000, 0, 10.0, 0.0001)

    with pytest.raises(ValueError, match=r"pips must be finite and nonnegative"):
        price_offset_pips(1.1000, 1, -5.0, 0.0001)

    with pytest.raises(ValueError, match=r"pip_size must be finite and positive"):
        price_offset_pips(1.1000, 1, 10.0, -0.0001)

    # price_offset_atr
    atr_long = price_offset_atr(1.1000, 1, 0.0015, multiplier=2.0)
    assert round(atr_long, 6) == 1.1030

    atr_short = price_offset_atr(1.1000, -1, 0.0015, multiplier=2.0, is_protective=True)
    assert round(atr_short, 6) == 1.1030

    with pytest.raises(ValueError, match=r"base_price must be finite and positive"):
        price_offset_atr(0.0, 1, 0.0010)

    with pytest.raises(
        ValueError, match=r"direction must be 1 \(Long\) or -1 \(Short\)"
    ):
        price_offset_atr(1.10, 2, 0.0010)

    with pytest.raises(ValueError, match=r"atr_value must be finite and nonnegative"):
        price_offset_atr(1.10, 1, -0.0010)

    with pytest.raises(ValueError, match=r"multiplier must be finite and nonnegative"):
        price_offset_atr(1.10, 1, 0.0010, multiplier=-1.0)

    # price_offset_percent
    pct_long = price_offset_percent(100.0, 1, 5.0)
    assert pct_long == 105.0

    pct_short = price_offset_percent(100.0, -1, 5.0, is_protective=True)
    assert pct_short == 105.0

    with pytest.raises(ValueError, match=r"base_price must be finite and positive"):
        price_offset_percent(-10.0, 1, 5.0)

    with pytest.raises(
        ValueError, match=r"direction must be 1 \(Long\) or -1 \(Short\)"
    ):
        price_offset_percent(100.0, 0, 5.0)

    with pytest.raises(ValueError, match=r"percent must be finite and nonnegative"):
        price_offset_percent(100.0, 1, -5.0)

    # evaluate_price_level
    spec = SymbolInfo(
        name="EURUSD",
        price=SymbolPrice(digits=5, tick_step=0.0001),
    )

    ev_abs = evaluate_price_level(
        "absolute", 1.1000, 1, absolute_price=1.1250, spec=spec
    )
    assert ev_abs == 1.1250

    ev_pips = evaluate_price_level("pips", 1.1000, 1, pips=10.0, pip_size=0.0001)
    assert round(ev_pips, 5) == 1.1010

    ev_atr = evaluate_price_level("atr", 1.1000, 1, atr_value=0.0010, multiplier=2.0)
    assert round(ev_atr, 5) == 1.1020

    ev_pct = evaluate_price_level("percent", 100.0, 1, percent=3.0)
    assert ev_pct == 103.0

    with pytest.raises(ValueError, match=r"Unknown price formula mode: invalid"):
        evaluate_price_level("invalid", 1.1000, 1)  # type: ignore[arg-type]
