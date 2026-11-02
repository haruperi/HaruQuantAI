"""Unit tests for CustomAnalysis extension cohort matching donor snippets.

Description:
    Tests CustomAnalysisMethod contracts, ResultsGroup, OrdersList, CustomAnalysisOrder,
    donor snippets CorrelationFilter and OutlierTrade, alongside legacy analyzers.
"""

from __future__ import annotations

from app.extend.custom_analysis import (
    TYPE_BOTH,
    TYPE_FILTER_STRATEGY,
    TYPE_PROCESS_DATABANK,
    CorrelationFilter,
    CorrelationFilterAnalyzer,
    CustomAnalysisMethod,
    CustomAnalysisOrder,
    OrdersList,
    OutlierTrade,
    OutlierTradeAnalyzer,
    ResultsGroup,
    TradeRecord,
)


class TestCustomAnalysisBase:
    """Test suite for CustomAnalysis base abstractions."""

    def test_custom_analysis_order_properties_and_clone(self) -> None:
        """Verify order attributes, aliases, and cloning."""
        order = CustomAnalysisOrder(
            ticket=42,
            pl=125.5,
            is_balance=False,
            open_time_ms=1000,
            close_time_ms=2000,
            result_key="Main",
            direction=1,
            sample_type="InSample",
        )
        assert order.ticket == 42
        assert order.pl == 125.5
        assert not order.is_balance_order()

        clone = order.clone()
        assert clone.ticket == order.ticket
        assert clone.pl == order.pl

        bal_order = CustomAnalysisOrder(ticket=43, is_balance=True)
        assert bal_order.is_balance_order()

    def test_orders_list_manipulation_and_filtering(self) -> None:
        """Verify orders collection indexing, len, cloning, and sample filtering."""
        o1 = CustomAnalysisOrder(ticket=1, pl=10.0, sample_type="InSample")
        o2 = CustomAnalysisOrder(ticket=2, pl=-5.0, sample_type="OutOfSample")
        o3 = CustomAnalysisOrder(
            ticket=3, pl=20.0, result_key="Sub", sample_type="InSample"
        )
        o4 = CustomAnalysisOrder(
            ticket=4, pl=15.0, direction=-1, sample_type="InSample"
        )

        olist = OrdersList([o1, o2, o3])
        assert olist.size() == 3
        assert len(olist) == 3
        assert olist.get(0).ticket == 1
        assert olist[1].ticket == 2

        olist.add(o4)
        assert olist.size() == 4
        assert list(iter(olist)) == [o1, o2, o3, o4]

        # Filter by sample type
        in_sample = olist.filter_with_clone(
            result_key="", direction=0, sample_type="InSample"
        )
        assert in_sample.size() == 3

        # Filter by result_key
        sub_only = olist.filter_with_clone(
            result_key="Sub", direction=0, sample_type="All"
        )
        assert sub_only.size() == 1
        assert sub_only.get(0).ticket == 3

        # Filter by direction
        short_only = olist.filter_with_clone(
            result_key="", direction=-1, sample_type="All"
        )
        assert short_only.size() == 1
        assert short_only.get(0).ticket == 4

        # Deep copy
        cloned_list = olist.clone()
        assert cloned_list.size() == 4

    def test_results_group_container(self) -> None:
        """Verify ResultsGroup container properties, fitness, and cloning."""
        orders = [CustomAnalysisOrder(ticket=1, pl=50.0)]
        rg = ResultsGroup(
            name="StratA",
            fitness=1.85,
            orders=orders,
            main_result_key="Main",
            main_result_data={"NetProfit": 50.0},
        )
        assert rg.name == "StratA"
        assert rg.get_name() == "StratA"
        assert rg.fitness == 1.85
        assert rg.get_fitness() == 1.85
        assert rg.get_main_result_key() == "Main"
        assert rg.main_result() == {"NetProfit": 50.0}
        assert rg.orders().size() == 1

        rg.set_fitness(2.5)
        assert rg.get_fitness() == 2.5

        # From OrdersList
        rg2 = ResultsGroup(name="StratB", orders=OrdersList(orders))
        assert rg2.orders().size() == 1

        # Default empty orders
        rg_empty = ResultsGroup(name="StratC")
        assert rg_empty.orders().size() == 0

        # Clone
        cloned_rg = rg.clone()
        assert cloned_rg.get_name() == "StratA"
        assert cloned_rg.get_fitness() == 2.5
        assert cloned_rg.main_result() == {"NetProfit": 50.0}

    def test_custom_analysis_method_base_defaults(self) -> None:
        """Verify default methods and properties on CustomAnalysisMethod."""

        class ConcreteMethod(CustomAnalysisMethod):
            pass

        method = ConcreteMethod("TestSnippet", TYPE_BOTH)
        assert method.get_name() == "TestSnippet"
        assert method.get_type() == TYPE_BOTH

        method.set_input_args("arg1, arg2")
        assert method.get_input_args() == "arg1, arg2"

        method.set_project_log("Log msg")
        assert method.get_project_log() == "Log msg"

        dummy_rg = ResultsGroup(name="S1")
        assert method.filter_strategy("P", "T", "D", dummy_rg) is True
        assert method.process_databank("P", "T", "D", [dummy_rg]) == [dummy_rg]


