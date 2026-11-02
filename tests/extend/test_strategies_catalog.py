"""Comprehensive test suite for StrategyQuant SQ.Strategies snippet catalog.

Description:
    Validates the base execution framework, multi-chart market data, simulated
    order routing, indicator adapters, and all 13 StrategyQuant concrete strategy
    classes. Enforces branch coverage and strict contract fidelity.

Purpose:
    FEAT-STRATEGIES: Test suite for StrategyQuant strategy snippets.

Key Capabilities:
    - FR-STRAT-TESTS: Exhaustive unit tests across all 13 strategy classes and base framework.

Python API Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --cov=app.extend.strategies
"""

from __future__ import annotations

from typing import override

import pytest
from app.extend.strategies import (
    CCIReverse,
    ChartData,
    CompleteStrategySample,
    DataSeries,
    FullData,
    IndicatorResult,
    Indicators,
    ITradingEvent,
    ITradingEventListener,
    LiveTestStrategy1,
    Log,
    MarketDataChartData1TestStrategy1,
    MarketDataManager,
    MarketDataTestStrategy,
    OrderCloseTypes,
    OrderTypes,
    Parameter,
    RobustnessTestStrategy,
    Strategy,
    TestIndyStrategy,
    TestOHLCDailyStrategy,
    TestSpecialStrategy,
    TestStrategy,
    TestStrategy1,
    TestStrategyAskBid,
    Trader,
    UpdateEventTypes,
    VariablesStrategyTest,
)


def test_base_contracts_and_enums() -> None:
    """Verify enumerations, DataSeries methods, and ChartData accessors."""
    assert UpdateEventTypes.BarTick.value == 0
    assert UpdateEventTypes.BarOpen.value == 1
    assert UpdateEventTypes.BarClose.value == 2

    assert OrderTypes.Buy.value == 1
    assert OrderTypes.Sell.value == 2
    assert OrderTypes.BuyLimit.value == 3
    assert OrderTypes.SellLimit.value == 4
    assert OrderTypes.BuyStop.value == 5
    assert OrderTypes.SellStop.value == 6

    assert OrderCloseTypes.Normal.value == 0
    assert OrderCloseTypes.Reversed.value == 1
    assert OrderCloseTypes.Deleted.value == 2
    assert OrderCloseTypes.Manual.value == 3
    assert OrderCloseTypes.SL.value == 4
    assert OrderCloseTypes.PT.value == 5
    assert OrderCloseTypes.EndOfDay.value == 6

    ds = DataSeries([10.0, 20.0, 30.0])
    assert len(ds) == 3
    assert ds.get(0) == 30.0
    assert ds.get(1) == 20.0
    assert ds.get(2) == 10.0
    assert ds.get(3, default=-1.0) == -1.0
    assert ds[0] == 30.0
    ds.append(40.0)
    assert len(ds) == 4
    assert ds.to_list() == [10.0, 20.0, 30.0, 40.0]

    empty_ds = DataSeries()
    assert len(empty_ds) == 0
    assert empty_ds.get(0, -99.0) == -99.0

    ir = IndicatorResult([1.0, 2.0])
    assert ir.Value.get(0) == 2.0

    chart = ChartData(
        symbol="GBPUSD",
        timeframe="M15",
        connection="LiveConn",
        opens=[1.2, 1.25],
        highs=[1.22, 1.27],
        lows=[1.19, 1.24],
        closes=[1.21, 1.26],
        volumes=[50.0, 60.0],
        times=[1000.0, 2000.0],
    )
    assert chart.Symbol == "GBPUSD"
    assert chart.Timeframe == "M15"
    assert chart.Connection == "LiveConn"
    assert chart.Open_val(0) == 1.25
    assert chart.High_val(0) == 1.27
    assert chart.Low_val(0) == 1.24
    assert chart.Close_val(0) == 1.26
    assert chart.Volume_val(0) == 60.0
    assert chart.Time(0) == 2000
    assert chart.Ask() == 1.26 + 0.0001
    assert chart.Bid() == 1.26
    assert not chart.isUpdated()
    chart.set_updated(True)
    assert chart.isUpdated()


