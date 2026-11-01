"""Unit tests for ResultsTradeListService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_trade_list import ResultsTradeListService


class TestResultsTradeListService:
    """Test suite for ResultsTradeListService."""

    def test_get_trades_golden_fixture_pagination(self) -> None:
        """Verify 5 trades with offset=1, limit=2 returns total_rows=5, len(rows)=2."""
        service = ResultsTradeListService()
        sample = RunResult(
            result_id="res_tl",
            databank_id="Results",
            strategy_id="Strat_TL",
            strategy_name="Strat_TL",
            strategy_payload={"initial_capital": 10000.0},
            trades=(
                {"ticket": 101, "profit_loss": 100.0, "symbol": "EURUSD"},
                {"ticket": 102, "profit_loss": 50.0, "symbol": "EURUSD"},
                {"ticket": 103, "profit_loss": -20.0, "symbol": "EURUSD"},
                {"ticket": 104, "profit_loss": 80.0, "symbol": "EURUSD"},
                {"ticket": 105, "profit_loss": 40.0, "symbol": "EURUSD"},
            ),
        )
        service.register_in_memory_result(sample)

        resp = service.get_trades(
            "proj_1",
            "Results",
            "Strat_TL",
            offset=1,
            limit=2,
        )
        page = resp.data
        assert page.total_rows == 5
        assert len(page.rows) == 2

        # First returned row should be trade #2 (since offset=1)
        row_0 = page.rows[0]
        assert row_0["NumberOfTrade"] == 2
        assert row_0["Ticket"] == 102
        assert row_0["ProfitLoss"] == 50.0
        # Balance after trade 1 (10100) + trade 2 (50) = 10150
        assert row_0["Balance"] == 10150.0

        d = page.to_dict()
        assert d["total_rows"] == 5
