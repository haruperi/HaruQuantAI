"""Unit tests for SQ.Functions extension cohort matching donor snippets.

Description:
    Validates ComparatorByProfit, DailyEquityComputer, StatFunctions, and
    OrderFunctions, alongside existing pure domain utilities (TradeFilter,
    normalize_price, bars_since, pip_size, aware_timestamp).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.core.data.contracts import (
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    SymbolPrice,
)
from app.extend.functions import (
    PL_TYPE_MONEY,
    PL_TYPE_PERCENT,
    PL_TYPE_PIPS,
    ComparatorByProfit,
    DailyEquityComputer,
    OrderFunctions,
    StatFunctions,
    TradeFilter,
    aware_timestamp,
    bars_since,
    normalize_price,
    pip_size,
)


@dataclass
class DummyOrder:
    """Mock order object supporting profit attributes and timestamps."""

    ticket: int = 1
    symbol: str = "EURUSD"
    direction: int = 1
    magic_number: int = 100
    comment: str = "TestOrder"
    strategy_name: str = "Strategy1"
    pl: float = 100.0
    pips_pl: float = 10.0
    pct_pl: float = 1.0
    close_time_ms: int = 100_000_000
    is_canceled: bool = False

    def is_filled_order(self) -> bool:
        """Return True if order is filled."""
        return not self.is_canceled


@dataclass
class DummyChart:
    """Mock chart object."""

    symbol: str = "EURUSD"


class DummyMarketData:
    """Mock MarketData with primary chart."""

    def __init__(self, chart: DummyChart) -> None:
        self._chart = chart

    def chart(self, index: int) -> DummyChart:
        return self._chart


class DummyTrader:
    """Mock trader managing open and history orders."""

    def __init__(
        self,
        open_orders: list[Any] | None = None,
        history_orders: list[Any] | None = None,
    ) -> None:
        self.open_orders = open_orders or []
        self.history_orders = history_orders or []


class DummyStrategy:
    """Mock strategy holding market data and trader."""

    def __init__(
        self,
        name: str = "Strategy1",
        chart_symbol: str = "EURUSD",
        trader: DummyTrader | None = None,
    ) -> None:
        self.strategy_name = name
        self.market_data = DummyMarketData(DummyChart(chart_symbol))
        self.trader = trader or DummyTrader()


class TestComparatorByProfit:
    """Test suite for ComparatorByProfit matching donor ComparatorByProfit.java."""

    def test_compare_money(self) -> None:
        """Verify comparison by monetary profit descending."""
        comp = ComparatorByProfit(PL_TYPE_MONEY)
        o_high = DummyOrder(ticket=1, pl=200.0)
        o_low = DummyOrder(ticket=2, pl=50.0)
        o_equal = DummyOrder(ticket=3, pl=200.0)

        assert comp.compare(o_high, o_low) == -1
        assert comp.compare(o_low, o_high) == 1
        assert comp.compare(o_high, o_equal) == 0

    def test_compare_pips(self) -> None:
        """Verify comparison by pips profit descending."""
        comp = ComparatorByProfit(PL_TYPE_PIPS)
        o_high = DummyOrder(ticket=1, pips_pl=50.0)
        o_low = DummyOrder(ticket=2, pips_pl=10.0)
        o_equal = DummyOrder(ticket=3, pips_pl=50.0)

        assert comp.compare(o_high, o_low) == -1
        assert comp.compare(o_low, o_high) == 1
        assert comp.compare(o_high, o_equal) == 0

    def test_compare_percent(self) -> None:
        """Verify comparison by percent profit descending."""
        comp = ComparatorByProfit(PL_TYPE_PERCENT)
        o_high = DummyOrder(ticket=1, pct_pl=5.0)
        o_low = DummyOrder(ticket=2, pct_pl=1.0)
        o_equal = DummyOrder(ticket=3, pct_pl=5.0)

        assert comp.compare(o_high, o_low) == -1
        assert comp.compare(o_low, o_high) == 1
        assert comp.compare(o_high, o_equal) == 0

    def test_sort_key(self) -> None:
        """Verify key function orders descending."""
        comp = ComparatorByProfit(PL_TYPE_MONEY)
        orders = [
            DummyOrder(ticket=1, pl=10.0),
            DummyOrder(ticket=2, pl=100.0),
            DummyOrder(ticket=3, pl=50.0),
        ]
        orders.sort(key=comp.key)
        assert [o.ticket for o in orders] == [2, 3, 1]

    def test_extract_pl_fallbacks(self) -> None:
        """Verify PL extraction fallbacks across alternative names."""
        comp_m = ComparatorByProfit(PL_TYPE_MONEY)
        comp_pip = ComparatorByProfit(PL_TYPE_PIPS)
        comp_pct = ComparatorByProfit(PL_TYPE_PERCENT)

        class AltOrder:
            PL = 75.0
            PipsPL = 8.0
            PctPL = 2.5

        class AltProfitOrder:
            profit = 35.0
            profit_loss_pips = 4.0
            profit_loss_pct = 1.2

        class EmptyOrder:
            pass

        assert comp_m.key(AltOrder()) == -75.0
        assert comp_pip.key(AltOrder()) == -8.0
        assert comp_pct.key(AltOrder()) == -2.5

        assert comp_m.key(AltProfitOrder()) == -35.0
        assert comp_pip.key(AltProfitOrder()) == -4.0
        assert comp_pct.key(AltProfitOrder()) == -1.2

        assert comp_m.key(EmptyOrder()) == -0.0


class TestDailyEquityComputer:
    """Test suite for DailyEquityComputer matching donor DailyEquityComputer.java."""

    def test_empty_orders(self) -> None:
        """Verify empty orders list returns empty equity."""
        assert DailyEquityComputer.compute_daily_equity([]) == []

    def test_unfilled_orders_only(self) -> None:
        """Verify list of only canceled/unfilled orders returns empty equity."""
        orders = [DummyOrder(ticket=1, is_canceled=True)]
        assert DailyEquityComputer.compute_daily_equity(orders) == []

    def test_daily_equity_same_day(self) -> None:
        """Verify accumulation of multiple trades on the same calendar day."""
        day_ms = 86_400_000
        base_time = 1_700_000_000_000 - (1_700_000_000_000 % day_ms)
        orders = [
            DummyOrder(ticket=1, pl=50.0, close_time_ms=base_time + 1000),
            DummyOrder(ticket=2, pl=30.0, close_time_ms=base_time + 5000),
        ]
        equity = DailyEquityComputer.compute_daily_equity(orders)
        assert len(equity) >= 3
        # First day has accumulated PL of 80.0
        assert equity[0] == 80.0
        # Subsequent forward-filled buffer days preserve 80.0
        assert equity[1] == 80.0
        assert equity[2] == 80.0

    def test_daily_equity_multi_day_with_gap(self) -> None:
        """Verify forward fill of equity across untraded days."""
        day_ms = 86_400_000
        base_time = 1_700_000_000_000 - (1_700_000_000_000 % day_ms)
        orders = [
            DummyOrder(ticket=1, pl=100.0, close_time_ms=base_time + 1000),
            # Gap of 2 days: Day 0 -> Day 2
            DummyOrder(ticket=2, pl=-20.0, close_time_ms=base_time + 2 * day_ms + 1000),
        ]
        equity = DailyEquityComputer.compute_daily_equity(orders)
        # Day 0: 100.0
        assert equity[0] == 100.0
        # Day 1 (gap): forward-filled 100.0
        assert equity[1] == 100.0
        # Day 2: 100.0 + (-20.0) = 80.0
        assert equity[2] == 80.0
        # Buffer days: forward-filled 80.0
        assert equity[3] == 80.0

    def test_daily_equity_out_of_order_returns_empty(self) -> None:
        """Verify out-of-order trade timestamps fail closed and return empty."""
        day_ms = 86_400_000
        base_time = 1_700_000_000_000 - (1_700_000_000_000 % day_ms)
        orders = [
            DummyOrder(ticket=1, pl=100.0, close_time_ms=base_time + day_ms),
            DummyOrder(ticket=2, pl=50.0, close_time_ms=base_time),  # past
        ]
        assert DailyEquityComputer.compute_daily_equity(orders) == []

    def test_daily_equity_with_get_pl_method(self) -> None:
        """Verify custom order with get_pl_by_type method."""

        class DynamicPlOrder:
            def __init__(self, close_time: int) -> None:
                self.close_time = close_time

            def is_filled_order(self) -> bool:
                return True

            def get_pl_by_type(self, pl_type: int) -> float:
                return 42.0

        orders = [DynamicPlOrder(100_000_000)]
        eq = DailyEquityComputer.compute_daily_equity(orders)
        assert len(eq) >= 3
        assert eq[0] == 42.0


class TestStatFunctions:
    """Test suite for StatFunctions matching donor StatFunctions.java."""

    def test_compute_average_default(self) -> None:
        """Verify mean average computation across complete sequence."""
        assert StatFunctions.compute_average([10.0, 20.0, 30.0]) == 20.0
        assert StatFunctions.compute_average([]) == 0.0

    def test_compute_average_with_range(self) -> None:
        """Verify mean average computation over index slice."""
        values = [10.0, 20.0, 30.0, 40.0]
        # Slice [1:3] -> [20.0, 30.0]
        assert StatFunctions.compute_average(values, from_idx=1, to_idx=3) == 25.0
        # Invalid slice -> 0.0
        assert StatFunctions.compute_average(values, from_idx=3, to_idx=2) == 0.0
        assert StatFunctions.compute_average(values, from_idx=-1, to_idx=2) == 0.0

    def test_compute_stdev_default(self) -> None:
        """Verify population standard deviation computation."""
        values = [10.0, 20.0, 30.0]
        mean = 20.0
        # ((10-20)^2 + (20-20)^2 + (30-20)^2) / 3 = 200 / 3 = 66.666...
        # sqrt(66.666...) ~ 8.1649658
        sd = StatFunctions.compute_stdev(mean, values)
        assert pytest.approx(sd, 0.0001) == 8.1649658
        assert StatFunctions.compute_stdev(0.0, []) == 0.0

    def test_compute_stdev_with_range(self) -> None:
        """Verify standard deviation computation over index slice."""
        values = [100.0, 10.0, 30.0, 500.0]
        # Slice [1:3] -> [10.0, 30.0], mean = 20.0
        sd = StatFunctions.compute_stdev(20.0, values, from_idx=1, to_idx=3)
        assert pytest.approx(sd, 0.0001) == 10.0
        # Invalid slice
        assert StatFunctions.compute_stdev(20.0, values, from_idx=3, to_idx=1) == 0.0
        assert StatFunctions.compute_stdev(20.0, values, from_idx=-1, to_idx=2) == 0.0


class TestOrderFunctions:
    """Test suite for OrderFunctions matching donor OrderFunctions.java."""

    def test_identify_strategy_and_symbol(self) -> None:
        """Verify strategy name and symbol criteria matching."""
        strat = DummyStrategy(name="Alpha", chart_symbol="EURUSD")
        order = DummyOrder(strategy_name="Alpha", symbol="EURUSD")

        # Matching strategy and Symbol "Any"
        assert OrderFunctions.identify(order, strat, "Any", 0, 0, "") is True
        # Symbol "Current" matches chart EURUSD
        assert OrderFunctions.identify(order, strat, "Current", 0, 0, "") is True
        # Exact symbol matches
        assert OrderFunctions.identify(order, strat, "EURUSD", 0, 0, "") is True
        # Different symbol fails
        assert OrderFunctions.identify(order, strat, "GBPUSD", 0, 0, "") is False

        # Strategy name mismatch fails
        diff_strat = DummyStrategy(name="Beta")
        assert OrderFunctions.identify(order, diff_strat, "Any", 0, 0, "") is False

    def test_identify_direction_magic_comment(self) -> None:
        """Verify direction, magic number, and comment substring matching."""
        strat = DummyStrategy(name="Alpha")
        order = DummyOrder(
            strategy_name="Alpha",
            direction=1,
            magic_number=12345,
            comment="Breakout long #1",
        )

        # Direction 1 matches; -1 fails
        assert OrderFunctions.identify(order, strat, "Any", 1, 0, "") is True
        assert OrderFunctions.identify(order, strat, "Any", -1, 0, "") is False

        # Magic number matches
        assert OrderFunctions.identify(order, strat, "Any", 0, 12345, "") is True
        assert OrderFunctions.identify(order, strat, "Any", 0, 99999, "") is False

        # Comment substring matches
        assert OrderFunctions.identify(order, strat, "Any", 0, 0, "Breakout") is True
        assert (
            OrderFunctions.identify(order, strat, "Any", 0, 0, "NonExistent") is False
        )

    def test_identify_callable_getters(self) -> None:
        """Verify getter methods for strategy name, symbol, direction, magic, comment."""

        class DynamicOrder:
            def get_strategy_name(self) -> str:
                return "DynStrat"

            def get_symbol(self) -> str:
                return "USDJPY"

            def get_direction(self) -> int:
                return -1

            def get_magic_number(self) -> int:
                return 777

            def get_comment(self) -> str:
                return "DynamicComment"

        class DynamicStrat:
            def get_strategy_name(self) -> str:
                return "DynStrat"

        d_order = DynamicOrder()
        d_strat = DynamicStrat()
        assert (
            OrderFunctions.identify(d_order, d_strat, "USDJPY", -1, 777, "Dynamic")
            is True
        )

    def test_find_live_and_history_orders(self) -> None:
        """Verify live order and history orders lookup in Strategy Trader."""
        o_live = DummyOrder(ticket=10, strategy_name="StratA", symbol="EURUSD")
        o_hist1 = DummyOrder(ticket=20, strategy_name="StratA", symbol="EURUSD")
        o_hist2 = DummyOrder(ticket=21, strategy_name="StratA", symbol="EURUSD")

        trader = DummyTrader(open_orders=[o_live], history_orders=[o_hist1, o_hist2])
        strat = DummyStrategy(name="StratA", trader=trader)

        # Find live order
        live_res = OrderFunctions.find_live_order(strat, "EURUSD", 0, 0, "")
        assert live_res is not None
        assert live_res.ticket == 10

        # Find first history order (oldest -> o_hist1)
        hist_first = OrderFunctions.find_history_order(strat, "EURUSD", 0, 0, "")
        assert hist_first is not None
        assert hist_first.ticket == 20

        # Find last history order (newest -> o_hist2)
        hist_last = OrderFunctions.find_last_history_order(strat, "EURUSD", 0, 0, "")
        assert hist_last is not None
        assert hist_last.ticket == 21

        # Non-matching criteria returns None
        assert OrderFunctions.find_live_order(strat, "GBPUSD", 0, 0, "") is None

        # None trader returns None
        empty_strat = DummyStrategy(name="NoTrader")
        empty_strat.trader = None  # type: ignore[assignment]
        assert OrderFunctions.find_live_order(empty_strat, "EURUSD", 0, 0, "") is None
        assert (
            OrderFunctions.find_history_order(empty_strat, "EURUSD", 0, 0, "") is None
        )
        assert (
            OrderFunctions.find_last_history_order(empty_strat, "EURUSD", 0, 0, "")
            is None
        )


class TestRetainedFunctionsUtilities:
    """Test suite for existing domain utilities in order_functions.py."""

    def test_trade_filter(self) -> None:
        """Verify TradeFilter matching logic and validation."""
        tf = TradeFilter(
            symbol="EURUSD", direction=1, magic=100, comment="Entry", ticket=1
        )
        pos = PositionInfo(
            ticket=1,
            symbol="EURUSD",
            position_type=0,  # Buy
            magic=100,
            comment="Entry trigger",
        )
        assert tf.matches(pos) is True

        # Mismatched ticket
        pos_wrong_ticket = PositionInfo(
            ticket=2,
            symbol="EURUSD",
            position_type=0,
            magic=100,
            comment="Entry trigger",
        )
        assert tf.matches(pos_wrong_ticket) is False

        # OrderInfo with sell direction
        order_sell = OrderInfo(
            ticket=5,
            symbol="EURUSD",
            order_type=1,  # Sell
            magic=100,
        )
        tf_sell = TradeFilter(symbol="EURUSD", direction=-1, magic=100)
        assert tf_sell.matches(order_sell) is True

        # Invalid direction raises ValueError
        with pytest.raises(ValueError, match="direction must be -1, 0, or 1"):
            TradeFilter(symbol="EURUSD", direction=5)

    def test_aware_timestamp_validation(self) -> None:
        """Verify aware_timestamp requires timezone information."""
        naive_dt = datetime.fromisoformat("2026-01-01T12:00:00")
        with pytest.raises(ValueError, match="must include a timezone"):
            aware_timestamp(naive_dt)

        aware_dt = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        assert aware_timestamp(aware_dt) > 0

    def test_bars_since_validations(self) -> None:
        """Verify bars_since ordering and boundary conditions."""
        t0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=15)
        t2 = t0 + timedelta(minutes=30)

        # Empty bar times
        with pytest.raises(ValueError, match="must be nonempty"):
            bars_since(t0.timestamp(), [], as_of=t2)

        # Non-ascending bar times
        with pytest.raises(ValueError, match="strictly oldest first"):
            bars_since(t0.timestamp(), [t1, t0], as_of=t2)

        # Bar times extending past as_of
        with pytest.raises(ValueError, match="must not extend past"):
            bars_since(t0.timestamp(), [t0, t1, t2], as_of=t1)

        # Trade timestamp before first bar
        with pytest.raises(ValueError, match="does not cover"):
            bars_since((t0 - timedelta(hours=1)).timestamp(), [t0, t1, t2], as_of=t2)

        # Event after as_of returns -1
        future_ts = (t2 + timedelta(hours=1)).timestamp()
        assert bars_since(future_ts, [t0, t1, t2], as_of=t2) == -1

        # Valid bars count
        assert bars_since(t0.timestamp(), [t0, t1, t2], as_of=t2) == 2

    def test_pricing_and_normalization(self) -> None:
        """Verify normalize_price and pip_size validations."""
        spec = SymbolInfo(
            name="EURUSD",
            price=SymbolPrice(tick_step=0.00001),
        )
        normalized = normalize_price(1.085523, spec)
        assert normalized == 1.08552

        # Invalid price (< 0 or nan)
        with pytest.raises(ValueError, match="finite and nonnegative"):
            normalize_price(-1.0, spec)

        # Invalid tick_step (<= 0)
        invalid_spec = SymbolInfo(
            name="EURUSD",
            price=SymbolPrice(tick_step=0.0),
        )
        with pytest.raises(ValueError, match="symbol tick step must be positive"):
            normalize_price(1.0, invalid_spec)

        # Price smaller than tick step
        tiny_step_spec = SymbolInfo(
            name="EURUSD",
            price=SymbolPrice(tick_step=10.0),
        )
        with pytest.raises(ValueError, match="smaller than the symbol tick step"):
            normalize_price(0.001, tiny_step_spec)

        # Pip size
        assert pip_size(None, 0.0001) == 0.0001
        assert pip_size(0.0005, 0.0001) == 0.0005
        with pytest.raises(ValueError, match="must be finite and positive"):
            pip_size(-0.0001, 0.0001)
