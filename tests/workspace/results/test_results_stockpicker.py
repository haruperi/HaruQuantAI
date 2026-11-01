"""Unit tests for ResultsStockpickerService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_stockpicker import ResultsStockpickerService


class TestResultsStockpickerService:
    """Test suite for ResultsStockpickerService."""

    def test_stockpicker_golden_fixture(self) -> None:
        """Verify 3 trades (AAPL +100, AAPL -20, NVDA +300) sort NVDA first then AAPL."""
        service = ResultsStockpickerService()
        sample = RunResult(
            result_id="res_sp",
            databank_id="Results",
            strategy_id="Strat_SP",
            strategy_name="StockpickerStrategy",
            trades=(
                {"symbol": "AAPL", "profit_loss": 100.0, "bars_in_trade": 10},
                {"symbol": "AAPL", "profit_loss": -20.0, "bars_in_trade": 6},
                {"symbol": "NVDA", "profit_loss": 300.0, "bars_in_trade": 15},
            ),
        )
        service.register_in_memory_result(sample)

        resp = service.get_symbol_rows("proj_1", "Results", "Strat_SP")
        rows = resp.data.rows
        assert len(rows) == 2

        # First row: NVDA (net_profit=300.0)
        assert rows[0].symbol == "NVDA"
        assert rows[0].trade_count == 1
        assert rows[0].net_profit == 300.0
        assert rows[0].winning_pct == 100.0

        # Second row: AAPL (net_profit=80.0, 2 trades, 50% win)
        assert rows[1].symbol == "AAPL"
        assert rows[1].trade_count == 2
        assert rows[1].net_profit == 80.0
        assert rows[1].winning_pct == 50.0
        assert rows[1].avg_bars_in_trade == 8.0

        d = resp.data.to_dict()
        assert len(d["rows"]) == 2
