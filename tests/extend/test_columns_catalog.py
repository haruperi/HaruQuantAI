"""Unit tests for Columns extension catalog and evaluators."""

from __future__ import annotations

from app.extend.columns import (
    DATABANK_COLUMNS,
    TRADE_COLUMNS,
    WALK_FORWARD_COLUMNS,
    DatabankColumnEvaluator,
    StrategyStatsSnapshot,
    TradeColumnEvaluator,
    TradeRecord,
    WalkForwardColumnEvaluator,
    WalkForwardRunStats,
)


class TestColumnsCatalog:
    """Test suite verifying all 160 column definitions and evaluators."""

    def test_descriptors_registration_counts(self) -> None:
        """Verify that all 160 columns (121 Databanks, 31 Trades, 8 WalkForward) are registered."""
        assert len(DATABANK_COLUMNS) == 121
        assert len(TRADE_COLUMNS) == 31
        assert len(WALK_FORWARD_COLUMNS) == 8
        assert (
            len(DATABANK_COLUMNS) + len(TRADE_COLUMNS) + len(WALK_FORWARD_COLUMNS)
            == 160
        )

        db_descriptors = DatabankColumnEvaluator.list_descriptors()
        assert len(db_descriptors) == 121

        trade_descriptors = TradeColumnEvaluator.list_descriptors()
        assert len(trade_descriptors) == 31

        wf_descriptors = WalkForwardColumnEvaluator.list_descriptors()
        assert len(wf_descriptors) == 8

    def test_golden_fixture_databanks(self) -> None:
        """Verify Databanks evaluator golden fixture with 4 trades."""
        snapshot = StrategyStatsSnapshot(
            trades=(
                {"ticket": 1, "profit_loss": 200.0},
                {"ticket": 2, "profit_loss": -50.0},
                {"ticket": 3, "profit_loss": 150.0},
                {"ticket": 4, "profit_loss": -100.0},
            ),
            initial_deposit=10000.0,
            strategy_name="GoldenStrat",
        )

        assert DatabankColumnEvaluator.evaluate("NetProfit", snapshot) == 200.0
        assert DatabankColumnEvaluator.evaluate("GrossProfit", snapshot) == 350.0
        assert DatabankColumnEvaluator.evaluate("GrossLoss", snapshot) == -150.0
        assert DatabankColumnEvaluator.evaluate("ProfitFactor", snapshot) == 2.33
        assert DatabankColumnEvaluator.evaluate("NumberOfTrades", snapshot) == 4
        assert DatabankColumnEvaluator.evaluate("WinningPct", snapshot) == 50.0
        assert DatabankColumnEvaluator.evaluate("AvgTrade", snapshot) == 50.0
        assert DatabankColumnEvaluator.evaluate("MaxProfit", snapshot) == 200.0
        assert DatabankColumnEvaluator.evaluate("MaxLoss", snapshot) == -100.0
        assert (
            DatabankColumnEvaluator.evaluate("ResultsName", snapshot) == "GoldenStrat"
        )

    def test_databanks_zero_trades_and_zero_loss_boundary(self) -> None:
        """Verify zero-trade and zero-gross-loss safe divisions."""
        empty_snapshot = StrategyStatsSnapshot(trades=(), initial_deposit=10000.0)
        assert DatabankColumnEvaluator.evaluate("ProfitFactor", empty_snapshot) == 0.0
        assert DatabankColumnEvaluator.evaluate("ReturnDDRatio", empty_snapshot) == 0.0
        assert DatabankColumnEvaluator.evaluate("WinningPct", empty_snapshot) == 0.0
        assert (
            DatabankColumnEvaluator.evaluate("InitialDeposit", empty_snapshot)
            == 10000.0
        )

        all_wins = StrategyStatsSnapshot(
            trades=({"ticket": 1, "profit_loss": 500.0},),
            initial_deposit=10000.0,
        )
        assert DatabankColumnEvaluator.evaluate("ProfitFactor", all_wins) == 500.0
        assert DatabankColumnEvaluator.evaluate("ReturnDDRatio", all_wins) == 500.0

    def test_golden_fixture_trades(self) -> None:
        """Verify Trades evaluator golden fixture."""
        trade = TradeRecord(
            ticket=1,
            symbol="EURUSD",
            type="BUY",
            open_price=1.1000,
            close_price=1.1050,
            size=1.0,
            profit_loss=500.0,
            profit_loss_pct=5.0,
        )

        assert (
            TradeColumnEvaluator.evaluate(
                "NumberOfTrade",
                trade,
                index=1,
                running_balance=10500.0,
                running_dd_money=0.0,
                running_dd_pct=0.0,
            )
            == 1
        )
        assert (
            TradeColumnEvaluator.evaluate(
                "ProfitLoss",
                trade,
                index=1,
                running_balance=10500.0,
                running_dd_money=0.0,
                running_dd_pct=0.0,
            )
            == 500.0
        )
        assert (
            TradeColumnEvaluator.evaluate(
                "Balance",
                trade,
                index=1,
                running_balance=10500.0,
                running_dd_money=0.0,
                running_dd_pct=0.0,
            )
            == 10500.0
        )
        assert (
            TradeColumnEvaluator.evaluate(
                "ProfitLossPct",
                trade,
                index=1,
                running_balance=10500.0,
                running_dd_money=0.0,
                running_dd_pct=0.0,
            )
            == 5.0
        )

    def test_golden_fixture_walk_forward(self) -> None:
        """Verify WalkForward evaluator golden fixture."""
        runs = (
            WalkForwardRunStats(run_index=1, net_profit=100.0),
            WalkForwardRunStats(run_index=2, net_profit=-20.0),
            WalkForwardRunStats(run_index=3, net_profit=80.0),
            WalkForwardRunStats(run_index=4, net_profit=40.0),
        )

        assert (
            WalkForwardColumnEvaluator.evaluate("WFPctOfProfitableRuns", runs) == 75.0
        )
        assert WalkForwardColumnEvaluator.evaluate("WFMaxProfitByRun", runs) == 100.0
        assert WalkForwardColumnEvaluator.evaluate("WFMaxProfitByRun", ()) == 0.0
