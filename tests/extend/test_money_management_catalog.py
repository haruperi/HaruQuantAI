"""Comprehensive test suite for MoneyManagement snippets and catalog.

Description:
    Tests all 12 StrategyQuant MoneyManagement snippet classes, their base contract,
    parameter aliases, StrategyQuant donor metadata, rounding/clamping routines,
    and both compute_size and compute_trade_size execution paths.
Purpose:
    FEAT-MONEY-MANAGEMENT: Verify full donor parity and branch coverage for money management.
Key Capabilities:
    - FR-MM-CATALOG-TESTS: Exhaustive branch coverage across all 12 sizer snippets.
Python API Usage:
    uv run pytest tests/extend/test_money_management_catalog.py --cov=app.extend.money_management --cov-branch
CLI Usage:
    uv run pytest tests/extend/test_money_management_catalog.py
"""

from __future__ import annotations

import math
from typing import Any, override

import pytest
from app.extend.money_management.atr_risk_based_sizing import (
    ATRRiskBasedSizing,
    _extract_atr,
)
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
from app.extend.money_management.sizers import (
    ATRRiskBasedSizing as ATRRiskBasedSizingFacade,
)
from app.extend.money_management.sizers import (
    CryptoFixedAmount as CryptoFixedAmountFacade,
)
from app.extend.money_management.sizers import (
    CryptoFixedBalancePct as CryptoFixedBalancePctFacade,
)
from app.extend.money_management.sizers import (
    CryptoSizeByPrice as CryptoSizeByPriceFacade,
)
from app.extend.money_management.sizers import (
    FixedAmount as FixedAmountFacade,
)
from app.extend.money_management.sizers import (
    FixedSize as FixedSizeFacade,
)
from app.extend.money_management.sizers import (
    PickerFixedAmount as PickerFixedAmountFacade,
)
from app.extend.money_management.sizers import (
    PickerRiskFixedPctOfAccount as PickerRiskFixedPctOfAccountFacade,
)
from app.extend.money_management.sizers import (
    RiskFixedBalancePct as RiskFixedBalancePctFacade,
)
from app.extend.money_management.sizers import (
    RiskFixedPctOfAccount as RiskFixedPctOfAccountFacade,
)
from app.extend.money_management.sizers import (
    SimpleMartingaleMM as SimpleMartingaleMMFacade,
)
from app.extend.money_management.sizers import (
    StocksSizeByPrice as StocksSizeByPriceFacade,
)
from app.extend.money_management.sizers import (
    _clamp_lots,
    _round_down,
)
from app.extend.money_management.sizing import (
    MAX_PERCENT,
    evaluate_sizing,
    fixed_lots,
    margin_percent,
    normalize_lots,
    risk_cash,
    risk_percent,
    volatility_risk,
)
from app.extend.money_management.stocks_size_by_price import StocksSizeByPrice


class DummyStrategy:
    """Mock strategy base for donor computeTradeSize validation."""

    def __init__(
        self,
        equity: float = 10000.0,
        balance: float = 10000.0,
        initial_balance: float = 10000.0,
        atr: float = 0.0020,
    ) -> None:
        self._equity = equity
        self._balance = balance
        self._initial = initial_balance
        self._atr = atr

    def get_account_equity(self) -> float:
        return self._equity

    def getAccountEquity(self) -> float:  # noqa: N802
        return self._equity

    def get_account_balance(self) -> float:
        return self._balance

    def getAccountBalance(self) -> float:  # noqa: N802
        return self._balance

    def get_initial_balance(self) -> float:
        return self._initial

    def getInitialBalance(self) -> float:  # noqa: N802
        return self._initial

    def get_atr_value(self, symbol: str, period: int) -> float:
        _ = (symbol, period)
        return self._atr

    def getATRValue(self, chart: Any, period: int, shift: int) -> float:  # noqa: N802
        _ = (chart, period, shift)
        return self._atr


