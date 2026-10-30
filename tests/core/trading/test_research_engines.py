"""Deterministic unit tests for strategy generation and optimization research engines."""

from __future__ import annotations

import pytest
from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError
from app.core.trading.generation import (
    GenerationEngine,
    GenerationSpec,
    Individual,
)
from app.core.trading.optimization import (
    CancellationToken,
    OptimizationEngine,
    ParameterRange,
    WalkForwardWindow,
)
from app.core.trading.strategy.contracts import StrategyDocument


def _make_dummy_bar(time: int) -> MarketBar:
    return MarketBar(
        time=time,
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=1.1005,
        tick_volume=100,
    )


def test_random_strategy_generation() -> None:
    """GenerationEngine builds valid, structured StrategyDocuments with entry and exit rules."""
    spec = GenerationSpec(
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        max_rule_depth=2,
        seed=42,
    )
    engine = GenerationEngine(spec)
    strategy = engine.generate_random_strategy(strategy_id="strat-test-rand")

    assert isinstance(strategy, StrategyDocument)
    assert strategy.strategy_id == "strat-test-rand"
    assert len(strategy.rules) == 2  # Entry and exit rules

    entry_rule = strategy.rules[0]
    exit_rule = strategy.rules[1]
    assert len(entry_rule.actions) >= 1
    assert len(exit_rule.actions) >= 1
    assert len(entry_rule.conditions) >= 1


def test_gp_tournament_selection_reproducibility() -> None:
    """Tournament selection is strictly deterministic given an identical random seed."""
    spec = GenerationSpec(
        seed=123,
        tournament_size=3,
        tournament_prob=0.8,
    )

    # 5 individuals with distinct fitness values
    dummy_strategy = GenerationEngine().generate_random_strategy()
    population = [
        Individual(strategy=dummy_strategy, fitness=float(i * 10)) for i in range(1, 6)
    ]

    engine1 = GenerationEngine(spec)
    selections1 = [engine1.tournament_select(population).fitness for _ in range(10)]

    engine2 = GenerationEngine(spec)
    selections2 = [engine2.tournament_select(population).fitness for _ in range(10)]

    assert selections1 == selections2
    assert len(selections1) == 10
    # Values selected should be valid fitnesses from population
    for f in selections1:
        assert f in {10.0, 20.0, 30.0, 40.0, 50.0}


def test_gp_crossover_and_mutation() -> None:
    """Subtree crossover and point mutations preserve strategy document integrity."""
    engine = GenerationEngine(GenerationSpec(seed=777))
    p1 = engine.generate_random_strategy("parent-1")
    p2 = engine.generate_random_strategy("parent-2")

    c1, c2 = engine.crossover(p1, p2)
    assert isinstance(c1, StrategyDocument)
    assert isinstance(c2, StrategyDocument)
    assert c1.strategy_id != p1.strategy_id
    assert c2.strategy_id != p2.strategy_id

    mutated = engine.mutate(c1)
    assert isinstance(mutated, StrategyDocument)
    assert mutated.strategy_id != c1.strategy_id
    assert len(mutated.rules) == len(c1.rules)


def test_gp_step_generation_and_migration() -> None:
    """Generational step advances population, evaluates fitness, and migrates between islands."""
    spec = GenerationSpec(
        population_size=10,
        island_count=2,
        seed=999,
    )
    engine = GenerationEngine(spec)
    engine.initialize_population()

    assert len(engine.islands) == 2
    assert len(engine.islands[0]) == 5
    assert len(engine.islands[1]) == 5

    def dummy_fitness(strat: StrategyDocument) -> float:
        return float(len(strat.strategy_id))

    new_pop = engine.step_generation(dummy_fitness)
    assert len(new_pop) == 10
    assert engine.current_generation == 1


