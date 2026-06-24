# ruff: noqa: E402, E501, PLR2004, D, ANN, S101
"""Coverage expansion tests for Optimization Service."""

import sys
from unittest.mock import MagicMock, patch

# Setup mock simulator module dynamically for the test run
class MockEngine:
    def __init__(self) -> None:
        self.deals: dict = {}

class MockOrchestrator:
    def __init__(self, engine) -> None:
        self.engine = engine
    def execute(self, payload) -> dict:
        return {
            "status": "success",
            "data": {
                "run_id": "opt_run_mock",
                "summary_metrics": {
                    "ending_balance": 100000.0,
                    "net_profit": 0.0,
                    "total_trades": 0,
                }
            }
        }

mock_simulator_engine = MagicMock()
mock_simulator_engine.EventDrivenExecutionEngine = MockEngine
mock_simulator_orch = MagicMock()
mock_simulator_orch.BacktestOrchestrator = MockOrchestrator
mock_simulator_base = MagicMock()
mock_strategies_base = MagicMock()
mock_registry = MagicMock()

_original_modules: dict = {}
_original_evaluate_single_fold = None

def setup_module(module) -> None:
    for name in [
        "app.services.simulator",
        "app.services.simulator.engine",
        "app.services.simulator.orchestrator",
        "app.services.strategies",
        "app.services.strategies.registry"
    ]:
        _original_modules[name] = sys.modules.get(name)
    sys.modules["app.services.simulator"] = mock_simulator_base
    sys.modules["app.services.simulator.engine"] = mock_simulator_engine
    sys.modules["app.services.simulator.orchestrator"] = mock_simulator_orch
    sys.modules["app.services.strategies"] = mock_strategies_base
    sys.modules["app.services.strategies.registry"] = mock_registry

    import app.services.optimization.sweeps as sweeps
    global _original_evaluate_single_fold
    _original_evaluate_single_fold = sweeps._evaluate_single_fold

    def mock_evaluate_single_fold(
        fold_idx, fold, strategy_ref, symbols, timeframe, request, dry_run, **kwargs
    ):
        kwargs.pop("dry_run", None)
        return _original_evaluate_single_fold(
            fold_idx, fold, strategy_ref, symbols, timeframe, request, dry_run, **kwargs
        )

    sweeps._evaluate_single_fold = mock_evaluate_single_fold

def teardown_module(module) -> None:
    import app.services.optimization.sweeps as sweeps
    global _original_evaluate_single_fold
    if _original_evaluate_single_fold is not None:
        sweeps._evaluate_single_fold = _original_evaluate_single_fold

    for name, orig in _original_modules.items():
        if orig is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = orig

import pytest
from datetime import timedelta
from app.services.optimization.models import (
    ParameterSpace,
    ParameterRange,
    WalkForwardRequest,
    WalkForwardResponse,
    WalkForwardWindow,
    OptimizationSummary,
    OptimizationResultItem,
)
from app.services.optimization.sweeps import (
    compare_optimization_runs,
    walk_forward,
    parallel_walk_forward,
    optimization_walk_forward,
    run_optimization_task,
    run_walk_forward_task,
    analyze_walk_forward_results,
    analyze_parallel_results,
    save_optimization_result,
    build_optimization_report,
)
from app.services.optimization.splitting import (
    expanding_window_split,
    run_walk_forward_optimization,
    run_walk_forward_matrix,
)
from app.services.optimization.robustness import (
    assess_strategy_robustness,
    run_slippage_stress_test,
    run_spread_stress_test,
    run_commission_stress_test,
    optimization_monte_carlo,
)
from app.services.optimization.algorithms.bayesian import bayesian_optimization
from app.services.optimization.algorithms.genetic import genetic_algorithm
from app.services.optimization.algorithms.grid import grid_search, parallel_grid_search
from app.services.optimization.algorithms.random import random_search, parallel_random_search


@pytest.fixture
def sample_space() -> ParameterSpace:
    return ParameterSpace(
        parameters=[
            ParameterRange(name="short", type="int", min_value=5, max_value=6),
            ParameterRange(name="long", type="int", min_value=10, max_value=12),
        ]
    )


# --- Sweeps Tests ---
def test_compare_optimization_runs() -> None:
    res = compare_optimization_runs(["run1"], [{"best_score": 1.5, "total_candidates": 10, "objective": "sharpe"}])
    assert res["run1"]["best_score"] == 1.5


def test_walk_forward_orchestration(sample_space: ParameterSpace) -> None:
    req = WalkForwardRequest(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-05T00:00:00Z",
        parameter_space=sample_space,
        objective="sharpe",
        initial_balance=10000.0,
        folds=2,
        fold_mode="rolling",
    )
    res = walk_forward("trend_following", ["EURUSD"], "M1", "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", req)
    assert res.walk_forward_score == 0.0

    res_parallel = parallel_walk_forward("trend_following", ["EURUSD"], "M1", "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", req, max_workers=2)
    assert res_parallel.walk_forward_score == 0.0

    res_user = optimization_walk_forward("trend_following", ["EURUSD"], "M1", "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", sample_space, folds=2)
    print("res_user:", res_user)
    assert res_user["status"] == "success"