class ConcreteSizer(BasePositionSizer):
    @override
    def compute_size(
        self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0
    ) -> float:
        return (account_equity / 10000.0) + (stop_loss_pips * pip_value * 0.0)


def test_base_contract_and_utilities() -> None:
    """Verify BasePositionSizer utilities, clamping, and default delegates."""
    sizer = ConcreteSizer()
    assert sizer.name == "BasePositionSizer"
    assert sizer.category == "MoneyManagement"
    assert sizer.sort_order == 100

    sizer.set_weight(1.5)
    assert sizer.weight == 1.5

    sizer.set_max_open_positions(3.0)
    assert sizer.max_pos == 3.0

    sizer.set_initial_capital(25000.0)
    assert sizer.initial_capital == 25000.0

    # Test round_down
    assert round_down(1.2399, 2) == 1.23
    assert round_down(-5.0, 2) == 0.0
    assert round_down(float("nan"), 2) == 0.0
    assert round_down(float("inf"), 2) == 0.0
    assert _round_down(2.559, 1) == 2.5

    # Test round_lots
    assert round_lots(0.126, 0.05, 2) == 0.10
    assert round_lots(-1.0, 0.01, 2) == 0.0
    assert round_lots(float("nan"), 0.01, 2) == 0.0
    assert round_lots(1.234, 0.0, 2) == 1.23

    # Test clamp_lots
    assert clamp_lots(0.005, decimals=2, lots_if_no_mm=0.1, min_lots=0.01) == 0.1
    assert clamp_lots(10.0, decimals=2, lots_if_no_mm=0.1, max_lots=5.0) == 5.0
    assert _clamp_lots(2.5, decimals=1, lots_if_no_mm=0.1) == 2.5

    # Test default compute_trade_size
    strategy = DummyStrategy(equity=12000.0)
    trade_size = sizer.compute_trade_size(
        strategy=strategy,
        price=1.1000,
        sl=1.0950,
        tick_size=0.0001,
        point_value=10.0,
    )
    assert trade_size == 1.2


def test_facade_reexports_match_classes() -> None:
    """Verify that sizers.py re-exports compatible classes to modular files."""
    assert issubclass(FixedSizeFacade, FixedSize)
    assert issubclass(FixedAmountFacade, FixedAmount)
    assert issubclass(RiskFixedPctOfAccountFacade, RiskFixedPctOfAccount)
    assert issubclass(RiskFixedBalancePctFacade, RiskFixedBalancePct)
    assert issubclass(ATRRiskBasedSizingFacade, ATRRiskBasedSizing)
    assert issubclass(StocksSizeByPriceFacade, StocksSizeByPrice)
    assert issubclass(CryptoFixedAmountFacade, CryptoFixedAmount)
    assert issubclass(CryptoFixedBalancePctFacade, CryptoFixedBalancePct)
    assert issubclass(CryptoSizeByPriceFacade, CryptoSizeByPrice)
    assert issubclass(PickerFixedAmountFacade, PickerFixedAmount)
    assert issubclass(PickerRiskFixedPctOfAccountFacade, PickerRiskFixedPctOfAccount)
    assert issubclass(SimpleMartingaleMMFacade, SimpleMartingaleMM)


def test_fixed_size_operations() -> None:
    """Verify FixedSize calculations, parameter aliases, and donor computeTradeSize."""
    s1 = FixedSize(size=0.25, decimals=2)
    assert s1.compute_size(10000.0, 20.0) == 0.25
    assert s1.compute_size(0.0, 0.0) == 0.25

    s2 = FixedSize(Size=0.5, Decimals=1)
    assert s2.compute_size(10000.0, 20.0) == 0.5
    s2.set_weight(2.0)
    assert s2.compute_trade_size(size_step=0.1) == 1.0


