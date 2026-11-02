"""Unit tests for StrategyQuant Trading extension snippets and registries.

Description:
    Tests all 6 StrategyQuant trading classes (None, PercentageBased, PerTrade,
    SizeBased, Stockpicker, and NoScaling) along with base contracts, helper
    functions, XML serialization/deserialization, and registry lookup mechanisms.

Purpose:
    FEAT-TRADING-TESTS: Verify 100% fidelity and coverage for SQ Trading snippets.

Key Capabilities:
    - FR-TEST-TRADING-COMMISSIONS: Test all commission calculation formulas and caps.
    - FR-TEST-TRADING-SCALING: Test scaling pass-through and order scaling.
    - FR-TEST-TRADING-REGISTRIES: Test class factory registration and lookup.

Python API Usage:
    uv run pytest tests/extend/test_trading_catalog.py --cov=app.extend.trading
"""

from __future__ import annotations

from typing import Any

import pytest
from app.extend.strategies.base import ILiveOrder, OrderTypes
from app.extend.trading import (
    BaseCommissionModel,
    CommissionsMethod,
    CommissionsMethodsList,
    NoneCommission,
    NoneMethod,
    NoScaling,
    PercentageBased,
    PercentageBasedCommission,
    PerTrade,
    PerTradeCommission,
    ScalingMethod,
    ScalingMethodsList,
    SizeBased,
    SizeBasedCommission,
    Stockpicker,
    StockpickerCommission,
)
from app.extend.trading.commissions.base import (
    get_order_close_price,
    get_order_open_price,
    get_order_size,
    is_pending_order,
)


class MockOrderWithProps:
    """Mock order exposing attributes directly without getter methods."""

    def __init__(
        self,
        size: float = 1.0,
        open_price: float = 100.0,
        close_price: float = 105.0,
        is_pending: bool = False,
    ) -> None:
        self.size = size
        self.open_price = open_price
        self.close_price = close_price
        self.is_pending = is_pending


class MockOrderWithPendingFlag:
    """Mock order exposing is_pending_order attribute."""

    def __init__(self, is_pending_order: bool = True) -> None:
        self.is_pending_order = is_pending_order


def test_order_inspection_helpers() -> None:
    """Verify order inspection helper functions across various representations."""
    # 1. ILiveOrder instance
    live_order = ILiveOrder("EURUSD", OrderTypes.Buy, size=2.5, price=1.1200)
    assert get_order_size(live_order) == 2.5
    assert get_order_open_price(live_order) == 1.1200
    assert get_order_close_price(live_order) == 0.0
    assert is_pending_order(live_order) is False

    # Pending ILiveOrder
    pending_order = ILiveOrder("EURUSD", OrderTypes.BuyLimit, size=1.0, price=1.1100)
    assert is_pending_order(pending_order) is True

    # 2. MockOrderWithProps
    prop_order = MockOrderWithProps(
        size=3.0, open_price=50.0, close_price=55.0, is_pending=True
    )
    assert get_order_size(prop_order) == 3.0
    assert get_order_open_price(prop_order) == 50.0
    assert get_order_close_price(prop_order) == 55.0
    assert is_pending_order(prop_order) is True

    # 3. MockOrderWithPendingFlag
    flag_order = MockOrderWithPendingFlag(is_pending_order=True)
    assert is_pending_order(flag_order) is True

    # 4. Dictionary order representation
    dict_order: dict[str, Any] = {
        "size": 4.5,
        "open_price": 200.0,
        "close_price": 210.0,
        "is_pending": False,
    }
    assert get_order_size(dict_order) == 4.5
    assert get_order_open_price(dict_order) == 200.0
    assert get_order_close_price(dict_order) == 210.0
    assert is_pending_order(dict_order) is False

    # 5. Numeric and fallback representations
    assert get_order_size(5.0) == 5.0
    assert get_order_size("invalid") == 1.0
    assert get_order_open_price("invalid") == 0.0
    assert get_order_close_price("invalid") == 0.0
    assert is_pending_order("invalid") is False


