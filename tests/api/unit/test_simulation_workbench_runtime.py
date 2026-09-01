"""Runtime composition tests for the Simulation Workbench (FEAT-API-27).

These cover the seams that used to fail closed: the catalogue completion
sink, bounded batch execution, canonical reproduction of a finalized
session, and the gateway-owned run provenance that links them.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.kernel.identity import generate_id
from app.services.api import register_api_user, run_api_migrations
from app.services.api.widgets.simulator.batching import (
    build_batch_runner,
)
from app.services.api.widgets.simulator.completion import (
    build_catalogue_completion_sink,
    build_catalogue_run_values,
)
from app.services.api.widgets.simulator.migrations import (
    get_simulation_workbench_migration_steps,
)
from app.services.api.widgets.simulator.persistence import (
    read_simulation_batch_items,
    read_simulation_batch_record,
    read_simulation_result_record,
)
from app.services.api.widgets.simulator.provenance import (
    RunProvenanceIndex,
)
from app.services.api.widgets.simulator.registry import (
    SimulationWorkbenchRegistry,
)
from app.services.api.widgets.simulator.reproduction import (
    build_reproduction_runner,
)
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
)

_PRINCIPAL = "user-workbench-runtime"
_NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


def _settings(tmp_path: Path, db_name: str) -> object:
    """Build isolated Data settings for one test database.

    Returns:
        Validated Data settings bound to a temporary database.
    """
    return build_data_settings(
        database_url=f"sqlite:///{db_name}",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


@pytest.fixture(name="runtime")
def _runtime(tmp_path: Path):
    """Return a factory re-entering the test database on worker threads.

    Returns:
        Callable producing the Data settings context for one thread.
    """
    settings = _settings(tmp_path, "swb-runtime.db")
    return lambda: data_settings_context(settings)


@pytest.fixture(name="principal")
def _principal(tmp_path: Path):
    """Apply the API manifest plus the workbench migration and one account.

    Yields:
        The registered principal identity owning every fixture resource.
    """
    with data_settings_context(_settings(tmp_path, "swb-runtime.db")):
        assert run_api_migrations(generate_id("req")).status == "success"
        assert (
            run_domain_migrations(
                build_migration_request(
                    domain="api",
                    steps=get_simulation_workbench_migration_steps(),
                    request_id=generate_id("req"),
                )
            ).status
            == "success"
        )
        register_api_user(
            username=_PRINCIPAL,
            password="bounded runtime password",  # pragma: allowlist secret
            request_id=generate_id("req"),
        )
        yield _PRINCIPAL


class _Report:
    """Minimal stand-in for a validated Analytics performance report."""

    report_id = "rep-1"


class _Evidence:
    """Minimal stand-in for one BacktestRunEvidence projection."""

    def __init__(self, run_id: str, job_id: str) -> None:
        """Build evidence for one finished canonical run."""
        self.projection: dict[str, Any] = {
            "run_id": run_id,
            "job_id": job_id,
            "principal_id": _PRINCIPAL,
            "strategy_id": "naive-ma-trend",
            "strategy_version": "v1",
            "strategy_label": "Naive MA Trend",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-02-01T00:00:00Z",
            "quality": {"status": "verified"},
        }
        self.simulation_result = {"schema_id": "simulation.result.v1"}
        self.performance_report = _Report()


def _sink(*, provenance=None):
    """Build one catalogue completion sink over fake attachment.

    Returns:
        The sink and the list recording each attachment call.
    """
    attached: list[tuple[str, str]] = []

    def attach(run_id: str, report_json: str, *, request_id: str) -> object:
        """Record one immutable attachment and return its owner projection."""
        del request_id
        attached.append((run_id, report_json))
        return {"artifact_ref": f"{run_id}/analytics-report.json"}

    sink = build_catalogue_completion_sink(
        SimulationWorkbenchRegistry(clock=lambda: _NOW),
        attach_report=attach,
        serializer=lambda _report: '{"report_id": "rep-1"}',
        clock=lambda: _NOW,
        provenance=provenance,
    )
    return sink, attached


def test_run_values_copy_owner_evidence_without_inventing_any() -> None:
    """Catalogue row values are copied from the owner projection only."""
    values = build_catalogue_run_values(
        _Evidence("run-1", "job-1").projection, created_at="2026-03-01T12:00:00Z"
    )
    assert values["origin_kind"] == "canonical_job"
    assert values["evidence_class"] == "canonical"
    assert values["job_id"] == "job-1"
    assert values["symbols"] == '["EURUSD"]'
    assert values["status"] == "queued"
    assert values["report_ref"] is None


def test_completion_sink_records_a_completed_catalogue_run(principal: str) -> None:
    """A finished canonical job lands as one completed catalogue row."""
    sink, attached = _sink()
    sink(_Evidence("run-sink", "job-sink"))
    rows = read_simulation_result_record(
        "run-sink", principal, request_id=generate_id("req")
    )
    assert len(rows) == 1
    assert rows[0]["status"] == "completed"
    assert rows[0]["report_ref"] == "run-sink/analytics-report.json"
    assert rows[0]["result_ref"] == "run-sink/result.json"
    assert rows[0]["quality_status"] == "verified"
    assert attached == [("run-sink", '{"report_id": "rep-1"}')]


def test_completion_sink_applies_recorded_gateway_provenance(principal: str) -> None:
    """A run the gateway started records why it exists."""
    index = RunProvenanceIndex()
    index.record("job-repro", {"origin_kind": "reproduction", "session_id": "sess-1"})
    sink, _ = _sink(provenance=index.resolve)
    sink(_Evidence("run-repro", "job-repro"))
    rows = read_simulation_result_record(
        "run-repro", principal, request_id=generate_id("req")
    )
    assert rows[0]["origin_kind"] == "reproduction"
    assert rows[0]["session_id"] == "sess-1"
    assert index.resolve("job-repro") == {}


def _run_source(outcomes: dict[str, str], *, submitted: list[object] | None = None):
    """Build a fake Simulator run dispatcher with fixed terminal outcomes.

    Returns:
        Callable accepting ``submit`` and ``get`` operations.
    """
    counter = [0]

    def source(operation: str, *args: object, **kwargs: object) -> object:
        """Dispatch one fake run operation."""
        del kwargs
        if operation == "submit":
            counter[0] += 1
            job_id = f"job-{counter[0]}"
            if submitted is not None:
                submitted.append(args[0])
            return {"job_id": job_id, "status": "queued"}
        if operation == "get":
            job_id = str(args[0])
            status = outcomes.get(job_id, "succeeded")
            return {
                "job_id": job_id,
                "status": status,
                "result": {"run_id": f"run-{job_id}"},
                "error": None if status == "succeeded" else "SIM_FAILED",
            }
        raise AssertionError(operation)

    return source


def _spec(symbol: str) -> dict[str, object]:
    """Build one batch run specification carrying its window.

    Returns:
        Plain JSON values for one batch item.
    """
    return {
        "symbol": symbol,
        "timeframe": "H1",
        "strategy_id": "naive-ma-trend",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-02-01T00:00:00Z",
        "parameters": {},
    }


def _await_terminal(batch_id: str, principal: str, *, total: int) -> None:
    """Wait until the batch itself recorded its terminal durable outcome.

    Raises:
        AssertionError: If the batch never finished within the bound.
    """
    deadline = threading.Event()
    for _ in range(200):
        items = read_simulation_batch_items(
            batch_id, principal, request_id=generate_id("req")
        )
        rows = read_simulation_batch_record(
            batch_id, principal, request_id=generate_id("req")
        )
        terminal = sum(
            1
            for item in items
            if item["status"] in {"completed", "failed", "cancelled"}
        )
        if terminal == total and rows and rows[0]["finished_at"]:
            return
        deadline.wait(0.05)
    raise AssertionError("batch never reached a terminal status")


def test_batch_executes_every_item_and_records_terminal_counts(
    principal: str, runtime: Any
) -> None:
    """A bounded batch runs each item and syncs its durable counts."""
    runner = build_batch_runner(
        _run_source({"job-2": "failed"}),
        poll_interval=0.01,
        runtime_context=runtime,
    )
    accepted: Any = runner(
        "create_batch",
        {"items": (_spec("EURUSD"), _spec("GBPUSD")), "concurrency": 2},
        principal_id=principal,
        request_id=generate_id("req"),
    )
    batch_id = str(accepted["batch"]["batch_id"])
    assert accepted["batch"]["total_count"] == 2
    _await_terminal(batch_id, principal, total=2)
    rows = read_simulation_batch_record(
        batch_id, principal, request_id=generate_id("req")
    )
    assert rows[0]["status"] == "failed"
    assert rows[0]["completed_count"] == 1
    assert rows[0]["failed_count"] == 1
    assert rows[0]["finished_at"]


def test_batch_records_each_item_provenance(principal: str, runtime: Any) -> None:
    """Every batch item's job records the batch it belongs to."""
    index = RunProvenanceIndex()
    runner = build_batch_runner(
        _run_source({}),
        poll_interval=0.01,
        provenance=index.record,
        runtime_context=runtime,
    )
    accepted: Any = runner(
        "create_batch",
        {"items": (_spec("EURUSD"),), "concurrency": 1},
        principal_id=principal,
        request_id=generate_id("req"),
    )
    batch_id = str(accepted["batch"]["batch_id"])
    _await_terminal(batch_id, principal, total=1)
    origin = index.resolve("job-1")
    assert origin == {"origin_kind": "batch", "batch_id": batch_id}


