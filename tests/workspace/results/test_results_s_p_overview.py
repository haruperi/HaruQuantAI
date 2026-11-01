"""Unit tests for ResultsSPOverviewService and Stockpicker overview."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_s_p_overview import ResultsSPOverviewService


class TestResultsSPOverviewService:
    """Test suite for ResultsSPOverviewService."""

    def test_sp_overview_golden_fixture(self) -> None:
        """Verify per-symbol realized P&L breakdown and open positions."""
        service = ResultsSPOverviewService()
        sample = RunResult(
            result_id="res_sp_01",
            databank_id="Results",
            strategy_id="SP_Strat_01",
            strategy_name="SP_Strategy",
            trades=(
                {"symbol": "AAPL", "profit_loss": 400.0},
                {"symbol": "AAPL", "profit_loss": 200.0},
                {"symbol": "MSFT", "profit_loss": 400.0},
            ),
            strategy_payload={
                "open_positions": [
                    {"symbol": "NVDA", "weight_pct": 25.0, "size": 10.0},
                    {"symbol": "AAPL", "weight_pct": 40.0, "size": 15.0},
                ]
            },
            metrics={"cagr": 18.5, "drawdown_pct": 12.0, "sharpe_ratio": 1.4},
        )
        service.register_in_memory_result(sample)

        resp = service.get_sp_overview("proj_1", "Results", "SP_Strat_01")
        proj = resp.data
        assert proj.symbol_breakdown == {"AAPL": 600.0, "MSFT": 400.0}
        assert proj.cagr_pct == 18.5
        assert proj.max_dd_pct == 12.0

        # Open positions sorted by descending weight_pct: AAPL (40%), NVDA (25%)
        assert len(proj.open_positions) == 2
        assert proj.open_positions[0].symbol == "AAPL"
        assert proj.open_positions[0].weight_pct == 40.0
        assert proj.open_positions[1].symbol == "NVDA"
        assert proj.open_positions[1].weight_pct == 25.0

        d = proj.to_dict()
        assert d["symbol_breakdown"]["AAPL"] == 600.0