def test_none_commission() -> None:
    """Verify NoneCommission unconditional 0.0 behavior and XML round-trip."""
    c = NoneCommission()
    assert c.name == "None"
    assert c.display == "No commissions"
    assert issubclass(NoneMethod, CommissionsMethod)
    assert issubclass(BaseCommissionModel, CommissionsMethod)

    order = ILiveOrder("EURUSD", OrderTypes.Buy, size=5.0, price=1.2000)
    assert c.computeCommissionsOnOpen(order, tickSize=0.0001, pointValue=1.0) == 0.0
    assert c.computeCommissionsOnClose(order, tickSize=0.0001, pointValue=1.0) == 0.0
    assert c.compute_commission(size=5.0, open_price=1.2000) == 0.0

    xml = c.getXML()
    assert xml["tag"] == "Commissions"
    assert xml["children"][0]["attributes"]["type"] == "NoneCommission"

    c2 = NoneCommission()
    c2.setFromXML(xml)
    assert c2.name == "NoneCommission"


def test_percentage_based_commission() -> None:
    """Verify PercentageBased commission calculation and aliases."""
    c = PercentageBased(CommissionPct=0.2)
    assert c.commission_pct == 0.2

    order = ILiveOrder("AAPL", OrderTypes.Buy, size=10.0, price=150.0)
    # 0.2% of (10 * 150 * 1.0) = 0.002 * 1500 = 3.0
    open_fee = c.computeCommissionsOnOpen(order, pointValue=1.0)
    assert open_fee == pytest.approx(3.0)
    close_fee = c.computeCommissionsOnClose(order, pointValue=1.0)
    assert close_fee == 0.0

    # Legacy keyword calculation
    total_fee = c.compute_commission(
        size=10.0, open_price=150.0, close_price=150.0, point_value=1.0
    )
    assert total_fee == pytest.approx(3.0)

    # Initialized via snake_case keyword
    c_snake = PercentageBasedCommission(commission_pct=0.1)
    assert c_snake.CommissionPct == 0.1

    # XML round-trip
    xml = c.getXML()
    assert xml["children"][0]["parameters"]["CommissionPct"] == 0.2
    c3 = PercentageBased(CommissionPct=0.0)
    c3.setFromXML(xml)
    assert c3.CommissionPct == 0.2


def test_per_trade_commission() -> None:
    """Verify PerTrade commission charges per trade side and skips pending orders."""
    c = PerTrade(Commission=7.5)
    assert c.commission == 7.5

    active_order = ILiveOrder("EURUSD", OrderTypes.Buy, size=2.0, price=1.1000)
    assert c.computeCommissionsOnOpen(active_order) == 7.5
    assert c.computeCommissionsOnClose(active_order) == 7.5

    pending_order = ILiveOrder("EURUSD", OrderTypes.BuyLimit, size=2.0, price=1.0900)
    assert c.computeCommissionsOnOpen(pending_order) == 7.5
    assert c.computeCommissionsOnClose(pending_order) == 0.0

    # Zero size order
    zero_order = ILiveOrder("EURUSD", OrderTypes.Buy, size=0.0, price=1.1000)
    assert c.computeCommissionsOnOpen(zero_order) == 0.0
    assert c.computeCommissionsOnClose(zero_order) == 0.0

    # Legacy compute_commission
    assert c.compute_commission(size=2.0, open_price=100.0) == 7.5
    assert c.compute_commission(size=0.0, open_price=100.0) == 0.0

    # Initialized via snake_case
    c_snake = PerTradeCommission(commission=6.0)
    assert c_snake.Commission == 6.0

    # XML round-trip
    xml = c.getXML()
    assert xml["children"][0]["parameters"]["Commission"] == 7.5
    c_deser = PerTrade(Commission=0.0)
    c_deser.setFromXML(xml)
    assert c_deser.Commission == 7.5


def test_size_based_commission() -> None:
    """Verify SizeBased commission proportional to lot volume."""
    c = SizeBased(Commission=8.0)
    assert c.commission_per_lot == 8.0

    order = ILiveOrder("EURUSD", OrderTypes.Buy, size=3.5, price=1.1000)
    assert c.computeCommissionsOnOpen(order) == pytest.approx(28.0)
    assert c.computeCommissionsOnClose(order) == 0.0

    # Legacy compute_commission
    total = c.compute_commission(size=2.5, open_price=1.1000)
    assert total == pytest.approx(20.0)

    # Initialized via snake_case
    c_snake = SizeBasedCommission(commission_per_lot=5.0)
    assert c_snake.Commission == 5.0

    # XML round-trip
    xml = c.getXML()
    assert xml["children"][0]["parameters"]["Commission"] == 8.0
    c_deser = SizeBased(Commission=0.0)
    c_deser.setFromXML(xml)
    assert c_deser.Commission == 8.0