def test_batch_admission_bounds_fail_closed(principal: str) -> None:
    """An empty batch or an out-of-range concurrency is refused."""
    runner = build_batch_runner(_run_source({}), poll_interval=0.01)
    with pytest.raises(ValueError, match="SIMULATION_BATCH_SIZE_INVALID"):
        runner(
            "create_batch",
            {"items": ()},
            principal_id=principal,
            request_id=generate_id("req"),
        )
    with pytest.raises(ValueError, match="SIMULATION_BATCH_CONCURRENCY_INVALID"):
        runner(
            "create_batch",
            {"items": (_spec("EURUSD"),), "concurrency": 99},
            principal_id=principal,
            request_id=generate_id("req"),
        )


def test_batch_stream_returns_ordered_items_from_the_cursor(principal: str) -> None:
    """Streaming reads durable rows from the requested position onward."""
    runner = build_batch_runner(_run_source({}), poll_interval=0.01)
    accepted: Any = runner(
        "create_batch",
        {"items": (_spec("EURUSD"), _spec("GBPUSD")), "concurrency": 1},
        principal_id=principal,
        request_id=generate_id("req"),
    )
    batch_id = str(accepted["batch"]["batch_id"])
    frame: Any = runner("stream_batch", batch_id, principal_id=principal, after=1)
    assert [item["position"] for item in frame["items"]] == [1]
    assert frame["after"] == 1