def test_walk_forward_error_handling(sample_space: ParameterSpace) -> None:
    # Cause random_search to fail inside WFA evaluation
    with patch("app.services.optimization.sweeps.random_search", side_effect=ValueError("Test Failure")):
        req = WalkForwardRequest(
            strategy_ref="trend_following",
            symbols=["EURUSD"],
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-05T00:00:00Z",
            parameter_space=sample_space,
            objective="sharpe",
            initial_balance=10000.0,
            folds=2,
            fold_mode="expanding",
        )
        res_user = optimization_walk_forward("trend_following", ["EURUSD"], "M1", "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", sample_space, fold_mode="expanding", folds=2)
        assert res_user["status"] == "error"


def test_background_task_orchestration() -> None:
    tid1 = run_optimization_task({"test": 1})
    assert tid1.startswith("task_opt_")

    tid2 = run_walk_forward_task({"test": 2})
    assert tid2.startswith("task_wfa_")

    wfar = WalkForwardResponse(run_id="wfa1", walk_forward_score=1.0, oos_retention_score=0.9, parameter_drift_score=0.1, walk_forward_efficiency=75.0, status="ready_for_risk_review", evidence={"ok": True})
    assert analyze_walk_forward_results(wfar) == {"ok": True}

    assert "total_runs" in analyze_parallel_results([])
    assert save_optimization_result({})["saved"] is True

    from app.services.optimization.models import ParameterCandidate
    best_cand = ParameterCandidate(parameters={"short": 5}, candidate_hash="hash")
    summary = OptimizationSummary(
        objective="sharpe",
        best_score=1.5,
        total_candidates=5,
        runtime_ms=10.0,
        candidates=[],
        best_candidate=best_cand,
    )
    report = build_optimization_report(summary)
    assert "Strategy Optimization Report" in report["formatted_report"]


# --- Splitting Tests ---
def test_expanding_window_split_branches() -> None:
    # Test expanding window split edge cases where train/test windows overlap or are truncated
    from datetime import datetime
    start = datetime(2026, 1, 1)
    end = datetime(2026, 1, 10)
    folds = expanding_window_split(start, end, folds=2, purging_bars=5, embargo_bars=10)
    assert len(folds) == 2


def test_run_walk_forward_optimization(sample_space: ParameterSpace) -> None:
    # Dry run success path
    res = run_walk_forward_optimization(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-05T00:00:00Z",
        parameter_space=sample_space,
        dry_run=True,
    )
    assert res["status"] == "success"

    # Exception path inside loop
    with patch("app.services.optimization.algorithms.random.random_search", side_effect=ValueError("Random search fail")):
        res_fail = run_walk_forward_optimization(
            strategy_ref="trend_following",
            symbols=["EURUSD"],
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-05T00:00:00Z",
            parameter_space=sample_space,
            dry_run=True,
        )
        # Should catch and record fold-level error
        assert "error" in res_fail["data"]["folds"][0]


def test_run_walk_forward_matrix(sample_space: ParameterSpace) -> None:
    with pytest.raises(ValueError, match="strategy_refs and parameter_spaces must have the same length"):
        run_walk_forward_matrix(["s1", "s2"], ["EURUSD"], "M1", "", "", [sample_space])

    res = run_walk_forward_matrix(["s1"], ["EURUSD"], "M1", "2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z", [sample_space], dry_run=True)
    assert res["status"] == "success"
    assert "s1" in res["data"]["matrix"]


# --- Robustness Tests ---
def test_robustness_stress_shocks() -> None:
    trades = [{"profit": 100.0, "volume": 1.0, "close_time": "2026-06-23T12:00:00Z"}]
    # Zero trades edge cases
    assert len(run_slippage_stress_test([], slippage_pips=1.0)) == 0
    assert len(run_spread_stress_test([], spread_multiplier=2.0)) == 0
    assert len(run_commission_stress_test([], extra_commission_per_lot=5.0)) == 0

    # Ruin probability edge check
    res = optimization_monte_carlo(trades, simulation_method="resample_trades", initial_balance=50.0)
    assert 0.0 <= res.ruin_probability <= 1.0


# --- Search Algorithms Coverage ---
def test_bayesian_optimization_strict_backend(sample_space: ParameterSpace) -> None:
    from app.services.optimization.helpers import OptimizationExecutionError
    with pytest.raises(OptimizationExecutionError, match="Bayesian optimization backend"):
        bayesian_optimization(
            strategy_ref="trend_following",
            symbols=["EURUSD"],
            timeframe="M1",
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
            parameter_space=sample_space,
            strict_backend=True,
            dry_run=True,
        )


def test_genetic_algorithm_strict_backend(sample_space: ParameterSpace) -> None:
    # Genetic algorithm is pure Python and runs without external dependency errors
    res = genetic_algorithm(
        strategy_ref="trend_following",
        symbols=["EURUSD"],
        timeframe="M1",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        parameter_space=sample_space,
        dry_run=True,
    )
    assert res.objective == "sharpe"