def test_stockpicker_commission_share_mode() -> None:
    """Verify Stockpicker commission in share mode with min and max bounds."""
    # 1. Base share mode with bounds
    c = Stockpicker(
        Commission=0.005,
        CommissionType="share",
        MinPerOrder=1.0,
        MinPerOrderType="money",
        MaxPerOrder=1.0,
        MaxPerOrderType="equity",
    )
    assert c.min_commission == 1.0
    assert c.max_commission_pct == 1.0
    assert c.per_share_commission == 0.005
    assert c.percentage_commission == 0.0

    # Low volume: 50 shares * 0.005 = 0.25 -> clamped to minCommission 1.0
    order_low = ILiveOrder("MSFT", OrderTypes.Buy, size=50.0, price=100.0)
    assert c.computeCommissionsOnOpen(order_low) == 1.0
    assert c.computeCommissionsOnClose(order_low) == 1.0

    # Normal volume: 500 shares * 0.005 = 2.5 (equity = 500 * 100 = 50,000; 1% cap = 500)
    order_med = ILiveOrder("MSFT", OrderTypes.Buy, size=500.0, price=100.0)
    assert c.computeCommissionsOnOpen(order_med) == 2.5

    # Capped volume: penny stock where fee exceeds 1% of trade value
    # 10,000 shares at $0.02 = $200 equity. Fee = 10,000 * 0.005 = $50. Cap 1% of $200 = $2.0
    order_penny = ILiveOrder("PENNY", OrderTypes.Buy, size=10000.0, price=0.02)
    assert c.computeCommissionsOnOpen(order_penny) == pytest.approx(2.0)


def test_stockpicker_commission_order_and_equity_modes() -> None:
    """Verify Stockpicker commission in order mode and equity percent mode."""
    # Order mode
    c_order = Stockpicker(
        Commission=4.95,
        CommissionType="order",
        MinPerOrder=2.0,
        MinPerOrderType="money",
        MaxPerOrder=10.0,
        MaxPerOrderType="money",
    )
    order = ILiveOrder("SPY", OrderTypes.Buy, size=100.0, price=400.0)
    assert c_order.computeCommissionsOnOpen(order) == 4.95

    # Equity percent mode
    c_equity = Stockpicker(
        Commission=0.1,  # 0.1%
        CommissionType="equity",
        MinPerOrder=0.05,  # 0.05%
        MinPerOrderType="equity",
        MaxPerOrder=0.5,  # 0.5%
        MaxPerOrderType="equity",
    )
    assert c_equity.percentage_commission == 0.1
    # 100 * 200 = 20,000 equity. 0.1% = 20.0
    order_eq = ILiveOrder("QQQ", OrderTypes.Buy, size=100.0, price=200.0)
    assert c_equity.computeCommissionsOnOpen(order_eq) == pytest.approx(20.0)


def test_stockpicker_edge_cases_and_validation() -> None:
    """Verify Stockpicker non-positive values, invalid modes, and legacy kwargs."""
    c = Stockpicker(Commission=0.01, CommissionType="share")

    # Non-positive size or price
    zero_size = ILiveOrder("SYM", OrderTypes.Buy, size=0.0, price=100.0)
    assert c.computeCommissionsOnOpen(zero_size) == 0.0

    zero_price = ILiveOrder("SYM", OrderTypes.Buy, size=10.0, price=0.0)
    assert c.computeCommissionsOnOpen(zero_price) == 0.0

    # Invalid commission type
    c_bad_type = Stockpicker(CommissionType="invalid")
    order = ILiveOrder("SYM", OrderTypes.Buy, size=10.0, price=10.0)
    with pytest.raises(ValueError, match="Invalid commission type"):
        c_bad_type.computeCommissionsOnOpen(order)

    # Invalid min per order type
    c_bad_min = Stockpicker(MinPerOrderType="invalid")
    with pytest.raises(ValueError, match="Invalid min per order type"):
        c_bad_min.computeCommissionsOnOpen(order)

    # Invalid max per order type
    c_bad_max = Stockpicker(MaxPerOrderType="invalid")
    with pytest.raises(ValueError, match="Invalid max per order type"):
        c_bad_max.computeCommissionsOnOpen(order)

    # Initialized via legacy kwargs
    c_legacy = StockpickerCommission(
        min_commission=1.5,
        max_commission_pct=2.0,
        per_share_commission=0.02,
        percentage_commission=0.0,
    )
    assert c_legacy.MinPerOrder == 1.5
    assert c_legacy.MaxPerOrder == 2.0
    assert c_legacy.Commission == 0.02
    assert c_legacy.CommissionType == "share"

    c_legacy_pct = StockpickerCommission(
        min_commission=1.0,
        max_commission_pct=5.0,
        per_share_commission=None,
        percentage_commission=0.25,
    )
    assert c_legacy_pct.Commission == 0.25
    assert c_legacy_pct.CommissionType == "equity"

    # XML round-trip
    xml = c.getXML()
    c_deser = Stockpicker()
    c_deser.setFromXML(xml)
    assert c_deser.Commission == 0.01