def test_reproduction_reexecutes_the_immutable_session_request() -> None:
    """Reproduction submits the session's exact request as a canonical job."""
    index = RunProvenanceIndex()
    submitted: list[object] = []
    runner = build_reproduction_runner(
        _run_source({}, submitted=submitted),
        session_request_reader=lambda _session_id: {
            "symbol": "EURUSD",
            "timeframe": "H1",
            "strategy_id": "naive-ma-trend",
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-02-01T00:00:00Z",
            "parameters": {},
            "initial_balance": "10000.00",
            "account_currency": "USD",
            "seed": 7,
        },
        provenance=index.record,
    )
    snapshot: Any = runner(
        {"session_id": "sess-1"}, principal_id=_PRINCIPAL, request_id="req-1"
    )
    assert snapshot["job_id"] == "job-1"
    assert submitted[0].symbol == "EURUSD"  # type: ignore[attr-defined]
    assert submitted[0].seed == 7  # type: ignore[attr-defined]
    assert index.resolve("job-1") == {
        "origin_kind": "reproduction",
        "session_id": "sess-1",
    }


def test_reproduction_without_a_durable_request_fails_closed() -> None:
    """A session holding no immutable request can never be reproduced."""
    runner = build_reproduction_runner(
        _run_source({}), session_request_reader=lambda _session_id: None
    )
    with pytest.raises(ValueError, match="SIMULATION_SESSION_NOT_REPRODUCIBLE"):
        runner({"session_id": "sess-1"}, principal_id=_PRINCIPAL)


def test_provenance_index_is_bounded() -> None:
    """The provenance index evicts its oldest entries under pressure."""
    index = RunProvenanceIndex(max_entries=2)
    index.record("job-1", {"origin_kind": "batch"})
    index.record("job-2", {"origin_kind": "batch"})
    index.record("job-3", {"origin_kind": "batch"})
    assert index.resolve("job-1") == {}
    assert index.resolve("job-3") == {"origin_kind": "batch"}


def test_catalogue_rows_cross_the_boundary_in_contract_shape() -> None:
    """Durable JSON text columns are published as the declared arrays."""
    from app.services.api.widgets.simulator.workbench_orchestration import (
        deserialize_json_list,
        project_catalogue_row,
    )

    row = project_catalogue_row(
        {"run_id": "run-1", "symbols": '["EURUSD", "GBPUSD"]', "tags": '["baseline"]'}
    )
    assert row["symbols"] == ("EURUSD", "GBPUSD")
    assert row["tags"] == ("baseline",)
    assert deserialize_json_list(None) == ()
    assert deserialize_json_list("not json") == ()
    assert deserialize_json_list('{"not": "a list"}') == ()
    assert deserialize_json_list(("EURUSD",)) == ("EURUSD",)


def test_failed_attachment_leaves_no_stranded_catalogue_row(principal: str) -> None:
    """A run whose report cannot be attached is never half-recorded."""

    def refuse(run_id: str, report_json: str, *, request_id: str) -> object:
        """Refuse the attachment the way an absent result artifact does."""
        del run_id, report_json, request_id
        raise RuntimeError("SIMULATION_RESULT_NOT_FOUND")

    sink = build_catalogue_completion_sink(
        SimulationWorkbenchRegistry(clock=lambda: _NOW),
        attach_report=refuse,
        serializer=lambda _report: '{"report_id": "rep-1"}',
        clock=lambda: _NOW,
    )
    with pytest.raises(RuntimeError, match="SIMULATION_RESULT_NOT_FOUND"):
        sink(_Evidence("run-stranded", "job-stranded"))
    assert (
        read_simulation_result_record(
            "run-stranded", principal, request_id=generate_id("req")
        )
        == ()
    )
