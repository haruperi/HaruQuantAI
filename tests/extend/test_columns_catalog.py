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

    def test_all_121_databank_classes_subclass_databank_column(self) -> None:
        """Verify all 121 individual databank classes inherit from DatabankColumn."""
        from app.extend.columns.base import DatabankColumn
        from app.extend.columns.databanks import DATABANK_INSTANCES

        assert len(DATABANK_INSTANCES) == 121
        for cid, col in DATABANK_INSTANCES.items():
            assert isinstance(col, DatabankColumn)
            assert col.column_id == cid
            assert col.label
            assert col.value_type in {
                "MONEY",
                "PCT",
                "PIPS",
                "NUMBER",
                "INT",
                "TEXT",
                "DATETIME",
                "CHART",
            }
            assert col.descriptor.column_id == cid

    def test_all_31_trade_classes_subclass_tradelist_column(self) -> None:
        """Verify all 31 individual trade classes inherit from TradelistColumn."""
        from app.extend.columns.base import TradelistColumn
        from app.extend.columns.trades import TRADE_INSTANCES

        assert len(TRADE_INSTANCES) == 31
        for cid, col in TRADE_INSTANCES.items():
            assert isinstance(col, TradelistColumn)
            assert col.column_id == cid
            assert col.label
            assert col.value_type in {
                "MONEY",
                "PCT",
                "PIPS",
                "NUMBER",
                "INT",
                "TEXT",
                "DATETIME",
                "CHART",
            }
            assert col.descriptor.column_id == cid

    def test_all_8_walk_forward_classes_subclass_walk_forward_column(self) -> None:
        """Verify all 8 walk forward classes inherit from WalkForwardColumn."""
        from app.extend.columns.base import WalkForwardColumn
        from app.extend.columns.walk_forward import WALK_FORWARD_INSTANCES

        assert len(WALK_FORWARD_INSTANCES) == 8
        for cid, col in WALK_FORWARD_INSTANCES.items():
            assert isinstance(col, WalkForwardColumn)
            assert col.column_id == cid
            assert col.label
            assert col.value_type in {
                "MONEY",
                "PCT",
                "PIPS",
                "NUMBER",
                "INT",
                "TEXT",
                "DATETIME",
                "CHART",
            }
            assert col.descriptor.column_id == cid

    def test_metadata_and_text_databank_columns(self) -> None:
        """Verify text and metadata databank column extractions."""
        snapshot = StrategyStatsSnapshot(
            metrics={
                "symbol": "GBPUSD",
                "timeframe": "M15",
                "note": "Trend follower test",
                "BacktestDuration": "12.4s",
                "LongestTrade": "5d 4h",
            },
            parameters={"period": 14, "threshold": 2.0},
            strategy_name="TrendStrat",
        )

        assert DatabankColumnEvaluator.evaluate("ResultsName", snapshot) == "TrendStrat"
        assert DatabankColumnEvaluator.evaluate("Symbol", snapshot) == "GBPUSD"
        assert DatabankColumnEvaluator.evaluate("TimeFrame", snapshot) == "M15"
        assert (
            DatabankColumnEvaluator.evaluate("Note", snapshot) == "Trend follower test"
        )
        assert DatabankColumnEvaluator.evaluate("BacktestDuration", snapshot) == "12.4s"
        assert DatabankColumnEvaluator.evaluate("LongestTrade", snapshot) == "5d 4h"
        assert (
            DatabankColumnEvaluator.evaluate("MiniEquityChart", snapshot)
            == "[MiniChart]"
        )
        assert "threshold" in str(
            DatabankColumnEvaluator.evaluate("Parameters", snapshot)
        )

    def test_all_walk_forward_metrics_execution(self) -> None:
        """Verify all 8 WalkForward metrics compute correctly."""
        runs = (
            WalkForwardRunStats(
                run_index=1,
                net_profit=100.0,
                net_profit_pct=10.0,
                drawdown=20.0,
                drawdown_pct=2.0,
                trades_count=15,
                stagnation_pct=5.0,
                score=80.0,
            ),
            WalkForwardRunStats(
                run_index=2,
                net_profit=50.0,
                net_profit_pct=5.0,
                drawdown=30.0,
                drawdown_pct=3.0,
                trades_count=8,
                stagnation_pct=12.0,
                score=60.0,
            ),
        )

        assert WalkForwardColumnEvaluator.evaluate("WFMaxDDbyRun", runs) == 30.0
        assert WalkForwardColumnEvaluator.evaluate("WFMaxPctDDbyRun", runs) == 3.0
        assert WalkForwardColumnEvaluator.evaluate("WFMaxProfitByRun", runs) == 100.0
        assert (
            WalkForwardColumnEvaluator.evaluate("WFMaxProfitByRunInPct", runs) == 10.0
        )
        assert WalkForwardColumnEvaluator.evaluate("WFMaxStagnationInPct", runs) == 12.0
        assert WalkForwardColumnEvaluator.evaluate("WFMinTradesInRun", runs) == 8.0
        assert (
            WalkForwardColumnEvaluator.evaluate("WFPctOfProfitableRuns", runs) == 100.0
        )
        assert WalkForwardColumnEvaluator.evaluate("WFScore", runs) == 70.0

    def test_all_31_trades_columns_execution(self) -> None:
        """Verify all 31 trade columns extract expected fields."""
        trade = TradeRecord(
            ticket=42,
            symbol="EURUSD",
            type="SELL",
            direction="SELL",
            open_time="2026-01-01 10:00",
            close_time="2026-01-01 12:00",
            open_price=1.2000,
            close_price=1.1950,
            size=2.0,
            profit_loss=100.0,
            profit_loss_pips=50.0,
            profit_loss_pct=1.0,
            comment="scalp",
            mae=-10.0,
            mfe=120.0,
            mae_pips=-5.0,
            mfe_pips=60.0,
            sl_level=1.2050,
            pt_level=1.1900,
            sample_type="InSample",
            bars_in_trade=8,
            time_in_trade="2h",
            comm_swap=-2.5,
            slippage_money=-0.5,
            result_name="SubRun1",
        )

        for col in TradeColumnEvaluator.list_descriptors():
            val = TradeColumnEvaluator.evaluate(
                col.column_id,
                trade,
                index=5,
                running_balance=10200.0,
                running_dd_money=50.0,
                running_dd_pct=0.5,
            )
            assert val is not None, f"Trade column {col.column_id} evaluated to None"

    def test_all_121_databank_columns_evaluate_comprehensive(self) -> None:
        """Verify all 121 databank column classes evaluate cleanly against populated snapshots."""
        from app.extend.columns.databanks import (
            DATABANK_COLUMNS,
            DATABANK_INSTANCES,
            DatabankColumnEvaluator,
        )

        dummy_metrics: dict[str, float | int | str] = dict.fromkeys(
            DATABANK_COLUMNS, 1.23
        )
        dummy_metrics.update(
            {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "note": "A note",
                "drawdown": 50.0,
                "net_profit": 150.0,
                "strategy_name": "FullCoverageStrat",
                "BacktestDuration": "10s",
                "LongestTrade": "1d",
                "EntryIndicators": "RSI",
                "ExitIndicators": "SMA",
                "PriceIndicators": "ATR",
                "FiltersResult": "Pass",
            }
        )
        snapshot = StrategyStatsSnapshot(
            trades=(
                {
                    "ticket": 1,
                    "profit_loss": 200.0,
                    "sample_type": "FullSample",
                    "type": "BUY",
                },
                {
                    "ticket": 2,
                    "profit_loss": -50.0,
                    "sample_type": "FullSample",
                    "type": "SELL",
                },
            ),
            initial_deposit=10000.0,
            strategy_name="FullCoverageStrat",
            metrics=dummy_metrics,
        )

        for col_id, col in DATABANK_INSTANCES.items():
            val1 = col.compute(snapshot)
            assert str(val1) != "", f"col {col_id} compute returned empty"
            val2 = col.get_value(snapshot)
            assert val2 == val1
            val3 = DatabankColumnEvaluator.evaluate(col_id, snapshot)
            assert str(val3) != ""