def test_no_scaling_method() -> None:
    """Verify NoScaling pass-through logic and XML serialization."""
    s = NoScaling()
    assert s.name == "No scaling"
    assert s.display == "No scaling"
    assert issubclass(NoScaling, ScalingMethod)

    assert s.scale_size(5.0) == 5.0
    assert s.scale_size(0.0) == 0.0
    assert s.scale_size(-2.0) == 0.0

    orders = ["order1", "order2"]
    assert s.scale_orders(orders) == orders

    xml = s.getXML()
    assert xml["tag"] == "Scaling"
    assert xml["children"][0]["attributes"]["type"] == "NoScaling"

    s_deser = NoScaling()
    s_deser.setFromXML(xml)
    assert s_deser.name == "NoScaling"


def test_registries_and_error_handling() -> None:
    """Verify CommissionsMethodsList and ScalingMethodsList registry behavior."""
    # Verify backward-compatibility package exports
    import app.extend.trading.commissions as legacy_mod

    assert legacy_mod.BaseCommissionModel is CommissionsMethod
    assert legacy_mod.NoneCommission is NoneCommission
    assert legacy_mod.NoScaling is NoScaling

    # Verify commissions.py module directly
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "app.extend.trading.commissions_file",
        "app/extend/trading/commissions.py",
    )
    assert spec is not None and spec.loader is not None
    comm_file_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comm_file_mod)
    assert comm_file_mod.BaseCommissionModel is CommissionsMethod
    assert comm_file_mod.NoScaling is NoScaling

    comm_registry = CommissionsMethodsList.get()
    assert comm_registry is CommissionsMethodsList.get()

    available_comms = CommissionsMethodsList.list_available()
    assert "None" in available_comms
    assert "PercentageBased" in available_comms
    assert "PerTrade" in available_comms
    assert "SizeBased" in available_comms
    assert "Stockpicker" in available_comms
    assert len(CommissionsMethodsList.get_available_classes()) >= 5

    # Creation
    inst = CommissionsMethodsList.create("PerTrade", Commission=12.0)
    assert isinstance(inst, PerTrade)
    assert inst.Commission == 12.0

    # Nonexistent class
    with pytest.raises(KeyError, match="Nonexisting custom class"):
        CommissionsMethodsList.create("NonexistentMethod")

    # ScalingMethodsList
    scaling_registry = ScalingMethodsList.get()
    assert scaling_registry is ScalingMethodsList.get()

    available_scalings = ScalingMethodsList.list_available()
    assert "NoScaling" in available_scalings
    assert len(ScalingMethodsList.get_available_classes()) >= 1

    scaling_inst = ScalingMethodsList.create("NoScaling")
    assert isinstance(scaling_inst, NoScaling)

    with pytest.raises(KeyError, match="Nonexisting custom class"):
        ScalingMethodsList.create("NonexistentScaling")

    # setFromXML error handling
    invalid_xml = {"tag": "Commissions", "children": []}
    per_trade = PerTrade()
    with pytest.raises(ValueError, match="Method xml element not found"):
        per_trade.setFromXML(invalid_xml)

    no_scaling = NoScaling()
    with pytest.raises(ValueError, match="Method xml element not found"):
        no_scaling.setFromXML(invalid_xml)
