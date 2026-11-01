"""Tests for FitnessMethodExistingPortfolio service."""

from __future__ import annotations

from app.workspace.portfolio_master.fitness_method_existing_portfolio import (
    ExistingPortfolioCriterion,
    ExistingPortfolioFitnessConfig,
    FitnessMethodExistingPortfolioService,
)


class TestFitnessMethodExistingPortfolioService:
    """Test suite for FitnessMethodExistingPortfolioService."""

    def test_golden_fixture_normalization_and_weights(self) -> None:
        """Assert exact golden fixture from line 182 in 11-AppPortfolioMaster.md."""
        config = ExistingPortfolioFitnessConfig(
            criteria=(
                ExistingPortfolioCriterion(
                    metric_id="ReturnDD",
                    value_type=1,
                    approximate_type=2,
                    weight=1.0,
                    target=0.0,
                ),
                ExistingPortfolioCriterion(
                    metric_id="PctStagnation",
                    value_type=1,
                    approximate_type=2,
                    weight=1.0,
                    target=0.0,
                ),
            )
        )
        stats = {"ReturnDDRatio": 10.0, "StagnationPct": 20.0}
        score = FitnessMethodExistingPortfolioService.evaluate(stats, config)
        assert score == 0.775

    def test_normalize_criterion(self) -> None:
        """Assert target field state normalization resets target when disabled."""
        # When value_type differs from approximate_type
        criterion_disabled = ExistingPortfolioCriterion(
            metric_id="NetProfit",
            value_type=1,
            approximate_type=2,
            weight=1.5,
            target=500.0,
        )
        norm, target_state = FitnessMethodExistingPortfolioService.normalize_criterion(
            criterion_disabled
        )
        assert target_state.enabled is False
        assert target_state.target == 0.0
        assert norm.target == 0.0

        # When value_type equals approximate_type
        criterion_enabled = ExistingPortfolioCriterion(
            metric_id="NetProfit",
            value_type=2,
            approximate_type=2,
            weight=1.5,
            target=500.0,
        )
        norm_en, target_state_en = (
            FitnessMethodExistingPortfolioService.normalize_criterion(criterion_enabled)
        )
        assert target_state_en.enabled is True
        assert target_state_en.target == 500.0
        assert norm_en.target == 500.0

    def test_approximate_target_scoring(self) -> None:
        """Assert approximate target matching scores closer values higher."""
        # NetProfit range is -10000..10000, span = 20000
        # target = 2000.0
        # test with stats = 2000.0 -> diff 0 -> score 1.0
        config_exact = ExistingPortfolioFitnessConfig(
            criteria=(
                ExistingPortfolioCriterion(
                    metric_id="NetProfit",
                    value_type=2,
                    approximate_type=2,
                    weight=1.0,
                    target=2000.0,
                ),
            )
        )
        assert (
            FitnessMethodExistingPortfolioService.evaluate(
                {"NetProfit": 2000.0}, config_exact
            )
            == 1.0
        )

        # test with stats = 4000.0 -> diff 2000 / 20000 = 0.1 -> score 0.9
        assert (
            FitnessMethodExistingPortfolioService.evaluate(
                {"NetProfit": 4000.0}, config_exact
            )
            == 0.9
        )

    def test_zero_weights_or_empty_criteria(self) -> None:
        """Assert zero weights and empty criteria return 0.0."""
        config_empty = ExistingPortfolioFitnessConfig(criteria=())
        assert FitnessMethodExistingPortfolioService.evaluate({}, config_empty) == 0.0

        config_zero = ExistingPortfolioFitnessConfig(
            criteria=(
                ExistingPortfolioCriterion(
                    metric_id="ReturnDD",
                    weight=0.0,
                ),
            )
        )
        assert (
            FitnessMethodExistingPortfolioService.evaluate(
                {"ReturnDDRatio": 10.0}, config_zero
            )
            == 0.0
        )
