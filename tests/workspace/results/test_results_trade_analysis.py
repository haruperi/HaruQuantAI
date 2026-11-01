"""Unit tests for ResultsTradeAnalysisService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_trade_analysis import (
    ResultsTradeAnalysisService,
)


class TestResultsTradeAnalysisService:
    """Test suite for ResultsTradeAnalysisService."""

    def test_evaluate_golden_fixture_day_of_week(self) -> None:
        """Verify 2 Monday trades (+100, -40) and 1 Friday trade (+50)."""
        service = ResultsTradeAnalysisService()
        # 2024-01-15 is Monday, 2024-01-19 is Friday
        sample = RunResult(
            result_id="res_ta",
            databank_id="Results",
            strategy_id="Strat_TA",
            strategy_name="Strat_TA",
            trades=(
                {"profit_loss": 100.0, "close_time": "2024-01-15T10:00:00Z"},
                {"profit_loss": -40.0, "close_time": "2024-01-15T14:00:00Z"},
                {"profit_loss": 50.0, "close_time": "2024-01-19T11:00:00Z"},
            ),
        )
        service.register_in_memory_result(sample)

        resp = service.evaluate(
            "proj_1",
            "Results",
            "Strat_TA",
            pane_ids=("ProfitsByDayInWeek",),
        )
        panes = resp.data
        assert len(panes) == 1
        dow_pane = panes[0]
        assert dow_pane.pane_id == "ProfitsByDayInWeek"

        monday = next(b for b in dow_pane.buckets if b.label == "Monday")
        assert monday.trade_count == 2
        assert monday.profit_loss == 60.0
        assert monday.win_count == 1
        assert monday.loss_count == 1

        friday = next(b for b in dow_pane.buckets if b.label == "Friday")
        assert friday.trade_count == 1
        assert friday.profit_loss == 50.0
        assert friday.win_count == 1
        assert friday.loss_count == 0

        d = dow_pane.to_dict()
        assert d["pane_id"] == "ProfitsByDayInWeek"
