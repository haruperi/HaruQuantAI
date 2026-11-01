"""Unit tests for ResultsReportService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_report import ResultsReportService


class TestResultsReportService:
    """Test suite for ResultsReportService."""

    def test_render_report_golden_fixture_escaping(self) -> None:
        """Verify report rendering and HTML escaping for strategy metadata."""
        service = ResultsReportService()
        sample = RunResult(
            result_id="res_rep_01",
            databank_id="Results",
            strategy_id="Strat_01",
            strategy_name="Strat <script>alert(1)</script> 01",
            trades=(
                {
                    "profit_loss": 200.0,
                    "type": "BUY",
                    "close_time": "2024-03-01T10:00:00Z",
                },
            ),
        )
        service.register_in_memory_result(sample)

        resp = service.render_report("proj_1", "Results", "Strat_01")
        doc = resp.data
        assert doc.strategy_id == "Strat_01"
        assert "<script>" not in doc.html_body
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in doc.html_body
        assert "<!DOCTYPE html>" in doc.html_body
        assert "Overview Metrics" in doc.html_body
        assert "Monthly Performance Matrix" in doc.html_body

        d = doc.to_dict()
        assert d["strategy_id"] == "Strat_01"