class TestCorrelationFilterSnippet:
    """Test suite for CorrelationFilter snippet matching donor CorrelationFilter.java."""

    def test_filter_strategy_always_true(self) -> None:
        """Verify single-strategy filter returns True."""
        cf = CorrelationFilter()
        assert cf.get_type() == TYPE_PROCESS_DATABANK
        rg = ResultsGroup(name="Strat1")
        assert cf.filter_strategy("Proj", "Task", "Databank", rg) is True

    def test_process_databank_empty(self) -> None:
        """Verify empty databank handling."""
        cf = CorrelationFilter()
        assert cf.process_databank("Proj", "Task", "Databank", []) == []

    def test_process_databank_correlation_pruning(self) -> None:
        """Verify databank strategies are ordered by fitness and correlated ones pruned."""
        cf = CorrelationFilter()
        cf.set_input_args("0.5")

        day_ms = 86_400_000
        # Strategy 1 (highest fitness): profits [10, 20, 30] across 3 days
        s1_orders = [
            CustomAnalysisOrder(ticket=1, pl=10.0, close_time_ms=1 * day_ms),
            CustomAnalysisOrder(ticket=2, pl=20.0, close_time_ms=2 * day_ms),
            CustomAnalysisOrder(ticket=3, pl=30.0, close_time_ms=3 * day_ms),
        ]
        # Strategy 2 (medium fitness, highly correlated with S1): profits [12, 19, 31]
        s2_orders = [
            CustomAnalysisOrder(ticket=1, pl=12.0, close_time_ms=1 * day_ms),
            CustomAnalysisOrder(ticket=2, pl=19.0, close_time_ms=2 * day_ms),
            CustomAnalysisOrder(ticket=3, pl=31.0, close_time_ms=3 * day_ms),
        ]
        # Strategy 3 (lowest fitness, uncorrelated / negatively correlated): profits [30, 20, 10]
        s3_orders = [
            CustomAnalysisOrder(ticket=1, pl=30.0, close_time_ms=1 * day_ms),
            CustomAnalysisOrder(ticket=2, pl=20.0, close_time_ms=2 * day_ms),
            CustomAnalysisOrder(ticket=3, pl=10.0, close_time_ms=3 * day_ms),
        ]

        rg1 = ResultsGroup("S1", fitness=10.0, orders=s1_orders)
        rg2 = ResultsGroup("S2", fitness=5.0, orders=s2_orders)
        rg3 = ResultsGroup("S3", fitness=1.0, orders=s3_orders)

        # Databank passed in random order
        databank = [rg2, rg3, rg1]

        pruned = cf.process_databank("Proj", "Task", "Results", databank)

        # S1 retained (fitness 10.0). S2 correlated with S1 (corr > 0.5) -> removed.
        # S3 uncorrelated with S1 -> retained.
        names = [rg.get_name() for rg in pruned]
        assert names == ["S1", "S3"]

    def test_correlation_fallback_open_time_and_empty_correlation(self) -> None:
        """Verify correlation records calculation with default zero timestamps."""
        cf = CorrelationFilter()
        rg_a = ResultsGroup(
            "A",
            fitness=5.0,
            orders=[
                CustomAnalysisOrder(ticket=1, pl=10.0, is_balance=True),
                CustomAnalysisOrder(ticket=2, pl=20.0, open_time_ms=0, close_time_ms=0),
            ],
        )
        rg_b = ResultsGroup(
            "B",
            fitness=2.0,
            orders=[
                CustomAnalysisOrder(ticket=1, pl=5.0, open_time_ms=0, close_time_ms=0),
            ],
        )
        p1, p2 = cf.precompute_periods_ap(rg_a, rg_b)
        assert len(p1) > 0
        assert len(p2) > 0

        # One empty orders strategy
        rg_empty = ResultsGroup("Empty", orders=[])
        corr = cf.compute_strategy_correlation(rg_a, rg_empty)
        assert corr == 0.0