def test_market_data_manager() -> None:
    """Verify MarketDataManager chart indexing and dynamic chart additions."""
    md = MarketDataManager()
    assert md.get_charts_count() == 1
    c0 = md.Chart(0)
    assert c0.Symbol == "EURUSD"

    c1 = md.Chart(2)
    assert md.get_charts_count() == 3
    assert c1.Symbol == "XSymbol_0_2"

    c_tf = md.addChart("M30")
    assert c_tf.Timeframe == "M30"

    c_sym_tf = md.addChart("USDJPY", "H4")
    assert c_sym_tf.Symbol == "USDJPY"
    assert c_sym_tf.Timeframe == "H4"

    c_full = md.addChart("ConnX", "AUDUSD", "D1")
    assert c_full.Connection == "ConnX"
    assert c_full.Symbol == "AUDUSD"
    assert c_full.Timeframe == "D1"


def test_orders_and_trader_flow() -> None:
    """Verify ILiveOrder, OrderBuilder, and Trader state mutations."""
    trader = Trader(balance=25000.0, equity=24500.0)
    assert trader.getAccountBalance() == 25000.0
    assert trader.getAccountEquity() == 24500.0
    trader.setAccountBalance(26000.0)
    trader.setAccountEquity(25500.0)
    assert trader.getAccountBalance() == 26000.0
    assert trader.getAccountEquity() == 25500.0

    class MockListener(ITradingEventListener):
        def __init__(self) -> None:
            self.events: list[ITradingEvent] = []

        @override
        def OnEvent(self, event: ITradingEvent) -> None:
            self.events.append(event)

        @override
        def OnTradingEvent(self, event: ITradingEvent) -> None:
            self.events.append(event)

    listener = MockListener()

    b_order = (
        trader.Buy("EURUSD")
        .setSize(2.5)
        .setMagicNumber(999)
        .setComment("TestBuy")
        .setSL(1.08)
        .setPT(1.12)
        .setExpiration(123456.0)
        .setMaxSlippage(0.5)
        .Send()
    )
    assert b_order.getMagicNumber() == 999
    assert b_order.getOrderType() == OrderTypes.Buy
    assert b_order.getOpenPrice() == 1.1000
    assert b_order.getClosePrice() == 0.0
    assert b_order.getBarsInTrade() == 0
    b_order.increment_bars()
    assert b_order.getBarsInTrade() == 1
    assert b_order.isSuccessful()
    assert not b_order.isPendingOrder()
    assert b_order.is_active()

    b_order.setSL(1.085).setPT(1.125).Send()

    assert trader.getOpenOrdersCount(True) == 1
    assert trader.getOpenOrder(0, True) is b_order

    async_order = trader.Sell("EURUSD").setMagicNumber(888).SendAsync(listener)
    assert len(listener.events) == 1
    assert listener.events[0].order is async_order
    assert trader.getOpenOrdersCount(True) == 2

    # Limit and stop orders
    limit_buy = trader.BuyLimit("EURUSD", 1.05).Send()
    assert limit_buy.isPendingOrder()
    limit_sell = trader.SellLimit("EURUSD", 1.15).Send()
    assert limit_sell.isPendingOrder()
    stop_buy = trader.BuyStop("EURUSD", 1.12).Send()
    assert stop_buy.isPendingOrder()
    stop_sell = trader.SellStop("EURUSD", 1.04).Send()
    assert stop_sell.isPendingOrder()

    generic_order = trader.Open(OrderTypes.Buy, "USDJPY", size=1.5).Send()
    assert generic_order.getOrderType() == OrderTypes.Buy

    # Close operations
    b_order.Close(OrderCloseTypes.Manual)
    assert not b_order.is_active()

    async_order.CloseAsync(listener)
    assert not async_order.is_active()
    assert len(listener.events) == 2

    assert trader.GetHistoryTrades() == []


def test_indicators_calculations() -> None:
    """Verify CCI and ATR mathematical correctness and edge cases."""
    ind = Indicators()
    ind.destroy()
    assert ind.getIndicatorsCache() == {}

    # CCI with short series
    res_short = ind.CCI([1.0, 2.0], period=20)
    assert res_short.Value.get(0) == 0.0

    # CCI with constant series (mean deviation = 0)
    res_const = ind.CCI([10.0] * 25, period=20)
    assert res_const.Value.get(0) == 0.0

    # CCI normal calculation
    prices = [10.0 + (i % 5) for i in range(30)]
    res_normal = ind.CCI(prices, period=14)
    assert len(res_normal.Value) == 30
    assert isinstance(res_normal.Value.get(0), float)

    # ATR edge cases and calculation
    empty_chart = ChartData(opens=[], highs=[], lows=[], closes=[])
    res_atr_empty = ind.ATR(empty_chart, period=14)
    assert res_atr_empty.Value.get(0) == 0.0

    chart = ChartData(
        highs=[10.0, 12.0, 11.0, 13.0, 15.0],
        lows=[9.0, 10.0, 9.5, 11.5, 13.0],
        closes=[9.5, 11.0, 10.5, 12.5, 14.0],
    )
    res_atr = ind.ATR(chart, period=3)
    assert len(res_atr.Value) == 5
    assert res_atr.Value.get(0) > 0.0


