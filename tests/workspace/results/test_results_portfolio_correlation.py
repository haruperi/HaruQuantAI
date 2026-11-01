"""Unit tests for ResultsPortfolioCorrelationService."""

from __future__ import annotations

from app.workspace.results.results_portfolio_correlation import (
    PortfolioCorrelationRequest,
    ResultsPortfolioCorrelationService,
)


class TestResultsPortfolioCorrelationService:
    """Test suite for ResultsPortfolioCorrelationService."""

    def test_correlation_matrix_computation(self) -> None:
        """Verify Pearson correlation between identical, inverse, and uncorrelated series."""
        service = ResultsPortfolioCorrelationService()
        # s1: strictly increasing
        service.register_series("S1", [10.0, 20.0, 30.0, 40.0])
        # s2: identical to s1 -> corr = 1.0
        service.register_series("S2", [10.0, 20.0, 30.0, 40.0])
        # s3: strictly inverse to s1 -> corr = -1.0
        service.register_series("S3", [40.0, 30.0, 20.0, 10.0])

        req = PortfolioCorrelationRequest(
            strategy_ids=("S1", "S2", "S3"),
            period="DAY",
            method="ProfitLoss",
        )
        resp = service.compute(req)
        matrix_res = resp.data

        assert matrix_res.strategy_ids == ("S1", "S2", "S3")
        assert matrix_res.matrix["S1"]["S1"] == 1.0
        assert matrix_res.matrix["S1"]["S2"] == 1.0
        assert matrix_res.matrix["S1"]["S3"] == -1.0
        assert matrix_res.matrix["S2"]["S3"] == -1.0
        assert matrix_res.max_correlation == 1.0

        d = matrix_res.to_dict()
        assert d["period"] == "DAY"
        assert d["matrix"]["S1"]["S3"] == -1.0

    def test_correlation_single_or_empty(self) -> None:
        """Verify correlation computation with single strategy or default series."""
        service = ResultsPortfolioCorrelationService()
        req = PortfolioCorrelationRequest(strategy_ids=("S1",))
        resp = service.compute(req)
        assert resp.data.matrix["S1"]["S1"] == 1.0
        assert resp.data.avg_correlation == 1.0

    def test_stop_and_save_preferences(self) -> None:
        """Verify stopping request and preference saving."""
        service = ResultsPortfolioCorrelationService()
        stop_resp = service.stop("req_calc_01")
        assert stop_resp.data is True
        assert "req_calc_01" in service._stopped_requests

        pref_resp = service.save_preferences("WEEK", "PctReturn", True)
        assert pref_resp.data is True

    def test_request_to_dict(self) -> None:
        """Verify PortfolioCorrelationRequest to_dict."""
        req = PortfolioCorrelationRequest(
            strategy_ids=("A", "B"), period="MONTH", method="Drawdown"
        )
        d = req.to_dict()
        assert d["strategy_ids"] == ["A", "B"]
        assert d["period"] == "MONTH"