def test_fixed_amount_operations() -> None:
    """Verify FixedAmount calculations, stop loss edge cases, and limits."""
    s1 = FixedAmount(risked_money=200.0, decimals=2, lots_if_no_mm=0.1, max_lots=5.0)
    # Stop = 20 pips, pip_val = 10 => 200 / 200 = 1.0
    assert s1.compute_size(10000.0, 20.0, 10.0) == 1.0
    # Fallback path
    assert s1.compute_size(10000.0, 0.0, 10.0) == 0.1
    # Max lots cap
    assert s1.compute_size(10000.0, 1.0, 1.0) == 5.0

    # PascalCase aliases
    s2 = FixedAmount(RiskedMoney=300.0, Decimals=1, LotsIfNoMM=0.2, MaxLots=2.0)
    assert s2.risked_money == 300.0

    # compute_trade_size
    strategy = DummyStrategy()
    ts = s2.compute_trade_size(
        strategy=strategy,
        price=1.2000,
        sl=1.1900,
        tick_size=0.0001,
        point_value=10.0,
        size_step=0.01,
    )
    assert ts == 2.0

    # sl <= 0 fallback
    assert s2.compute_trade_size(price=1.2, sl=0.0) == 0.2

    # Negative money raises ValueError
    bad = FixedAmount(risked_money=-10.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size(price=1.0, sl=0.9)


def test_risk_fixed_pct_of_account_operations() -> None:
    """Verify RiskFixedPctOfAccount equity risk, StopLossInPips, and limits."""
    s1 = RiskFixedPctOfAccount(
        risk_in_pct=2.0, decimals=2, lots_if_no_mm=0.1, max_lots=10.0
    )
    assert s1.compute_size(10000.0, 20.0, 10.0) == 1.0
    # Fallback to StopLossInPips (100)
    assert s1.compute_size(10000.0, 0.0, 10.0) == 0.2
    # Zero equity fallback
    assert s1.compute_size(0.0, 20.0, 10.0) == 0.1

    # PascalCase
    s2 = RiskFixedPctOfAccount(
        Risk=3.0, Decimals=1, StopLossInPips=50, LotsIfNoMM=0.5, MaxLots=4.0
    )
    assert s2.risk_in_pct == 3.0

    strategy = DummyStrategy(equity=20000.0)
    ts = s2.compute_trade_size(
        strategy=strategy,
        price=1.1500,
        sl=1.1400,
        tick_size=0.0001,
        point_value=10.0,
        size_step=0.01,
    )
    assert ts == 4.0

    bad = RiskFixedPctOfAccount(risk_in_pct=-1.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size(price=1.0, sl=0.9)


def test_risk_fixed_balance_pct_operations() -> None:
    """Verify RiskFixedBalancePct balance risk calculations."""
    s1 = RiskFixedBalancePct(
        risk_in_pct=2.0,
        decimals=2,
        lots_if_no_mm=0.1,
        max_lots=10.0,
        account_balance=10000.0,
    )
    assert s1.compute_size(5000.0, 20.0, 10.0) == 1.0
    assert s1.compute_size(0.0, 0.0, 0.0) == 0.1

    strategy = DummyStrategy(balance=15000.0)
    ts = s1.compute_trade_size(
        strategy=strategy,
        price=1.1000,
        sl=1.0900,
        tick_size=0.0001,
        point_value=10.0,
        size_step=0.01,
    )
    assert ts > 0.0

    # sl <= 0 fallback
    assert s1.compute_trade_size(price=1.0, sl=0.0) == 0.1

    bad = RiskFixedBalancePct(risk_in_pct=-5.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size(price=1.0, sl=0.9)


def test_atr_risk_based_sizing_operations() -> None:
    """Verify ATRRiskBasedSizing stop calculation, mock ATR retrieval, and caps."""
    s1 = ATRRiskBasedSizing(
        risk_in_pct=2.0,
        atr_period=14,
        atr_multiplier=2.0,
        decimals=2,
        lots_if_no_mm=0.1,
        max_lots=10.0,
    )
    assert s1.compute_size(10000.0, 20.0, 10.0) == 0.5
    # Zero stop fallback
    assert s1.compute_size(10000.0, 0.0, 10.0) == 0.1

    # PascalCase
    s2 = ATRRiskBasedSizing(
        Risk=3.0,
        ATRPeriod=20,
        ATRMult=1.5,
        Decimals=1,
        LotsIfNoMM=0.2,
        MaxLots=5.0,
    )
    assert s2.atr_period == 20

    strategy = DummyStrategy(equity=10000.0, atr=0.0010)
    ts = s2.compute_trade_size(strategy=strategy, symbol="EURUSD", size_step=0.01)
    assert ts > 0.0

    bad = ATRRiskBasedSizing(risk_in_pct=-1.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size()

    # _extract_atr helper branch coverage
    assert _extract_atr(None, "EURUSD", 14) == 0.0

    class LegacyStrategy:
        def __init__(self) -> None:
            self.MarketData = self

        def Chart(self, _s: str) -> str:  # noqa: N802
            return "chart"

        def getATRValue(self, _chart: str, _p: int, _s: int) -> float:  # noqa: N802
            return 0.0015

    assert _extract_atr(LegacyStrategy(), "EURUSD", 14) == 0.0015


def test_stocks_size_by_price_operations() -> None:
    """Verify StocksSizeByPrice capital allocation by stock share price."""
    s1 = StocksSizeByPrice(
        capital_pct=50.0, decimals=0, lots_if_no_mm=1.0, max_lots=500.0
    )
    assert s1.compute_size(10000.0, 0.0, 50.0) == 100.0
    # Zero price fallback
    assert s1.compute_size(10000.0, 0.0, 0.0) == 1.0

    # PascalCase
    s2 = StocksSizeByPrice(UseAccountBalance=False, MaxSize=200.0, Decimals=0)
    assert not s2.use_account_balance
    assert s2.max_lots == 200.0

    strategy = DummyStrategy(balance=20000.0, initial_balance=10000.0)
    ts = s2.compute_trade_size(strategy=strategy, price=50.0, size_step=1.0)
    assert ts == 200.0

    # price <= 0 fallback
    assert s2.compute_trade_size(price=0.0) == 1.0


def test_crypto_fixed_amount_operations() -> None:
    """Verify CryptoFixedAmount quote currency sizing."""
    s1 = CryptoFixedAmount(
        risked_money=100.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
    )
    assert s1.compute_size(10000.0, 20.0, 10.0) == 0.5
    assert s1.compute_size(0.0, 0.0, 0.0) == 0.01

    ts = s1.compute_trade_size(price=500.0, size_step=0.001)
    assert ts == 0.2

    bad = CryptoFixedAmount(risked_money=-10.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size(price=100.0)


def test_crypto_fixed_balance_pct_operations() -> None:
    """Verify CryptoFixedBalancePct percentage sizing for crypto."""
    s1 = CryptoFixedBalancePct(
        risk_in_pct=2.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
    )
    assert s1.compute_size(10000.0, 20.0, 10.0) == 1.0
    assert s1.compute_size(0.0, 0.0, 0.0) == 0.01

    strategy = DummyStrategy(balance=10000.0)
    ts = s1.compute_trade_size(strategy=strategy, price=2000.0, size_step=0.001)
    assert ts == 0.1

    bad = CryptoFixedBalancePct(risk_in_pct=-2.0)
    with pytest.raises(ValueError, match="Call init"):
        bad.compute_trade_size(price=100.0)


def test_crypto_size_by_price_operations() -> None:
    """Verify CryptoSizeByPrice capital allocation by coin price."""
    s1 = CryptoSizeByPrice(
        capital_pct=10.0, decimals=4, lots_if_no_mm=0.01, max_lots=50.0
    )
    assert s1.compute_size(10000.0, 0.0, 50.0) == 20.0
    assert s1.compute_size(0.0, 0.0, 0.0) == 0.01

    strategy = DummyStrategy(balance=10000.0)
    ts = s1.compute_trade_size(strategy=strategy, price=200.0, size_step=0.001)
    assert ts == 50.0


def test_picker_fixed_amount_operations() -> None:
    """Verify PickerFixedAmount integer and fractional share sizing."""
    s1 = PickerFixedAmount(
        amount=1000.0, decimals=0, lots_if_no_mm=1.0, max_lots=1000.0
    )
    assert s1.compute_size(10000.0, 0.0, 50.0) == 20.0
    assert s1.compute_size(0.0, 0.0, 0.0) == 1.0

    # Donor computeTradeSize without fractional shares
    ts = s1.compute_trade_size(price=40.0)
    assert ts == 25.0

    # With fractional shares enabled
    s_frac = PickerFixedAmount(
        amount=1000.0,
        allow_fractional_shares=True,
        fractional_decimal_numbers=2,
        fractional_step=0.05,
    )
    ts_f = s_frac.compute_trade_size(price=30.0)
    assert math.isclose(ts_f, 33.35, abs_tol=0.05)

    # Error conditions
    with pytest.raises(ValueError, match=r"invalid.*price"):
        s1.compute_trade_size(price=0.0)

    with pytest.raises(ValueError, match=r"trade size.*< 1"):
        s1.compute_trade_size(price=2000.0)


def test_picker_risk_fixed_pct_of_account_operations() -> None:
    """Verify PickerRiskFixedPctOfAccount equity risk across positions."""
    s1 = PickerRiskFixedPctOfAccount(
        risk_in_pct=10.0, decimals=0, lots_if_no_mm=1.0, max_lots=1000.0
    )
    assert s1.compute_size(10000.0, 0.0, 50.0) == 20.0
    assert s1.compute_size(0.0, 0.0, 0.0) == 1.0

    strategy = DummyStrategy(equity=20000.0)
    ts = s1.compute_trade_size(strategy=strategy, price=50.0)
    assert ts == 40.0

    s_frac = PickerRiskFixedPctOfAccount(
        risk_in_pct=10.0,
        allow_fractional_shares=True,
        fractional_decimal_numbers=2,
        fractional_step=0.01,
    )
    ts_f = s_frac.compute_trade_size(strategy=strategy, price=30.0)
    assert math.isclose(ts_f, 66.67, abs_tol=0.05)

    with pytest.raises(ValueError, match=r"invalid.*price"):
        s1.compute_trade_size(price=-5.0)

    with pytest.raises(ValueError, match=r"trade size.*< 1"):
        s1.compute_trade_size(strategy=strategy, price=50000.0)


def test_simple_martingale_operations() -> None:
    """Verify SimpleMartingaleMM streak progression, resets, and direction."""
    martingale = SimpleMartingaleMM(
        mm_StartLots=0.1, mm_Multiplier=2.0, mm_MaxLots=0.5, mm_Decimals=2
    )
    assert martingale.compute_size(10000.0, 20.0) == 0.1

    # Loss streak
    martingale.record_trade_outcome(-50.0)
    assert martingale.compute_size(10000.0, 20.0) == 0.2

    martingale.record_trade_outcome(-50.0)
    assert martingale.compute_size(10000.0, 20.0) == 0.4

    # 0.8 > max_lots (0.5) -> resets to start_lots (0.1)
    martingale.record_trade_outcome(-50.0)
    assert martingale.compute_size(10000.0, 20.0) == 0.1

    # Profit resets consecutive losses
    martingale.record_trade_outcome(100.0)
    assert martingale.consecutive_losses == 0

    # Direction separation
    m_dir = SimpleMartingaleMM(
        start_lots=0.1,
        multiplier=2.0,
        max_lots=10.0,
        separate_by_direction=True,
    )
    m_dir.record_trade_outcome(-10.0, direction=1)
    # Long order gets multiplied
    assert m_dir.compute_trade_size(order_type=1, size_step=0.01) == 0.2
    # Short order remains at starting size
    assert m_dir.compute_trade_size(order_type=-1, size_step=0.01) == 0.1

    # Short order profit resets short streak
    m_dir.record_trade_outcome(-10.0, direction=-1)
    assert m_dir.compute_trade_size(order_type=-1, size_step=0.01) == 0.2
    m_dir.record_trade_outcome(20.0, direction=-1)
    assert m_dir.compute_trade_size(order_type=-1, size_step=0.01) == 0.1
    # Long still has streak
    assert m_dir.compute_trade_size(order_type=1, size_step=0.01) == 0.2


def test_sizing_module_functions() -> None:
    """Verify auxiliary sizing algorithms in app.extend.money_management.sizing."""
    assert MAX_PERCENT == 100.0

    # normalize_lots
    assert normalize_lots(0.126, min_lot=0.01, max_lot=10.0, lot_step=0.05) == 0.15
    assert normalize_lots(0.0, min_lot=0.1, max_lot=5.0, lot_step=0.01) == 0.0
    assert normalize_lots(0.02, min_lot=0.1, max_lot=5.0, lot_step=0.01) == 0.1
    assert normalize_lots(20.0, min_lot=0.1, max_lot=5.0, lot_step=0.01) == 5.0
    with pytest.raises(ValueError, match="Trade volume"):
        normalize_lots(-1.0, min_lot=0.1, max_lot=5.0, lot_step=0.01)
    with pytest.raises(ValueError, match="Trade volume"):
        normalize_lots(float("nan"), min_lot=0.1, max_lot=5.0, lot_step=0.01)

    # fixed_lots
    assert fixed_lots(0.5, min_lot=0.1, max_lot=5.0, lot_step=0.1) == 0.5
    with pytest.raises(ValueError, match="min_lot"):
        fixed_lots(0.5, min_lot=5.0, max_lot=1.0)
    with pytest.raises(ValueError, match="lot_step"):
        fixed_lots(0.5, min_lot=0.1, max_lot=5.0, lot_step=-0.1)

    # risk_percent
    assert risk_percent(10000.0, 2.0, 50.0, 10.0) == 0.4
    with pytest.raises(ValueError, match=r"(?i)equity"):
        risk_percent(-100.0, 2.0, 50.0, 10.0)
    with pytest.raises(ValueError, match=r"(?i)risk percentage"):
        risk_percent(10000.0, -1.0, 50.0, 10.0)
    with pytest.raises(ValueError, match=r"(?i)stop loss"):
        risk_percent(10000.0, 2.0, 0.0, 10.0)
    with pytest.raises(ValueError, match=r"(?i)pip value"):
        risk_percent(10000.0, 2.0, 50.0, 0.0)

    # risk_cash
    assert risk_cash(200.0, 50.0, 10.0) == 0.4
    with pytest.raises(ValueError, match=r"(?i)cash amount"):
        risk_cash(-10.0, 50.0, 10.0)
    with pytest.raises(ValueError, match=r"(?i)stop loss"):
        risk_cash(200.0, 0.0, 10.0)
    with pytest.raises(ValueError, match=r"(?i)pip value"):
        risk_cash(200.0, 50.0, 0.0)

    # volatility_risk
    assert volatility_risk(200.0, 2.0, 1.0, 2.0) == 50.0
    with pytest.raises(ValueError, match="Cash risk"):
        volatility_risk(-1.0, 0.0020, 1.0, 2.0)
    with pytest.raises(ValueError, match="ATR volatility"):
        volatility_risk(200.0, 0.0, 1.0, 2.0)
    with pytest.raises(ValueError, match="multiplier"):
        volatility_risk(200.0, 0.0020, 1.0, 0.0)
    with pytest.raises(ValueError, match="Point value"):
        volatility_risk(200.0, 0.0020, 0.0, 2.0)

    # margin_percent
    assert (
        margin_percent(10000.0, 10.0, 1.0, contract_size=100000.0, leverage=100.0)
        == 1.0
    )
    with pytest.raises(ValueError, match="equity"):
        margin_percent(-1.0, 10.0, 1.0)
    with pytest.raises(ValueError, match="Margin percentage"):
        margin_percent(10000.0, 0.0, 1.0)
    with pytest.raises(ValueError, match="price"):
        margin_percent(10000.0, 10.0, 0.0)
    with pytest.raises(ValueError, match="Leverage"):
        margin_percent(10000.0, 10.0, 1.0, leverage=-5.0)

    # evaluate_sizing
    assert evaluate_sizing("fixed", lots=0.5) == 0.5
    assert (
        evaluate_sizing(
            "cash_risk", cash_amount=200.0, stop_distance_pips=50.0, pip_value=10.0
        )
        == 0.4
    )
    assert (
        evaluate_sizing(
            "percent_equity",
            equity=10000.0,
            risk_pct=2.0,
            stop_distance_pips=50.0,
            pip_value=10.0,
        )
        == 0.4
    )
    assert (
        evaluate_sizing("percent_margin", equity=10000.0, margin_pct=10.0, price=1.0)
        > 0.0
    )
    assert (
        evaluate_sizing(
            "volatility",
            cash_amount=200.0,
            atr_value=0.0020,
            multiplier=2.0,
            point_value=1.0,
        )
        > 0.0
    )
    with pytest.raises(ValueError, match="Unknown sizing"):
        evaluate_sizing("unknown")  # type: ignore[arg-type]


def test_stocks_and_crypto_size_by_price_edge_cases() -> None:
    """Verify edge cases and exception handling for StocksSizeByPrice and CryptoSizeByPrice."""
    # StocksSizeByPrice
    bad_stocks = StocksSizeByPrice(max_lots=-5.0)
    with pytest.raises(ValueError, match="Call init"):
        bad_stocks.compute_trade_size(price=50.0)

    class SQLegacyStrategy:
        def __init__(self) -> None:
            pass

        def getAccountBalance(self) -> float:  # noqa: N802
            return 5000.0

        def getInitialBalance(self) -> float:  # noqa: N802
            return 2000.0

    leg_strat = SQLegacyStrategy()
    s_stocks = StocksSizeByPrice(use_account_balance=True, max_lots=100.0)
    assert s_stocks.compute_trade_size(strategy=leg_strat, price=100.0) == 50.0

    s_stocks_init = StocksSizeByPrice(use_account_balance=False, max_lots=100.0)
    assert s_stocks_init.compute_trade_size(strategy=leg_strat, price=100.0) == 20.0

    # CryptoSizeByPrice
    bad_crypto = CryptoSizeByPrice(max_lots=-1.0)
    with pytest.raises(ValueError, match="Call init"):
        bad_crypto.compute_trade_size(price=100.0)

    s_crypto_init = CryptoSizeByPrice(use_account_balance=False, max_lots=50.0)
    assert s_crypto_init.compute_trade_size(strategy=leg_strat, price=100.0) == 20.0


def test_atr_and_martingale_additional_edge_cases() -> None:
    """Verify ATR and Martingale additional edge cases."""
    # ATR with zero ATR value
    dummy = DummyStrategy(atr=0.0)
    atr_sizer = ATRRiskBasedSizing(lots_if_no_mm=0.25, max_lots=5.0)
    assert atr_sizer.compute_trade_size(strategy=dummy, symbol="EURUSD") == 0.25

    # Martingale negative start lots
    bad_mart = SimpleMartingaleMM(start_lots=-1.0)
    with pytest.raises(ValueError, match="Call init"):
        bad_mart.compute_trade_size()

    # Martingale exceeding max lots resets to start_lots
    mart_cap = SimpleMartingaleMM(start_lots=0.1, multiplier=10.0, max_lots=0.5)
    mart_cap.record_trade_outcome(-10.0)
    # 0.1 * 10 = 1.0 > 0.5 -> resets to 0.1
    assert mart_cap.compute_trade_size() == 0.1
