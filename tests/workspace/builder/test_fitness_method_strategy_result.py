"""Unit tests for FitnessMethodStrategyResult service and models."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.fitness_method_strategy_result import (
    FitnessCriterion,
    FitnessMethodStrategyResultConfig,
    FitnessMethodStrategyResultService,
)


@dataclass
class MockStats:
    """Mock strategy statistics snapshot."""

    return_dd_ratio: float = 4.0
    profit_factor: float = 1.5
    number_of_trades: int = 50


def test_golden_fixture_weighted_fitness() -> None:
    """Verify golden fixture: 2 criteria yielding 0.833333 fitness."""
    service = FitnessMethodStrategyResultService()
    config = FitnessMethodStrategyResultConfig(
        mode="WEIGHTED",
        criteria=(
            FitnessCriterion(
                column_id="ReturnDDRatio",
                target_value=4.0,
                weight=2.0,
                maximize=True,
            ),
            FitnessCriterion(
                column_id="ProfitFactor",
                target_value=3.0,
                weight=1.0,
                maximize=True,
            ),
        ),
    )

    stats = MockStats(return_dd_ratio=4.0, profit_factor=1.5, number_of_trades=50)
    fitness = service.evaluate(stats, config)
    assert fitness == 0.833333


def test_zero_trades_returns_zero() -> None:
    """Ensure zero trades returns 0.0 fitness regardless of other metrics."""
    service = FitnessMethodStrategyResultService()
    config = FitnessMethodStrategyResultConfig()
    stats = {"ReturnDDRatio": 10.0, "number_of_trades": 0}
    assert service.evaluate(stats, config) == 0.0


def test_dict_stats_support() -> None:
    """Ensure stats supplied as dictionary are evaluated correctly."""
    service = FitnessMethodStrategyResultService()
    config = FitnessMethodStrategyResultConfig(
        criteria=(
            FitnessCriterion(column_id="SharpeRatio", target_value=2.0, weight=1.0),
        )
    )
    stats = {"SharpeRatio": 1.0, "number_of_trades": 25}
    assert service.evaluate(stats, config) == 0.5


def test_minimize_criterion() -> None:
    """Ensure maximize=False inverts score (1.0 - score)."""
    service = FitnessMethodStrategyResultService()
    config = FitnessMethodStrategyResultConfig(
        criteria=(
            FitnessCriterion(
                column_id="Drawdown", target_value=20.0, weight=1.0, maximize=False
            ),
        )
    )
    stats = {"Drawdown": 5.0, "number_of_trades": 30}
    # 5.0 / 20.0 = 0.25 -> inverted = 0.75
    assert service.evaluate(stats, config) == 0.75


def test_invalid_weights_raise() -> None:
    """Ensure empty criteria or zero total weight raises BUILDER_INVALID_FITNESS_WEIGHTS."""
    service = FitnessMethodStrategyResultService()

    with pytest.raises(DomainError) as exc:
        service.evaluate(
            {"number_of_trades": 10}, FitnessMethodStrategyResultConfig(criteria=())
        )
    assert exc.value.code == "BUILDER_INVALID_FITNESS_WEIGHTS"

    with pytest.raises(DomainError) as exc:
        service.evaluate(
            {"number_of_trades": 10},
            FitnessMethodStrategyResultConfig(
                criteria=(FitnessCriterion(column_id="A", weight=0.0),)
            ),
        )
    assert exc.value.code == "BUILDER_INVALID_FITNESS_WEIGHTS"