def test_strategy_base_shortcuts_and_parameter() -> None:
    """Verify Strategy base shortcuts, price querying, and Parameter descriptor."""

    class DummyStrategy(Strategy):
        val: Parameter[int] = Parameter(42)

        @override
        def Initialize(self) -> None:
            pass

        @override
        def OnBarUpdate(self) -> None:
            pass

    strat = DummyStrategy()
    assert strat.val == 42
    strat.val = 100
    assert strat.val == 100

    assert isinstance(DummyStrategy.val, Parameter)

    assert strat.getEventType() == UpdateEventTypes.BarOpen
    strat.setUpdateEventType(UpdateEventTypes.BarTick)
    assert strat.getEventType() == UpdateEventTypes.BarTick

    assert not strat.is_stopped()
    strat.StopStrategy()
    assert strat.is_stopped()

    assert strat.Bars() >= 3
    assert strat.TimeCurrent() > 0
    assert strat.Ask() > strat.Bid()

    # Price queries
    assert strat.Open_price(0) == strat.Open.get(0)
    assert strat.Open_price(0, 0) == strat.Open.get(0)
    assert strat.High_price(0) == strat.High.get(0)
    assert strat.High_price(0, 0) == strat.High.get(0)
    assert strat.Low_price(0) == strat.Low.get(0)
    assert strat.Low_price(0, 0) == strat.Low.get(0)
    assert strat.Close_price(0) == strat.Close.get(0)
    assert strat.Close_price(0, 0) == strat.Close.get(0)
    assert strat.Volume_val(0) == strat.Volume.get(0)
    assert strat.Volume_val(0, 0) == strat.Volume.get(0)

    c0 = strat.MarketData.Chart(0)
    atr = strat.getATRValue(c0, 2, 0)
    assert isinstance(atr, float)

    strat.Deinitialize()

    Log.debug("test debug")
    Log.info("test info")
    Log.warn("test warn")
    Log.error("test error")


def test_cci_reverse_strategy() -> None:
    """Verify CCIReverse buy/sell reversal and order closing."""
    strat = CCIReverse()
    strat.Initialize()

    # Non-BarOpen early return
    strat.setUpdateEventType(UpdateEventTypes.BarTick)
    strat.OnBarUpdate()
    assert strat.Trader.getOpenOrdersCount(True) == 0

    # BarOpen with positive CCI
    strat.setUpdateEventType(UpdateEventTypes.BarOpen)
    # Simulate rising prices so CCI > 0
    strat.Open = DataSeries([1.0, 1.01, 1.02, 1.03, 1.05, 1.10] * 5)
    strat.OnBarUpdate()
    assert strat.Trader.getOpenOrdersCount(True) == 1
    assert strat.Trader.getOpenOrder(0, True).getOrderType() == OrderTypes.Buy

    # Simulate falling prices so CCI < 0
    strat.Open = DataSeries([1.10, 1.08, 1.06, 1.04, 1.02, 0.95] * 5)
    strat.OnBarUpdate()
    # Old buy closed (reversed), new sell opened
    assert strat.Trader.getOpenOrdersCount(True) == 1
    assert strat.Trader.getOpenOrder(0, True).getOrderType() == OrderTypes.Sell


def test_complete_strategy_sample_strategy() -> None:
    """Verify CompleteStrategySample multi-chart checks and discrepancy assertions."""
    strat = CompleteStrategySample()
    strat.Initialize()
    assert strat.getEventType() == UpdateEventTypes.BarOpen

    # Normal execution across charts
    strat.OnBarUpdate()

    # Discrepancy test 1
    strat.Open = DataSeries([999.0])
    with pytest.raises(ValueError, match="Values from Open"):
        strat.OnBarUpdate()