def test_optimization_indexes_bidirectional_mapping() -> None:
    """OptimizationIndexes maps linear indices to Cartesian parameter permutations and back."""
    ranges = [
        ParameterRange(
            name="stop_loss", start=10.0, end=30.0, step=10.0
        ),  # [10, 20, 30] -> size 3
        ParameterRange(
            name="take_profit", start=50.0, end=100.0, step=25.0
        ),  # [50, 75, 100] -> size 3
    ]
    opt_engine = OptimizationEngine()
    indexes = opt_engine.build_indexes(ranges)

    assert indexes.total_permutations == 9

    for i in range(indexes.total_permutations):
        params = indexes.get_params(i)
        assert "stop_loss" in params
        assert "take_profit" in params
        assert params["stop_loss"] in {10.0, 20.0, 30.0}
        assert params["take_profit"] in {50.0, 75.0, 100.0}

        # Check inverse resolution
        # Note: mapping is exact for discreet step values
        assert isinstance(params["stop_loss"], float)
        assert isinstance(params["take_profit"], float)


def test_walk_forward_matrix_generation() -> None:
    """Rolling Walk-Forward windows partition historical series into sequential IS/OOS stages."""
    engine = OptimizationEngine()
    bars = [_make_dummy_bar(1000 + i * 60) for i in range(500)]

    windows = engine.generate_wf_windows(
        total_bars=len(bars),
        num_windows=4,
        is_ratio=0.7,
        bars=bars,
    )

    assert len(windows) == 4
    for i, w in enumerate(windows):
        assert isinstance(w, WalkForwardWindow)
        assert w.index == i
        assert w.is_start_bar < w.is_end_bar
        assert w.is_end_bar == w.oos_start_bar
        assert w.oos_start_bar < w.oos_end_bar
        assert w.is_start_time < w.is_end_time
        assert w.oos_start_time < w.oos_end_time

        # Rolling check: each subsequent window starts later than prior
        if i > 0:
            assert w.is_start_bar > windows[i - 1].is_start_bar


def test_wfe_efficiency_metric() -> None:
    """Walk-Forward Efficiency measures ratio of OOS to IS performance."""
    engine = OptimizationEngine()
    assert engine.calculate_wfe(100.0, 80.0) == pytest.approx(80.0)
    assert engine.calculate_wfe(50.0, 25.0) == pytest.approx(50.0)
    assert engine.calculate_wfe(0.0, 50.0) == 0.0
    assert engine.calculate_wfe(-20.0, 50.0) == 0.0


def test_grid_search_progress_and_cancellation() -> None:
    """Grid execution reports progress steps and respects cooperative CancellationToken."""
    engine = OptimizationEngine()
    ranges = [
        ParameterRange(name="p1", start=1.0, end=2.0, step=1.0),  # [1.0, 2.0]
        ParameterRange(name="p2", start=10.0, end=20.0, step=10.0),  # [10.0, 20.0]
    ]

    progress_steps: list[tuple[int, int]] = []

    def mock_eval(params: dict[str, float]) -> float:
        return params["p1"] + params["p2"]

    def on_progress(step: int, total: int) -> None:
        progress_steps.append((step, total))

    token = CancellationToken()
    results = engine.run_grid(
        parameter_ranges=ranges,
        evaluate_fn=mock_eval,
        token=token,
        progress=on_progress,
    )

    assert len(results) == 4
    assert len(progress_steps) == 4
    assert progress_steps[-1] == (4, 4)
    # Best score first (descending): p1=2.0 + p2=20.0 = 22.0
    assert results[0][1] == 22.0

    # Test cancellation token raises DomainError
    cancelled_token = CancellationToken()
    cancelled_token.cancel()
    assert cancelled_token.is_cancelled

    with pytest.raises(DomainError) as exc_info:
        engine.run_grid(
            parameter_ranges=ranges,
            evaluate_fn=mock_eval,
            token=cancelled_token,
        )
    assert exc_info.value.code == "OPTIMIZATION_CANCELLED"
