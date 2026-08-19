"""Registry coordination tests for the Simulation Workbench."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.api import register_api_user, run_api_migrations
from app.services.api.widgets.simulator.migrations import (
    get_simulation_workbench_migration_steps,
)
from app.services.api.widgets.simulator.persistence import (
    create_simulation_batch_item_records,
    create_simulation_batch_record,
    create_simulation_result_record,
    read_simulation_batch_items,
    read_simulation_result_record,
)
from app.services.api.widgets.simulator.registry import (
    SimulationWorkbenchConflictError,
    SimulationWorkbenchRegistry,
)
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
)
from app.utils import generate_id

_FIXED_DAYS = (1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6)


def _fixed_clock_factory():
    """Build one fresh deterministic UTC clock reading sequence."""
    calls: list[int] = [0]

    def _fixed_clock() -> datetime:
        """Advance one deterministic UTC reading per call."""
        day = _FIXED_DAYS[calls[0] % len(_FIXED_DAYS)]
        calls[0] += 1
        return datetime(2026, 3, day, 12, 0, 0, tzinfo=UTC)

    return _fixed_clock


def _settings(tmp_path: Path, db_name: str) -> object:
    """Build isolated Data settings for one test database."""
    return build_data_settings(
        database_url=f"sqlite:///{db_name}",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


@pytest.fixture(name="store")
def _store(tmp_path: Path):
    """Apply the complete API manifest plus the workbench migration."""
    with data_settings_context(_settings(tmp_path, "swb-registry.db")):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        partial = run_domain_migrations(
            build_migration_request(
                domain="api",
                steps=get_simulation_workbench_migration_steps(),
                request_id=generate_id("req"),
            )
        )
        assert partial.status == "success"
        yield


def _run_values(principal_id: str, run_id: str, status: str) -> dict[str, object]:
    """Build one catalogue run row in the given lifecycle status."""
    return {
        "run_id": run_id,
        "principal_id": principal_id,
        "origin_kind": "canonical_job",
        "origin_id": f"job-{run_id}",
        "job_id": f"job-{run_id}",
        "batch_id": None,
        "session_id": None,
        "strategy_id": "naive-ma-trend",
        "strategy_version": "v1",
        "strategy_label": "Naive MA Trend",
        "symbols": json.dumps(["EURUSD"]),
        "timeframe": "H1",
        "measurement_start": "2026-01-01T00:00:00Z",
        "measurement_end": "2026-02-01T00:00:00Z",
        "status": status,
        "result_ref": None,
        "report_id": None,
        "report_ref": None,
        "artifact_manifest_ref": f"{run_id}/manifest.json",
        "quality_status": None,
        "evidence_class": "canonical",
        "created_at": "2026-02-28T00:00:00Z",
        "completed_at": None,
        "name": None,
        "alias": None,
        "description": None,
        "tags": "[]",
        "run_reason": None,
        "archive_state": "active",
        "updated_at": "2026-02-28T00:00:00Z",
    }


def _batch(
    principal_id: str,
    batch_id: str,
    *,
    statuses: tuple[str, ...],
) -> None:
    """Create one owned batch with one item per declared status."""
    created = "2026-02-28T00:00:00Z"
    create_simulation_batch_record(
        {
            "batch_id": batch_id,
            "principal_id": principal_id,
            "status": "running",
            "concurrency": 2,
            "name": None,
            "total_count": len(statuses),
            "completed_count": 0,
            "failed_count": 0,
            "cancelled_count": 0,
            "finished_at": None,
            "created_at": created,
            "updated_at": created,
        },
        request_id=generate_id("req"),
    )
    create_simulation_batch_item_records(
        tuple(
            {
                "batch_id": batch_id,
                "position": position,
                "run_id": f"run-{batch_id}-{position}",
                "job_id": f"job-{position}",
                "status": status,
                "error": (
                    "BACKTEST_PROVIDER_CONNECTION_FAILED"
                    if status == "failed"
                    else None
                ),
                "created_at": created,
                "updated_at": created,
            }
            for position, status in enumerate(statuses)
        ),
        request_id=generate_id("req"),
    )


def test_completion_uses_the_fixed_clock_and_records_evidence(store) -> None:
    """Completion stamps the injected clock reading and evidence refs."""
    principal_id = register_principal("registry-clock")
    create_simulation_result_record(
        _run_values(principal_id, "run-clock", "running"),
        request_id=generate_id("req"),
    )
    attached: list[tuple[str, str]] = []

    def attach(run_id: str, report_json: str) -> None:
        attached.append((run_id, report_json))

    registry = SimulationWorkbenchRegistry(
        clock=_fixed_clock_factory(), attach_report=attach
    )
    row = registry.complete_run(
        "run-clock",
        principal_id,
        request_id=generate_id("req"),
        report_json='{"v": 1}',
        evidence={"report_id": "report-1", "report_ref": "run-clock/report.json"},
    )
    assert attached == [("run-clock", '{"v": 1}')]
    assert row["status"] == "completed"
    assert row["report_id"] == "report-1"
    assert row["completed_at"].startswith("2026-03-01")


def register_principal(username: str) -> str:
    """Register one bounded test account and return its principal id."""
    user = register_api_user(
        username=username,
        password="bounded registry password",  # pragma: allowlist secret
        request_id=generate_id("req"),
        tenant_or_environment="development",
        runtime_profile="simulation",
    )
    return user.user_id


def test_completion_conflicts_on_a_terminal_run(store) -> None:
    """A second completion of the same run fails with the conflict code."""
    principal_id = register_principal("registry-conflict")
    create_simulation_result_record(
        _run_values(principal_id, "run-conflict", "running"),
        request_id=generate_id("req"),
    )
    registry = SimulationWorkbenchRegistry(clock=_fixed_clock_factory())
    registry.complete_run("run-conflict", principal_id, request_id=generate_id("req"))
    with pytest.raises(
        SimulationWorkbenchConflictError, match="SIMULATION_RUN_NOT_ACTIVE"
    ):
        registry.complete_run(
            "run-conflict", principal_id, request_id=generate_id("req")
        )


def test_partial_failure_retry_targets_failed_items_only(store) -> None:
    """Retry requeues failed items and leaves completed items untouched."""
    principal_id = register_principal("registry-retry")
    _batch(principal_id, "batch-retry", statuses=("completed", "failed", "queued"))
    resubmitted: list[str] = []

    def resubmit(item: dict[str, object]) -> str:
        resubmitted.append(str(item["position"]))
        return f"job-retry-{item['position']}"

    registry = SimulationWorkbenchRegistry(clock=_fixed_clock_factory())
    result = registry.retry_failed_batch_items(
        "batch-retry",
        principal_id,
        request_id=generate_id("req"),
        resubmit=resubmit,
    )
    assert result["retried_items"] == 1
    assert len(resubmitted) == 1
    statuses = {
        item["position"]: item["status"]
        for item in read_simulation_batch_items(
            "batch-retry", principal_id, request_id=generate_id("req")
        )
    }
    assert statuses == {0: "completed", 1: "queued", 2: "queued"}


def test_cancellation_happens_once(store) -> None:
    """A second cancellation affects zero further items."""
    principal_id = register_principal("registry-cancel")
    _batch(principal_id, "batch-cancel", statuses=("queued", "queued"))
    registry = SimulationWorkbenchRegistry(clock=_fixed_clock_factory())
    first = registry.cancel_batch(
        "batch-cancel", principal_id, request_id=generate_id("req")
    )
    second = registry.cancel_batch(
        "batch-cancel", principal_id, request_id=generate_id("req")
    )
    assert first["cancelled_items"] == 2
    assert second["cancelled_items"] == 0


def test_ownership_is_enforced_for_batches_and_runs(store) -> None:
    """Foreign principals get conflicts and zero-row transitions."""
    owner = register_principal("registry-owner")
    intruder = register_principal("registry-intruder")
    create_simulation_result_record(
        _run_values(owner, "run-owned", "running"), request_id=generate_id("req")
    )
    _batch(owner, "batch-owned", statuses=("queued",))
    registry = SimulationWorkbenchRegistry(clock=_fixed_clock_factory())
    with pytest.raises(
        SimulationWorkbenchConflictError, match="SIMULATION_BATCH_NOT_FOUND"
    ):
        registry.cancel_batch("batch-owned", intruder, request_id=generate_id("req"))
    with pytest.raises(
        SimulationWorkbenchConflictError, match="SIMULATION_RUN_NOT_ACTIVE"
    ):
        registry.complete_run("run-owned", intruder, request_id=generate_id("req"))
    assert (
        registry.annotate_run(
            "run-owned",
            intruder,
            {"name": "stolen"},
            request_id=generate_id("req"),
        )
        == 0
    )
    assert (
        read_simulation_result_record(
            "run-owned", owner, request_id=generate_id("req")
        )[0]["status"]
        == "running"
    )


def test_archive_never_deletes_evidence(store) -> None:
    """Archiving flips metadata only; the row and its refs survive."""
    principal_id = register_principal("registry-archive")
    create_simulation_result_record(
        _run_values(principal_id, "run-archive", "running"),
        request_id=generate_id("req"),
    )
    registry = SimulationWorkbenchRegistry(clock=_fixed_clock_factory())
    assert (
        registry.archive_run("run-archive", principal_id, request_id=generate_id("req"))
        == 1
    )
    row = read_simulation_result_record(
        "run-archive", principal_id, request_id=generate_id("req")
    )[0]
    assert row["archive_state"] == "archived"
    assert row["artifact_manifest_ref"] == "run-archive/manifest.json"