class TestOutlierTradeSnippet:
    """Test suite for OutlierTrade snippet matching donor OutlierTrade.java."""

    def test_outlier_trade_empty_orders(self) -> None:
        """Verify empty orders strategy is rejected."""
        ot = OutlierTrade()
        assert ot.get_type() == TYPE_FILTER_STRATEGY
        ot.set_input_args("1.1, 0")
        rg = ResultsGroup("EmptyStrat", orders=[])
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is False

    def test_outlier_trade_malformed_input_args(self) -> None:
        """Verify malformed inputArgs fails closed and returns False."""
        ot = OutlierTrade()
        rg = ResultsGroup("S", orders=[CustomAnalysisOrder(ticket=1, pl=10.0)])

        ot.set_input_args("")
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is False

        ot.set_input_args("not_a_number, 0")
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is False

    def test_outlier_trade_count_le_2_passes(self) -> None:
        """Verify strategies with 2 or fewer valid trades pass."""
        ot = OutlierTrade()
        ot.set_input_args("1.1, 0")

        # 2 trades with huge first PL: count is 2, so count > 2 check doesn't trigger
        orders = [
            CustomAnalysisOrder(ticket=1, pl=1000.0),
            CustomAnalysisOrder(ticket=2, pl=10.0),
            CustomAnalysisOrder(ticket=3, pl=5000.0, is_balance=True),  # skipped
        ]
        rg = ResultsGroup("StratSmall", orders=orders)
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is True

    def test_outlier_trade_option_0_without_filtering_same_pl(self) -> None:
        """Verify option 0 tracks duplicate PLs in top 3."""
        ot = OutlierTrade()
        # Option 0: duplicates are allowed in top 3
        ot.set_input_args("1.1, 0")

        # PLs: 100, 50, 50, 10.
        # first=100, second=50, third=50.
        # threshold = 1.1 * (50 + 50) = 110.
        # first (100) < threshold (110) -> Passes (returns True).
        orders_pass = [
            CustomAnalysisOrder(ticket=1, pl=100.0),
            CustomAnalysisOrder(ticket=2, pl=50.0),
            CustomAnalysisOrder(ticket=3, pl=50.0),
            CustomAnalysisOrder(ticket=4, pl=10.0),
        ]
        rg_pass = ResultsGroup("Pass0", orders=orders_pass)
        assert ot.filter_strategy("Proj", "Task", "Results", rg_pass) is True

        # Now test where first PL is outlier:
        # PLs: 200, 50, 50, 10.
        # first=200, second=50, third=50.
        # threshold = 1.1 * 100 = 110.
        # 200 > 110 -> Rejects (returns False).
        orders_fail = [
            CustomAnalysisOrder(ticket=1, pl=200.0),
            CustomAnalysisOrder(ticket=2, pl=50.0),
            CustomAnalysisOrder(ticket=3, pl=50.0),
            CustomAnalysisOrder(ticket=4, pl=10.0),
        ]
        rg_fail = ResultsGroup("Fail0", orders=orders_fail)
        assert ot.filter_strategy("Proj", "Task", "Results", rg_fail) is False

    def test_outlier_trade_option_1_with_filtering_same_pl(self) -> None:
        """Verify option 1 enforces strictly distinct top 3 PL values."""
        ot = OutlierTrade()
        # Option 1: duplicates are filtered out from top 3
        ot.set_input_args("1.1, 1")

        # PLs: 100, 50, 50, 10.
        # In option 1:
        # first = 100
        # second = 50
        # next 50 is ignored because pl == secondPL
        # third = 10 (since 10 != first and 10 != second)
        # sum of second + third = 50 + 10 = 60.
        # threshold = 1.1 * 60 = 66.
        # first (100) > 66 -> Rejects (returns False)!
        orders = [
            CustomAnalysisOrder(ticket=1, pl=100.0),
            CustomAnalysisOrder(ticket=2, pl=50.0),
            CustomAnalysisOrder(ticket=3, pl=50.0),
            CustomAnalysisOrder(ticket=4, pl=10.0),
        ]
        rg = ResultsGroup("TestOption1", orders=orders)
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is False

        # When second + third is large enough:
        # PLs: 100, 70, 70, 70, 40, 5. (Duplicate 70 tests short-circuit branch)
        # first=100, second=70, third=40. Sum=110. Threshold=1.1*110=121.
        # 100 < 121 -> Passes (returns True).
        orders_pass = [
            CustomAnalysisOrder(ticket=1, pl=100.0),
            CustomAnalysisOrder(ticket=2, pl=70.0),
            CustomAnalysisOrder(ticket=3, pl=70.0),
            CustomAnalysisOrder(ticket=4, pl=70.0),
            CustomAnalysisOrder(ticket=5, pl=40.0),
            CustomAnalysisOrder(ticket=6, pl=5.0),
        ]
        rg_pass = ResultsGroup("PassOption1", orders=orders_pass)
        assert ot.filter_strategy("Proj", "Task", "Results", rg_pass) is True

    def test_outlier_trade_other_option(self) -> None:
        """Verify behavior when option is neither 0 nor 1."""
        ot = OutlierTrade()
        ot.set_input_args("1.1, 2")
        orders = [
            CustomAnalysisOrder(ticket=1, pl=100.0),
            CustomAnalysisOrder(ticket=2, pl=50.0),
            CustomAnalysisOrder(ticket=3, pl=20.0),
        ]
        rg = ResultsGroup("Option2", orders=orders)
        # When option != 0 and != 1, first_pl, second_pl, third_pl remain 0.0,
        # so first_pl (0.0) > threshold (0.0) is False -> returns True.
        assert ot.filter_strategy("Proj", "Task", "Results", rg) is True


