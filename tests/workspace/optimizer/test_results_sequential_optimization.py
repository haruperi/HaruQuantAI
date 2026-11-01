"""Tests for ResultsSequentialOptimizationService."""

from app.workspace.optimizer.results_sequential_optimization import (
    ResultsSequentialOptimizationService,
    SequentialOptResultsPayload,
    SequentialOptStepProjection,
)


class TestResultsSequentialOptimizationService:
    """Test suite verifying sequential optimization curves and parameter application."""

    def test_golden_fixture_apply_params(self) -> None:
        """Verify golden fixture: apply_params with {'Period': 25} updates and returns updated map."""
        service = ResultsSequentialOptimizationService()
        resp = service.apply_params(
            project_id="proj_1",
            databank_name="Results",
            strategy_id="Strat_01",
            params={"Period": 25},
        )
        assert resp.request_id == "req_Strat_01_apply_params"
        assert resp.data == {"Period": 25}
        assert resp.data["Period"] == 25

    def test_get_results_retrieval(self) -> None:
        """Verify sequential results payload retrieval with steps."""
        service = ResultsSequentialOptimizationService()
        step1 = SequentialOptStepProjection(
            param_name="Period",
            original_value=14,
            best_value=25,
            tested_values=(10.0, 15.0, 20.0, 25.0),
            metric_values=(100.0, 120.0, 150.0, 200.0),
        )
        payload = SequentialOptResultsPayload(
            strategy_id="Strat_01",
            fitness_metric="NetProfit",
            original_metric=100.0,
            optimized_metric=200.0,
            steps=(step1,),
        )
        service.set_mock_payload("Strat_01", payload)

        resp = service.get_results("Strat_01")
        assert resp.data.strategy_id == "Strat_01"
        assert resp.data.optimized_metric == 200.0
        assert len(resp.data.steps) == 1
        assert resp.data.steps[0].best_value == 25
