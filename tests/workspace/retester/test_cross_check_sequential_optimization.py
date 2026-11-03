"""Unit tests for CrossCheckSequentialOptimizationService."""

from app.core.data.contracts import MarketBar
from app.core.trading.strategy.hsl.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    ParameterSpec,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_sequential_optimization import (
    CrossCheckSequentialOptimizationService,
    SequentialOptConfig,
    SequentialOptParameterRange,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
        parameters={
            "p1": ParameterSpec(type="float", default=10.0),
            "p2": ParameterSpec(type="float", default=1.0),
        },
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckSequentialOptimization:
    """Test suite for CrossCheckSequentialOptimizationService."""

    def test_golden_fixture_evaluations_count(self) -> None:
        """Sweeping 2 parameters (p1: 10..20 step 5 [3 vals], p2: 1..2 step 1 [2 vals]) executes 3+2=5 evals (not 6)."""
        strat = _make_strategy()
        bars: list[MarketBar] = []

        config = SequentialOptConfig(
            enabled=True,
            parameters=(
                SequentialOptParameterRange(name="p1", start=10.0, stop=20.0, step=5.0),
                SequentialOptParameterRange(name="p2", start=1.0, stop=2.0, step=1.0),
            ),
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinFit", metric="NetProfit", operator=">=", threshold=50.0
                ),
            ),
        )

        # Custom fitness function: p1 + p2 * 10
        # p1 sweeps [10, 15, 20]: with p2=1 -> [20, 25, 30]. Best p1=20 (fit=30). Locks p1=20.
        # p2 sweeps [1, 2]: with p1=20 -> [30, 40]. Best p2=2 (fit=40).
        def eval_fn(params: dict[str, float]) -> float:
            return params["p1"] + params["p2"] * 10.0

        res = CrossCheckSequentialOptimizationService.run(
            strat, bars, config, eval_fn=eval_fn
        )

        assert res.total_evaluations == 5
        assert res.per_parameter_evaluations == {"p1": 3, "p2": 2}
        assert res.best_parameters["p1"] == 20.0
        assert res.best_parameters["p2"] == 2.0
        assert res.best_fitness == 40.0
        assert res.passed is False  # 40.0 < threshold 50.0
        assert len(res.failure_reasons) == 1
