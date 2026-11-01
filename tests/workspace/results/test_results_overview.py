"""Unit tests for ResultsOverviewService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_overview import ResultsOverviewService


def _create_overview_result(strategy_id: str = "Strat_01") -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name="SampleStrategy",
        trades=(
            {
                "ticket": 1,
                "profit_loss": 150.0,
                "type": "BUY",
                "close_time": "2024-01-15T12:00:00Z",
                "sample_type": "FullSample",
            },
            {
                "ticket": 2,
                "profit_loss": -50.0,
                "type": "SELL",
                "close_time": "2024-02-10T12:00:00Z",
                "sample_type": "FullSample",
            },
            {
                "ticket": 3,
                "profit_loss": 200.0,
                "type": "BUY",
                "close_time": "2024-02-20T12:00:00Z",
                "sample_type": "FullSample",
            },
        ),
        metrics={"net_profit": 300.0, "profit_factor": 6.0},
    )


class TestResultsOverviewService:
    """Test suite for ResultsOverviewService."""

    def test_overview_golden_fixture_and_template_selection(self) -> None:
        """Verify template fallback to SQDefault and metric calculations."""
        service = ResultsOverviewService()
        sample = _create_overview_result("Strat_01")
        service.register_in_memory_result(sample)

        resp = service.get_overview(
            "proj_1",
            "Results",
            "Strat_01",
            template=None,
            available_templates=("SQDefault", "SQDefaultPct"),
        )
        proj = resp.data
        assert proj.selected_template == "SQDefault"
        assert len(proj.metrics) >= 6

        net_profit_row = next(m for m in proj.metrics if m.metric_id == "NetProfit")
        assert net_profit_row.all_trades == 300.0
        assert net_profit_row.long_trades == 350.0
        assert net_profit_row.short_trades == -50.0

        assert len(proj.monthly_matrix) == 1
        year_row = proj.monthly_matrix[0]
        assert year_row.year == 2024
        assert year_row.months[0] == 150.0  # Jan
        assert year_row.months[1] == 150.0  # Feb: -50 + 200 = 150
        assert year_row.ytd_money == 300.0

        d = proj.to_dict()
        assert d["selected_template"] == "SQDefault"

    def test_explicit_template_override(self) -> None:
        """Verify explicit template selection overrides available templates."""
        service = ResultsOverviewService()
        sample = _create_overview_result("Strat_01")
        service.register_in_memory_result(sample)

        resp = service.get_overview(
            "proj_1",
            "Results",
            "Strat_01",
            template="CustomTemplate",
        )
        assert resp.data.selected_template == "CustomTemplate"