def test_live_test_strategy_1() -> None:
    """Verify LiveTestStrategy1 timed entries at minute 0 and 30, and 4-bar exit."""
    strat = LiveTestStrategy1()
    strat.Initialize()

    # Hour 00:00:00 UTC (timestamp 1514764800000 -> 2018-01-01 00:00:00)
    strat.MarketData.Chart(0).Time_series = DataSeries([1514764800000.0])
    strat.OnBarUpdate()
    order1 = strat.order
    assert order1 is not None
    assert order1.getOrderType() == OrderTypes.Buy

    # Advance bars in trade to 4 and set time to minute 15
    for _ in range(4):
        order1.increment_bars()

    # Minute 15 (neither 0 nor 30), so closing order won't trigger re-entry
    strat.MarketData.Chart(0).Time_series = DataSeries([1514764800000.0 + 900000.0])
    strat.OnBarUpdate()
    # Order should be closed after 4 bars
    assert strat.order is None

    # Test sell on half hour with a fresh instance
    strat_sell = LiveTestStrategy1()
    strat_sell.Initialize()
    strat_sell.MarketData.Chart(0).Time_series = DataSeries([1514766600000.0])
    strat_sell.OnBarUpdate()
    order2 = strat_sell.order
    assert order2 is not None
    assert order2.getOrderType() == OrderTypes.Sell


def test_market_data_chart_data_1_test_strategy_1() -> None:
    """Verify MarketDataChartData1TestStrategy1 tick processing and chart metadata checks."""
    strat = MarketDataChartData1TestStrategy1()
    strat.Initialize()

    # Run 24 ticks through OnBarUpdate
    for _ in range(24):
        strat.OnBarUpdate()

    assert strat.is_stopped()
    assert len(strat.data) >= 5
    assert isinstance(strat.data[0], FullData)

    # Trigger metadata error branches
    strat.MarketData.Chart(0).Connection = "WrongConn"
    with pytest.raises(ValueError, match="Error 1"):
        strat._verify_chart_metadata()

    strat.MarketData.Chart(0).Connection = "XTestConn1"
    strat.MarketData.Chart(0).Symbol = "WrongSym"
    with pytest.raises(ValueError, match="Error 2"):
        strat._verify_chart_metadata()


def test_market_data_test_strategy() -> None:
    """Verify MarketDataTestStrategy chart initialization and price evaluation."""
    strat = MarketDataTestStrategy()
    strat.Initialize()
    strat.OnBarUpdate()
    assert strat.MarketData.get_charts_count() >= 4


def test_robustness_test_strategy() -> None:
    """Verify RobustnessTestStrategy alternating directions, SL/PT update, and bar exits."""
    strat = RobustnessTestStrategy()
    strat.Initialize()

    # First bar opens Sell order (toggles from initial Buy)
    strat.OnBarUpdate()
    order1 = strat._order
    assert order1 is not None
    assert order1.getOrderType() == OrderTypes.Sell

    # Second bar modifies SL/PT
    strat.OnBarUpdate()
    assert order1._sl == 1.234
    assert order1._pt == 1.234

    # Advance beyond 5 bars
    for _ in range(6):
        order1.increment_bars()

    # Next bar closes old order and opens Buy
    strat.OnBarUpdate()
    order2 = strat._order
    assert order2 is not None
    assert order2.getOrderType() == OrderTypes.Buy

    # Verify event callbacks
    ev = ITradingEvent(event_type="Custom")
    strat.OnEvent(ev)
    strat.OnTradingEvent(ev)
    assert len(strat.events_received) >= 2


def test_test_indy_strategy() -> None:
    """Verify TestIndyStrategy CSV record writing and subclass indicator overrides."""

    class CustomIndyStrategy(TestIndyStrategy):
        @override
        def getIndyValue(self) -> float:
            return 123.45

    strat = CustomIndyStrategy(event_type=UpdateEventTypes.BarOpen, data_index=0)
    strat.setLogName("custom_log")
    strat.Initialize()
    strat.OnBarUpdate()
    strat.Deinitialize()

    records = strat.get_records()
    assert len(records) == 1
    assert "123.45" in records[0]


def test_test_ohlc_daily_strategy() -> None:
    """Verify TestOHLCDailyStrategy daily shift logging and timestamp thresholding."""
    strat = TestOHLCDailyStrategy(start_time=1000)
    strat.Initialize()

    # Time before start_time
    strat.Time = DataSeries([500.0])
    strat.OnBarUpdate()
    assert len(strat.get_records()) == 0

    # Time after start_time
    strat.Time = DataSeries([2000.0])
    strat.OnBarUpdate()
    strat.Deinitialize()

    records = strat.get_records()
    assert len(records) == 1
    assert ";" in records[0]


