"""Tests for FitnessMethodWFResultService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.fitness_method_w_f_result import (
    FitnessMethodWFResultConfig,
    FitnessMethodWFResultService,
    WFFitnessCriterion,
)


class TestFitnessMethodWFResultService:
    """Test suite verifying walk-forward fitness evaluation and normalization."""

    def test_golden_fixture_evaluation(self) -> None:
        """Verify golden fixture: NetProfit=500 (target 500) and WFPctOfProfitableRuns=80 (target 100) -> 0.9."""
        config = FitnessMethodWFResultConfig(
            criteria=(
                WFFitnessCriterion(
                    metric="NetProfit",
                    target_value=500.0,
                    weight=1.0,
                    maximize=True,
                ),
                WFFitnessCriterion(
                    metric="WFPctOfProfitableRuns",
                    target_value=100.0,
                    weight=1.0,
                    maximize=True,
                ),
            )
        )
        wf_results = [{"NetProfit": 500.0, "WFPctOfProfitableRuns": 80.0}]
        score = FitnessMethodWFResultService.evaluate(wf_results, config)
        assert score == 0.9

    def test_empty_and_none_results(self) -> None:
        """Verify None or empty results return 0.0."""
        config = FitnessMethodWFResultConfig()
        assert FitnessMethodWFResultService.evaluate(None, config) == 0.0
        assert FitnessMethodWFResultService.evaluate([], config) == 0.0

    def test_unknown_metric_rejection(self) -> None:
        """Verify DomainError code OPTIMIZER_UNKNOWN_WF_METRIC on unregistered metric."""
        config = FitnessMethodWFResultConfig(
            criteria=(WFFitnessCriterion(metric="NonExistentMetric"),)
        )
        with pytest.raises(DomainError) as exc_info:
            FitnessMethodWFResultService.evaluate([{"NetProfit": 100.0}], config)
        assert exc_info.value.code == "OPTIMIZER_UNKNOWN_WF_METRIC"

    def test_non_finite_values_clamped_to_zero(self) -> None:
        """Verify NaN or inf metric values are clamped to 0.0."""
        config = FitnessMethodWFResultConfig(
            criteria=(
                WFFitnessCriterion(metric="NetProfit", target_value=100.0, weight=1.0),
            )
        )
        wf_results = [{"NetProfit": float("nan")}]
        assert FitnessMethodWFResultService.evaluate(wf_results, config) == 0.0

    def test_minimization_metric(self) -> None:
        """Verify minimization criterion logic."""
        config = FitnessMethodWFResultConfig(
            criteria=(
                WFFitnessCriterion(
                    metric="Drawdown",
                    target_value=100.0,
                    maximize=False,
                    weight=1.0,
                ),
            )
        )
        # Drawdown = 20 on target 100 -> 1.0 - 0.2 = 0.8
        wf_results = [{"Drawdown": 20.0}]
        score = FitnessMethodWFResultService.evaluate(wf_results, config)
        assert score == 0.8
