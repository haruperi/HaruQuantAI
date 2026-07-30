"""Shared public-boundary builders for Optimization usage programs."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.analytics import (
    build_performance_report,
    create_analytics_run_config,
    create_risk_free_rate_evidence,
    create_statistical_validation_config,
)
from app.services.optimization import (
    build_optimization_evidence,
    build_simulation_analytics_backtest_adapter,
    candidate_hash,
    create_optimization_value,
    parameter_space_hash,
    run_bounded_search,
)
from app.utils import canonical_digest, canonical_json, generate_id
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
_STATE = tempfile.TemporaryDirectory(prefix="optimization-usage-")


def parameter_space() -> object:
    """Build a bounded executable parameter space through the public API."""
    period = create_optimization_value(
        "ParameterRange",
        name="period",
        kind="integer",
        minimum=Decimal(2),
        maximum=Decimal(3),
        step=Decimal(1),
    )
    return create_optimization_value(
        "ParameterSpace",
        parameters=(period,),
        constraints=("period >= 2",),
    )


def conditional_parameter_space() -> object:
    """Build a conditional parameter space for projection evidence."""
    enabled = create_optimization_value(
        "ParameterRange", name="enabled", kind="boolean"
    )
    period = create_optimization_value(
        "ParameterRange",
        name="period",
        kind="integer",
        minimum=Decimal(2),
        maximum=Decimal(3),
        step=Decimal(1),
        active_when="enabled == True",
    )
    return create_optimization_value(
        "ParameterSpace",
        parameters=(enabled, period),
        constraints=("period >= 2",),
    )


def analytics_config() -> object:
    """Build bounded Analytics policy through its function-only boundary."""
    rate = create_risk_free_rate_evidence(
        rate=Decimal("0.02"),
        unit="annual_decimal",
        source="optimization-usage-policy",
        as_of=NOW,
    )
    statistics = create_statistical_validation_config(
        seed=1,
        bootstrap_iterations=10,
        permutation_iterations=10,
        confidence=0.95,
        alpha=0.05,
    )
    return create_analytics_run_config(
        max_warning_detail_bytes=1024,
        max_trades=100,
        max_equity_points=100,
        max_benchmark_points=100,
        max_statistical_observations=100,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=100_000,
        risk_free_rate=rate,
        statistics=statistics,
    )


def execution_context(dataset: object | None = None) -> object:
    """Build complete execution provenance, optionally from genuine MT5 data."""
    if dataset is None:
        start = NOW
        end = NOW + timedelta(days=1)
        data_ref = "documented-dataset"
        data_hash = "b" * 64
        symbol = "EURUSD"
        timeframe = "M1"
    else:
        start = dataset.start
        end = dataset.end
        data_ref = f"mt5:{dataset.symbol}:{dataset.timeframe}"
        data_hash = canonical_digest(dataset.model_dump(mode="python", warnings=False))
        symbol = dataset.symbol
        timeframe = dataset.timeframe
    return create_optimization_value(
        "BacktestExecutionContext",
        strategy_id="strategy-1",
        strategy_version="v1",
        strategy_config_ref="strategy-config",
        strategy_config_hash="a" * 64,
        data_ref=data_ref,
        data_version="v1",
        data_hash=data_hash,
        tick_generation_ref="tick-profile",
        tick_generation_version="v1",
        tick_generation_hash="c" * 64,
        execution_profile_ref="execution-profile",
        execution_profile_version="v1",
        execution_profile_hash="d" * 64,
        risk_policy_ref="risk-policy",
        risk_policy_version="v1",
        risk_policy_hash="e" * 64,
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        initial_balance=Decimal(10_000),
        account_currency="USD",
        runtime_profile="simulation",
        canonical=True,
        cost_model_hash="f" * 64,
        realism_hash="1" * 64,
        objective_hash="2" * 64,
        engine_type="event_driven",
        engine_version="v1",
        module_version="v1",
    )


def execution_request(dataset: object | None = None) -> object:
    """Build one candidate request bound to the selected evidence."""
    context = execution_context(dataset)
    space = parameter_space()
    executable = {"enabled": True, "period": 2}
    digest = candidate_hash(
        strategy_hash="a" * 64,
        data_hash=context.data_hash,
        cost_model_hash=context.cost_model_hash,
        realism_hash=context.realism_hash,
        objective_hash=context.objective_hash,
        engine_type=context.engine_type,
        engine_version=context.engine_version,
        module_version=context.module_version,
        space_hash=parameter_space_hash(space),
        executable_parameters=executable,
    )
    return create_optimization_value(
        "BacktestExecutionRequest",
        candidate_hash=digest,
        executable_parameters=executable,
        seed=7,
        request_id="req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        workflow_id="wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        correlation_id="cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        context=context,
    )


def search_request(dataset: object | None = None, **overrides: object) -> object:
    """Build a bounded search request."""
    values: dict[str, object] = {
        "space": parameter_space(),
        "execution_context": execution_context(dataset),
        "method": "grid",
        "objective": "net_pnl",
        "enabled_objectives": frozenset({"net_pnl"}),
        "max_candidates": 3,
        "max_parameter_space_expansion": 4,
        "max_constraint_count": 5,
        "max_runtime_seconds": 30.0,
        "request_id": "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "workflow_id": "wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "correlation_id": "cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    }
    values.update(overrides)
    return create_optimization_value("SearchRequest", **values)


def walk_forward_request(dataset: object | None = None, **overrides: object) -> object:
    """Build a valid three-fold chronological request."""
    start = dataset.start if dataset is not None else NOW
    values: dict[str, object] = {
        "search": search_request(dataset),
        "mode": "rolling",
        "observation_times": tuple(
            start + timedelta(minutes=index) for index in range(11)
        ),
        "train_bars": 3,
        "test_bars": 2,
        "step_bars": 2,
        "purge_bars": 1,
        "embargo_bars": 1,
        "average_trade_duration_bars": 1,
        "minimum_fold_count": 3,
    }
    values.update(overrides)
    return create_optimization_value("WalkForwardRequest", **values)


def monte_carlo_request(**overrides: object) -> object:
    """Build a bounded robustness request from explicit observed outcomes."""
    values: dict[str, object] = {
        "outcomes": (Decimal(10), Decimal(-5), Decimal(3)),
        "initial_balance": Decimal(100),
        "method": "resample_returns",
        "simulations": 5,
        "seed": 17,
        "ruin_threshold": Decimal(50),
        "confidence_level": 0.8,
    }
    values.update(overrides)
    return create_optimization_value("MonteCarloRequest", **values)


def candidate_score(candidate: str, value: float, trades: int = 1) -> object:
    """Build one candidate score through the function-only boundary."""
    return create_optimization_value(
        "CandidateScore",
        candidate_hash=candidate,
        objective="net_pnl",
        direction="maximize",
        value=value,
        available=True,
        trade_count=trades,
        metrics={"net_pnl": value},
    )


def performance_report() -> object:
    """Build measured Analytics evidence from an explicit closed trade."""
    source = {
        "contract_version": "v1",
        "schema_id": "simulation.result.v1",
        "source_id": "observed-simulation-run",
        "phase": "backtest",
        "window_start": NOW,
        "window_end": NOW + timedelta(hours=1),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "symbols": ("EURUSD",),
        "timeframe": "M1",
        "closed_trades": (
            {
                "ticket": "ticket-1",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": Decimal(1),
                "entry_time": NOW,
                "entry_price": Decimal("1.10"),
                "stop_loss": Decimal("1.09"),
                "take_profit": Decimal("1.12"),
                "exit_time": NOW + timedelta(minutes=1),
                "exit_price": Decimal("1.11"),
                "comment": "closed",
                "commission": Decimal(-1),
                "swap": Decimal(0),
                "profit": Decimal(10),
                "magic": "strategy-1",
                "mae": Decimal(-2),
                "mfe": Decimal(12),
            },
        ),
        "quality_metadata": {},
        "source_metadata": {"evidence": "explicit-observed-trade"},
    }
    response = build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        created_at=NOW + timedelta(hours=1),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=analytics_config(),
    )
    if response.status != "success" or response.data is None:
        raise RuntimeError(f"Analytics rejected usage evidence: {response.error}")
    return response.data


def genuine_execution_bundle() -> tuple[object, object, object]:
    """Build genuine MT5 evidence and the real Simulator/Analytics adapter."""
    dataset = live_tick_dataset()
    simulation_request = backtest_request(dataset)
    root = Path(_STATE.name)
    adapter = build_simulation_analytics_backtest_adapter(
        auth_context=authority(simulation_request),
        simulation_dependencies=dependencies(root, dataset),
        analytics_config=analytics_config(),
        engine_type="event_driven",
        engine_version="v1",
    )
    return dataset, execution_request(dataset), adapter


def genuine_search_summary() -> tuple[object, object]:
    """Run a bounded search against genuine MT5/Simulator/Analytics evidence."""
    dataset, _, adapter = genuine_execution_bundle()
    request = search_request(
        dataset,
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
    )
    return run_bounded_search(request, adapter), adapter


def evidence_request(search: object | None = None) -> object:
    """Build evidence assembly input from a completed genuine search."""
    summary = genuine_search_summary()[0] if search is None else search
    return create_optimization_value(
        "EvidenceAssemblyRequest",
        search=summary,
        chart_data={
            "objective": [
                candidate.score.value
                for candidate in summary.candidates
                if candidate.score is not None
            ]
        },
        audit_references=(f"audit:{summary.search_id}",),
    )


class SqliteOptimizationStore:
    """Small durable SQLite implementation of the documented state port."""

    def __init__(self) -> None:
        """Create an isolated durable usage database."""
        self.path = Path(_STATE.name) / "optimization-usage.db"
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS state "
                "(kind TEXT, search_id TEXT PRIMARY KEY, payload TEXT)"
            )
            connection.commit()
        finally:
            connection.close()

    def save_checkpoint(self, value: object) -> object:
        """Persist one checkpoint transactionally."""
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "INSERT OR REPLACE INTO state VALUES (?, ?, ?)",
                ("checkpoint", value.search_id, canonical_json(value.model_dump())),
            )
            connection.commit()
        finally:
            connection.close()
        return create_optimization_value(
            "OptimizationPersistenceReceipt",
            search_id=value.search_id,
            reproducibility_hash=value.reproducibility_hash,
            stored_at=NOW,
            durable=True,
        )

    def load_checkpoint(self, search_id: str) -> object | None:
        """Load one checkpoint from SQLite."""
        connection = sqlite3.connect(self.path)
        try:
            row = connection.execute(
                "SELECT payload FROM state WHERE kind = ? AND search_id = ?",
                ("checkpoint", search_id),
            ).fetchone()
        finally:
            connection.close()
        return (
            create_optimization_value("OptimizationCheckpoint", **json.loads(row[0]))
            if row
            else None
        )

    def save_result(
        self, result: object, ranked_candidates: tuple[Mapping[str, object], ...]
    ) -> object:
        """Persist one result and verify its ranked evidence."""
        if ranked_candidates != result.ranked_candidates:
            raise ValueError("ranked evidence does not match result")
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "INSERT OR REPLACE INTO state VALUES (?, ?, ?)",
                ("result", result.search_id, canonical_json(result.model_dump())),
            )
            connection.commit()
        finally:
            connection.close()
        return create_optimization_value(
            "OptimizationPersistenceReceipt",
            search_id=result.search_id,
            reproducibility_hash=result.reproducibility_hash,
            stored_at=NOW,
            durable=True,
        )


def checkpoint() -> object:
    """Build one versioned checkpoint through the public boundary."""
    return create_optimization_value(
        "OptimizationCheckpoint",
        search_id="search-one",
        reproducibility_hash="a" * 64,
        completed_candidate_position=2,
        rng_state={"seed": 7},
        evidence_references=("candidate-2",),
        created_at=NOW,
    )


def optimization_result() -> object:
    """Return versioned evidence built from a genuine search."""
    return build_optimization_evidence(evidence_request())