def test_test_special_strategy() -> None:
    """Verify TestSpecialStrategy benchmark validation and discrepancy detection."""
    # Base timestamp 1514764800000 (2018-01-01 00:00:00 UTC)
    ref_map = {
        1514764800000: [
            "2018-01-01",
            "00:00",
            "0",  # closedF = True (matches initial self._closed = True)
            "1.1000",
            "1.1001",
            "1.0999",
            "10000.0",
            "10000.0",
        ]
    }
    strat = TestSpecialStrategy(ref_map)
    strat.Initialize()

    strat.MarketData.Chart(0).Time_series = DataSeries(
        [1514764800000.0, 1514764800000.0]
    )

    # Non-BarOpen returns early
    strat.setUpdateEventType(UpdateEventTypes.BarTick)
    strat.OnBarUpdate()

    # Normal BarOpen execution
    strat.setUpdateEventType(UpdateEventTypes.BarOpen)
    strat.OnBarUpdate()

    # Test error branches
    bad_map = {1514764800000: ["", "", "1", "1.1", "1.1", "1.1", "99999.0", "10000.0"]}
    strat.set_reference_map(bad_map)
    with pytest.raises(ValueError, match="Incorrect account balance"):
        strat.OnBarUpdate()

    bad_map_equity = {
        1514764800000: ["", "", "1", "1.1", "1.1", "1.1", "10000.0", "99999.0"]
    }
    strat.set_reference_map(bad_map_equity)
    with pytest.raises(ValueError, match="Incorrect account equity"):
        strat.OnBarUpdate()

    bad_map_closed = {
        1514764800000: ["", "", "1", "1.1", "1.1", "1.1", "10000.0", "10000.0"]
    }
    strat.set_reference_map(bad_map_closed)
    with pytest.raises(ValueError, match="Incorrect open type"):
        strat.OnBarUpdate()

    missing_map = {999999999: [""]}
    strat.set_reference_map(missing_map)
    with pytest.raises(ValueError, match="Missing data"):
        strat.OnBarUpdate()


def test_test_strategy() -> None:
    """Verify TestStrategy multi-chart checks and multiple-chart update assertion."""
    strat = TestStrategy()
    strat.Initialize()
    strat.OnBarUpdate()

    strat.MultipleChartsUpdated = True
    with pytest.raises(ValueError, match="MultipleChartsUpdated"):
        strat.OnBarUpdate()


def test_test_strategy_1() -> None:
    """Verify TestStrategy1 async execution and alternating Buy/Sell transitions."""
    strat = TestStrategy1()
    strat.Initialize()
    strat.OnBarUpdate()
    order1 = strat._order
    assert order1 is not None
    assert order1.getOrderType() == OrderTypes.Sell

    # Advance bars
    for _ in range(6):
        order1.increment_bars()

    strat.OnBarUpdate()
    order2 = strat._order
    assert order2 is not None
    assert order2.getOrderType() == OrderTypes.Buy


def test_test_strategy_ask_bid() -> None:
    """Verify TestStrategyAskBid quote capture and deinitialization."""
    strat = TestStrategyAskBid()
    strat.Initialize()
    strat.OnBarUpdate()
    strat.Deinitialize()

    records = strat.get_records()
    assert len(records) == 1
    assert ";" in records[0]


def test_variables_strategy_test() -> None:
    """Verify VariablesStrategyTest parameter bindings and CCI period dynamic sizing."""
    strat = VariablesStrategyTest(
        int_var_1=14,
        int_var_2=28,
        double_var_1=22.22,
        bool_var_1=False,
        string_var_1="custom",
    )
    assert strat.IntVar1 == 14
    assert strat.IntVar2 == 28
    assert strat.DoubleVar1 == 22.22
    assert not strat.BoolVar1
    assert strat.StringVar1 == "custom"

    strat.Initialize()

    # Non-BarOpen returns early
    strat.setUpdateEventType(UpdateEventTypes.BarTick)
    strat.OnBarUpdate()
    assert strat.Trader.getOpenOrdersCount(False) == 0

    # BarOpen with rising prices
    strat.setUpdateEventType(UpdateEventTypes.BarOpen)
    strat.Open = DataSeries([1.0, 1.02, 1.04, 1.06, 1.08, 1.15] * 5)
    strat.OnBarUpdate()
    assert strat.Trader.getOpenOrdersCount(False) == 1
    assert strat.Trader.getOpenOrder(0, False).getOrderType() == OrderTypes.Buy

    # BarOpen with falling prices
    strat.Open = DataSeries([1.15, 1.10, 1.05, 1.00, 0.95, 0.90] * 5)
    strat.OnBarUpdate()
    # Old buy closed (deleted), new sell opened
    assert strat.Trader.getOpenOrdersCount(False) == 1
    assert strat.Trader.getOpenOrder(0, False).getOrderType() == OrderTypes.Sell