class TestCustomAnalysisLegacyAnalyzers:
    """Test suite for retained CustomAnalysis analyzers for backward compatibility."""

    def test_correlation_filter_analyzer(self) -> None:
        """Verify retaining only strategies with correlation below threshold."""
        matrix = {
            "S1": {"S1": 1.0, "S2": 0.8, "S3": 0.2},
            "S2": {"S1": 0.8, "S2": 1.0, "S3": 0.3},
            "S3": {"S1": 0.2, "S2": 0.3, "S3": 1.0},
        }

        retained = CorrelationFilterAnalyzer.evaluate(
            ["S1", "S2", "S3"], matrix, max_correlation=0.5
        )
        assert retained == ("S1", "S3")

    def test_outlier_trade_analyzer(self) -> None:
        """Verify outlier trade detection and adjusted net profit calculation."""
        trades = (
            *(TradeRecord(ticket=i, profit_loss=50.0) for i in range(1, 10)),
            TradeRecord(ticket=10, profit_loss=1000.0),
        )

        report = OutlierTradeAnalyzer.evaluate(trades, std_multiplier=2.5)
        assert report.outlier_tickets == (10,)
        assert report.adjusted_net_profit == 450.0
        assert report.mean_pl == 145.0
        assert report.std_pl > 0.0

        d = report.to_dict()
        assert d["outlier_tickets"] == [10]
        assert d["adjusted_net_profit"] == 450.0

    def test_outlier_trade_analyzer_empty(self) -> None:
        """Verify empty trades sequence produces zero report."""
        report = OutlierTradeAnalyzer.evaluate(())
        assert report.outlier_tickets == ()
        assert report.adjusted_net_profit == 0.0
        assert report.mean_pl == 0.0
