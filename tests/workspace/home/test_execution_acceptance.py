"""Actual catalog/backtest numerical acceptance.

Description:
    Uses isolated encoded market bars and independently calculated trades to
    verify reproducibility, optimization, cancellation and numerical rejection.
Purpose:
    FEAT-HOME-EXECUTION-ACCEPTANCE: Establish semantic execution evidence.
Key Capabilities:
    - FR-home-execution-evaluate: Verify actual trades and explicit evaluation logs.
    - FR-home-execution-finite: Verify rejected numerical output and warning logs.
Python API Usage:
    pytest tests/workspace/home/test_execution_acceptance.py
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_execution_acceptance.py --no-cov
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq
import pytest
from app.core.data.catalog import DataCatalog
from app.core.data.market_storage import encode_frame
from app.core.host.persistence import HostPersistence, SQLiteValue
from app.core.jobs.manager import JobCancelledError, JobContext
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.home.execution import ProjectExecutor


def market(root: Path, gateway: HostPersistence, final_close: float = 10.0) -> None:
    """Register actual encoded partitions, using four bars with +2 and -2 trades."""
    frame = pl.DataFrame(
        {
            "DateTime": [
                datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=i)
                for i in range(4)
            ],
            "Open": [10.0, 14.0, 10.0, max(12.0, final_close + 1)],
            "High": [12.0, 15.0, 13.0, max(13.0, final_close + 2)],
            "Low": [9.0, 12.0, 9.0, min(9.0, final_close - 1)],
            "Close": [11.0, 13.0, 12.0, final_close],
            "Volume": [1, 1, 1, 1],
        }
    )
    partition = root / "market.parquet"
    pq.write_table(encode_frame(frame.to_pandas(), "M1", 1.0), partition)
    row: dict[str, SQLiteValue] = {
        "id": "sample:TEST:M1",
        "source": "sample",
        "symbol": "TEST",
        "timeframe": "M1",
        "bars": 4,
        "underlying": "TEST",
        "broker": "Default",
        "timezone": "UTC",
        "category": "Forex",
        "date_from": "2026-01-01",
        "date_to": "2026-01-01",
        "created_at": "2026-01-01",
        "updated_at": "2026-01-01T01:00:00Z",
        "lineage_json": json.dumps({"partitions": [str(partition)], "tick_size": 1.0}),
    }
    existing = gateway.read_records("datamgr_datasets", filters={"id": row["id"]})
    if existing.get("data", {}).get("records"):
        response = gateway.update_record(
            "datamgr_datasets", row, filters={"id": row["id"]}
        )
    else:
        response = gateway.create_records("datamgr_datasets", row)
    assert response["success"]


def strategy_payload() -> dict[str, Any]:
    """Enter above threshold and close on a bearish bar; no invented trade data."""
    return {
        "strategy_id": "known",
        "params": [{"name": "threshold", "value": 10.0}],
        "rules": [
            {
                "rule_id": "entry",
                "conditions": [
                    {"left": "close", "comparator": ">", "right": "threshold"}
                ],
                "actions": [{"kind": "enter", "volume": 1.0}],
            },
            {
                "rule_id": "exit",
                "conditions": [{"left": "close", "comparator": "<", "right": "open"}],
                "actions": [{"kind": "exit"}],
            },
        ],
    }


def project(mode: str = "RETEST", **patch: Any) -> ProjectDocument:
    config = {
        "dataset": {"symbol": "TEST", "source": "sample", "timeframe": "M1"},
        "mode": mode,
        "seed": 42,
        "model": {
            "initial_capital": 100,
            "pip_size": 1,
            "economics": {
                "pip_size": 0.0001,
                "tick_size": 0.00001,
                "pip_value_per_lot": 0.0001,
                "contract_size": 1,
                "min_volume": 0.01,
                "max_volume": 100,
                "volume_step": 0.01,
            },
        },
        "strategy_result_ids": ["source"] if mode != "RANDOM" else [],
        **patch,
    }
    task_type = {"RETEST": "retest", "RANDOM": "build", "GRID": "optimize"}[mode]
    return ProjectDocument(
        ProjectManifest("project", "Project"),
        databanks={"Results": "bank"},
        tasks={
            "task": TaskDocument(
                "task", task_type, {"execution": config}, databank_target="bank"
            )
        },
        metadata={"revision": 1},
    )


@pytest.fixture
def execution(tmp_path: Path) -> tuple[ProjectExecutor, HostPersistence, ResultStore]:
    """Use one temporary gateway for all catalog and result capabilities."""
    (tmp_path / "test.db").touch()
    gateway = HostPersistence(tmp_path / "test.db")
    gateway.ensure_datasets_schema()
    results = ResultStore(gateway)
    market(tmp_path, gateway)
    results.save_result(
        "bank",
        RunResult(
            "source", "bank", "known", "Known", strategy_payload=strategy_payload()
        ),
    )
    return ProjectExecutor(DataCatalog(gateway), results), gateway, results


def context(root: Path, identity: str) -> JobContext:
    return JobContext(identity, root / identity, min_available_ram_pct=0)


def test_retest_actual_trades_and_repeat_preservation(
    execution: Any, tmp_path: Path, caplog: Any
) -> None:
    executor, gateway, results = execution
    snapshot = executor.prepare(project(), "task", 1)
    with caplog.at_level("INFO"):
        receipt = executor.run(context(tmp_path, "run-one"), snapshot)
    stored = results.get_result(receipt["result_ids"][0])
    assert [trade["net_pnl"] for trade in stored.trades] == [2.0, -2.0]
    assert stored.metrics["net_profit"] == 0
    assert len(stored.equity_curve) == 4
    assert len(stored.mae_mfe) == 2
    assert stored.strategy_payload["strategy_id"] == "known"
    assert (
        stored.parameters["execution"]["dataset"]["revision"] == "2026-01-01T01:00:00Z"
    )
    assert "net_profit_is" not in stored.metrics
    assert "FR-home-execution-evaluate" in caplog.text
    second = executor.run(context(tmp_path, "run-two"), snapshot)
    assert second["result_ids"] != receipt["result_ids"]
    assert len(results.list_results("bank")) == 3
    market(tmp_path, gateway, final_close=9.0)
    # Previously captured bars remain unchanged even when the source partition changes.
    assert executor.run(context(tmp_path, "snapshot"), snapshot)["best_fitness"] == 0
    changed = executor.prepare(project(), "task", 1)
    assert executor.run(context(tmp_path, "changed"), changed)["best_fitness"] == -1


def test_grid_selects_independently_expected_parameters(
    execution: Any, tmp_path: Path
) -> None:
    executor, _, results = execution
    document = project(
        "GRID",
        parameter_ranges=[{"name": "threshold", "start": 10, "end": 12, "step": 1}],
    )
    receipt = executor.run(
        context(tmp_path, "grid"), executor.prepare(document, "task", 1)
    )
    assert receipt["candidates_evaluated"] == 3
    assert receipt["best_parameters"] == {"threshold": 10.0}
    assert receipt["best_fitness"] == 0
    assert [
        results.get_result(key).metrics["net_profit"] for key in receipt["result_ids"]
    ] == [0, -3, -3]


def test_random_builder_evaluates_real_bars(execution: Any, tmp_path: Path) -> None:
    executor, _, results = execution
    receipt = executor.run(
        context(tmp_path, "build"),
        executor.prepare(project("RANDOM", candidates=3), "task", 1),
    )
    assert receipt["candidates_evaluated"] == 3
    assert receipt["candidates_accepted"] + receipt["candidates_rejected"] == 3
    for key in receipt["result_ids"]:
        result = results.get_result(key)
        assert len(result.equity_curve) == 4
        assert result.metrics["net_profit"] == sum(t["net_pnl"] for t in result.trades)


def test_nonfinite_policy_rejects_without_writes(
    execution: Any, tmp_path: Path, caplog: Any
) -> None:
    executor, gateway, results = execution
    market(tmp_path, gateway, final_close=14.0)
    with caplog.at_level("WARNING"):
        receipt = executor.run(
            context(tmp_path, "nonfinite"), executor.prepare(project(), "task", 1)
        )
    assert receipt["candidates_rejected"] == 1
    assert receipt["result_ids"] == []
    assert len(results.list_results("bank")) == 1
    assert "FR-home-execution-finite" in caplog.text


@pytest.mark.parametrize(
    "task,revision,code",
    [
        (None, 1, "TASK_NOT_FOUND"),
        ("unknown", 1, "TASK_NOT_FOUND"),
        ("task", None, "CONFLICT"),
        ("task", True, "CONFLICT"),
        ("task", 2, "CONFLICT"),
    ],
)
def test_preflight_fails_before_writes(
    execution: Any, task: Any, revision: Any, code: str
) -> None:
    executor, _, results = execution
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(), task, revision)
    assert caught.value.code == code
    assert len(results.list_results("bank")) == 1


def test_cancellation_prevents_result_commit(execution: Any, tmp_path: Path) -> None:
    executor, _, results = execution
    job = context(tmp_path, "cancel")
    job.cancel()
    with pytest.raises(JobCancelledError):
        executor.run(job, executor.prepare(project(), "task", 1))
    assert len(results.list_results("bank")) == 1


@pytest.mark.parametrize(
    "patch",
    [
        {"model": {"initial_capital": 0}},
        {"model": {"point_value": 0}},
        {"model": {"pip_size": 0}},
        {"model": {"initial_capital": float("nan")}},
        {"model": {"commission_per_order": -1}},
        {"model": {"slippage_points": -1}},
        {"model": {"precision_mode": "TICK"}},
        {"strategy_result_ids": []},
        {"dataset": {"symbol": "TEST", "source": "sample", "timeframe": "bad"}},
        {
            "dataset": {
                "symbol": "TEST",
                "source": "sample",
                "timeframe": "M1",
                "start": 10,
                "end": 9,
            }
        },
    ],
)
def test_invalid_saved_settings_never_create_results(
    execution: Any, patch: dict[str, Any]
) -> None:
    """Unsupported models and malformed saved settings fail before any write."""
    executor, _, results = execution
    before = results.get_result("source").to_dict()
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(**patch), "task", 1)
    assert caught.value.code == "INVALID_EXECUTION_SETTINGS"
    assert [item.result_id for item in results.list_results("bank")] == ["source"]
    assert results.get_result("source").to_dict() == before


@pytest.mark.parametrize(
    "task_patch,code",
    [
        ({"enabled": False}, "TASK_NOT_FOUND"),
        ({"task_id": "different"}, "TASK_NOT_FOUND"),
        ({"task_type": "unavailable"}, "UNSUPPORTED_TASK"),
        ({"task_type": "build"}, "UNSUPPORTED_MODE"),
        ({"databank_target": "foreign"}, "DATABANK_NOT_FOUND"),
    ],
)
def test_native_task_authority_rejected_before_execution(
    execution: Any, task_patch: dict[str, Any], code: str
) -> None:
    """Disabled, mismatched and foreign native tasks cannot submit research."""
    executor, _, results = execution
    document = project()
    document = replace(
        document, tasks={"task": replace(document.tasks["task"], **task_patch)}
    )
    with pytest.raises(DomainError) as caught:
        executor.prepare(document, "task", 1)
    assert caught.value.code == code
    assert len(results.list_results("bank")) == 1


@pytest.mark.parametrize(
    "dataset_patch,code",
    [
        ({"symbol": "MISSING"}, "DATASET_NOT_FOUND"),
        ({"source": "missing"}, "DATASET_NOT_FOUND"),
        ({"revision": "obsolete"}, "STALE_CATALOG_REVISION"),
    ],
)
def test_missing_or_stale_catalog_authority_preserves_results(
    execution: Any, dataset_patch: dict[str, Any], code: str
) -> None:
    """A real catalog must resolve the saved dataset and pinned revision."""
    executor, _, results = execution
    dataset = {"symbol": "TEST", "source": "sample", "timeframe": "M1"}
    dataset.update(dataset_patch)
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(dataset=dataset), "task", 1)
    assert caught.value.code == code
    assert len(results.list_results("bank")) == 1


@pytest.mark.parametrize("boundary", [1767225600, 1767225780])
def test_sample_boundary_must_be_inside_actual_market(
    execution: Any, boundary: int
) -> None:
    """Both endpoint dates are rejected rather than inventing sample metrics."""
    executor, _, results = execution
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(split_time=boundary), "task", 1)
    assert caught.value.code == "INVALID_SAMPLE_BOUNDARY"
    assert len(results.list_results("bank")) == 1


@pytest.mark.parametrize(
    "bank,payload,code",
    [
        ("foreign", None, "STRATEGY_NOT_OWNED"),
        ("bank", {}, "INVALID_STRATEGY"),
        ("bank", {"strategy_id": "other", "rules": []}, "INVALID_STRATEGY"),
    ],
)
def test_unowned_or_invalid_stored_strategy_is_not_executed(
    execution: Any, bank: str, payload: dict[str, Any] | None, code: str
) -> None:
    """Stored identifiers cannot substitute for valid owned strategy definitions."""
    executor, _, results = execution
    selected = RunResult(
        "selected",
        bank,
        "known",
        "Selected",
        strategy_payload=strategy_payload() if payload is None else payload,
    )
    results.save_result(bank, selected)
    before = results.get_result("selected").to_dict()
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(strategy_result_ids=["selected"]), "task", 1)
    assert caught.value.code == code
    assert results.get_result("selected").to_dict() == before
    assert len(results.list_results("bank")) == (2 if bank == "bank" else 1)


def test_fixed_sizing_changes_actual_trade_volume_and_pnl(
    execution: Any, tmp_path: Path
) -> None:
    """Existing fixed sizing doubles both independently known trade profits."""
    executor, _, results = execution
    document = project(money_management={"method": "FixedSize", "size": 2})
    receipt = executor.run(
        context(tmp_path, "sized"), executor.prepare(document, "task", 1)
    )
    stored = results.get_result(receipt["result_ids"][0])
    assert [trade["net_pnl"] for trade in stored.trades] == [4, -4]
    assert stored.metrics["net_profit"] == 0
    assert stored.parameters["execution"]["money_management"]["size"] == 2


def test_rounding_position_to_zero_does_not_write_results(
    execution: Any, tmp_path: Path
) -> None:
    """Positive input sizing still fails closed if configured rounding erases it."""
    executor, _, results = execution
    document = project(money_management={"size": 0.001, "decimals": 0})
    with pytest.raises(DomainError) as caught:
        executor.run(
            context(tmp_path, "rounded"), executor.prepare(document, "task", 1)
        )
    assert caught.value.code == "INVALID_POSITION_SIZE"
    assert len(results.list_results("bank")) == 1


@pytest.mark.parametrize(
    "ranges",
    [
        [],
        [{"name": "threshold", "start": 2, "end": 1, "step": 1}],
        [{"name": "threshold", "start": 1, "end": 2, "step": 0}],
        [{"name": "threshold", "start": 0, "end": 10000, "step": 1}],
        [
            {"name": "threshold", "start": 1, "end": 2, "step": 1},
            {"name": "threshold", "start": 1, "end": 2, "step": 1},
        ],
        [
            {"name": "threshold", "start": 0, "end": 100, "step": 1},
            {"name": "other", "start": 0, "end": 100, "step": 1},
        ],
    ],
)
def test_invalid_or_unbounded_grids_fail_before_evaluation(
    execution: Any, ranges: list[dict[str, Any]]
) -> None:
    """Reversed, duplicate and excessive grids cannot create a research job."""
    executor, _, results = execution
    with pytest.raises(DomainError) as caught:
        executor.prepare(project("GRID", parameter_ranges=ranges), "task", 1)
    assert caught.value.code == "INVALID_EXECUTION_SETTINGS"
    assert len(results.list_results("bank")) == 1


def test_grid_requires_parameter_from_the_selected_strategy(execution: Any) -> None:
    """A valid numeric range cannot target an invented strategy parameter."""
    executor, _, results = execution
    with pytest.raises(DomainError) as caught:
        executor.prepare(
            project(
                "GRID",
                parameter_ranges=[{"name": "missing", "start": 1, "end": 2, "step": 1}],
            ),
            "task",
            1,
        )
    assert caught.value.code == "INVALID_PARAMETER"
    assert len(results.list_results("bank")) == 1


def test_missing_stored_strategy_is_not_replaced_with_generated_data(
    execution: Any,
) -> None:
    """A deleted selection is an error and never silently generates a substitute."""
    executor, _, results = execution
    with pytest.raises(DomainError) as caught:
        executor.prepare(project(strategy_result_ids=["deleted"]), "task", 1)
    assert caught.value.code == "RESULT_NOT_FOUND"
    assert len(results.list_results("bank")) == 1


def test_hsl_optimization_recompiles_typed_parameters_and_sizing() -> None:
    """Grid values and sizing overrides change the canonical executable definition."""
    from app.core.trading.strategy.hsl.compiler import StrategyCompiler
    from app.core.trading.strategy.hsl.documents import parse_hsl_document
    from app.core.trading.strategy.hsl.models import HSLStrategyDocument

    document = HSLStrategyDocument.model_validate(
        {
            "strategy": {
                "id": "grid",
                "name": "Grid",
                "parameters": {
                    "period": {"type": "int", "default": 2, "min": 2, "max": 10}
                },
                "rules": [
                    {
                        "id": "entry",
                        "when": {"type": "state", "state": "always_true"},
                        "then": [{"action": "enter_market", "side": "long"}],
                    }
                ],
            }
        }
    )
    original = StrategyCompiler().compile_to_runtime(document)
    candidate = ProjectExecutor._parameter_candidate(original, {"period": 4.0})
    assert candidate.params[0].value == 4
    assert isinstance(candidate.params[0].value, int)
    assert candidate.hsl_json != original.hsl_json
    sized = ProjectExecutor._sized_candidate(candidate, 0.25)
    restored = parse_hsl_document(sized.hsl_json or "")
    assert restored.strategy.money_management.size.value == 0.25
    assert restored.strategy.rules[0].then[0].size.value == 0.25
