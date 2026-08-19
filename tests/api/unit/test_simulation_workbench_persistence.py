"""Catalogue persistence tests for the Simulation Workbench."""

from __future__ import annotations

import json
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
    create_simulation_session_record,
    read_simulation_batch_items,
    read_simulation_batch_record,
    read_simulation_result_record,
    read_simulation_results_page,
    read_simulation_session_record,
)
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
)
from app.utils import generate_id


def _settings(tmp_path: Path, db_name: str) -> object:
    """Build isolated Data settings for one test database."""
    return build_data_settings(
        database_url=f"sqlite:///{db_name}",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _register(username: str) -> str:
    """Register one bounded test account and return its principal id."""
    user = register_api_user(
        username=username,
        password="bounded catalogue password",  # pragma: allowlist secret
        request_id=generate_id("req"),
        tenant_or_environment="development",
        runtime_profile="simulation",
    )
    return user.user_id


def _result_values(
    principal_id: str, run_id: str, created_at: str
) -> dict[str, object]:
    """Build one exact catalogue result row mapping."""
    return {
        "run_id": run_id,
        "principal_id": principal_id,
        "origin_kind": "canonical_job",
        "origin_id": "job-1",
        "job_id": "job-1",
        "batch_id": None,
        "session_id": None,
        "strategy_id": "naive-ma-trend",
        "strategy_version": "v1",
        "strategy_label": "Naive MA Trend",
        "symbols": json.dumps(["EURUSD"]),
        "timeframe": "H1",
        "measurement_start": "2026-01-01T00:00:00Z",
        "measurement_end": "2026-02-01T00:00:00Z",
        "status": "completed",
        "result_ref": f"{run_id}/result.json",
        "report_id": "report-1",
        "report_ref": f"{run_id}/analytics-report.json",
        "artifact_manifest_ref": f"{run_id}/manifest.json",
        "quality_status": "pass",
        "evidence_class": "canonical",
        "created_at": created_at,
        "completed_at": created_at,
        "name": "Run One",
        "alias": None,
        "description": None,
        "tags": json.dumps(["baseline"]),
        "run_reason": None,
        "archive_state": "active",
        "updated_at": created_at,
    }


@pytest.fixture(name="store")
def _store(tmp_path: Path):
    """Apply the complete API manifest plus the workbench migration."""
    with data_settings_context(_settings(tmp_path, "sim-workbench.db")):
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


def test_create_and_read_one_catalogue_row(store) -> None:
    """A created row round-trips with its owner principal."""
    principal_id = _register("swb-create")
    values = _result_values(principal_id, "run-1", "2026-03-01T00:00:00Z")
    assert create_simulation_result_record(values, request_id=generate_id("req")) == 1
    rows = read_simulation_result_record(
        "run-1", principal_id, request_id=generate_id("req")
    )
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-1"
    assert rows[0]["evidence_class"] == "canonical"
    assert rows[0]["report_ref"] == "run-1/analytics-report.json"


def test_duplicate_identity_is_idempotent(store) -> None:
    """Re-inserting the same run identity is a no-op."""
    principal_id = _register("swb-dup")
    values = _result_values(principal_id, "run-1", "2026-03-01T00:00:00Z")
    request_id = generate_id("req")
    create_simulation_result_record(values, request_id=request_id)
    assert create_simulation_result_record(values, request_id=request_id) == 0
    rows = read_simulation_result_record(
        "run-1", principal_id, request_id=generate_id("req")
    )
    assert len(rows) == 1


def test_reads_are_principal_scoped(store) -> None:
    """A foreign principal never sees another principal's run."""
    owner = _register("swb-owner")
    intruder = _register("swb-intruder")
    create_simulation_result_record(
        _result_values(owner, "run-1", "2026-03-01T00:00:00Z"),
        request_id=generate_id("req"),
    )
    assert (
        read_simulation_result_record("run-1", intruder, request_id=generate_id("req"))
        == ()
    )
    assert (
        read_simulation_results_page(
            intruder, limit=50, offset=0, request_id=generate_id("req")
        )
        == ()
    )


def test_page_ordering_is_created_at_then_run_descending(store) -> None:
    """Pages descend by creation time with a stable run-id tiebreak."""
    principal_id = _register("swb-page")
    for index, (run, created) in enumerate(
        (
            ("run-a", "2026-03-01T00:00:00Z"),
            ("run-b", "2026-03-02T00:00:00Z"),
            ("run-c", "2026-03-02T00:00:00Z"),
        )
    ):
        create_simulation_result_record(
            _result_values(principal_id, run, created), request_id=generate_id("req")
        )
        del index
    page = read_simulation_results_page(
        principal_id, limit=2, offset=0, request_id=generate_id("req")
    )
    assert [row["run_id"] for row in page] == ["run-c", "run-b"]
    next_page = read_simulation_results_page(
        principal_id, limit=2, offset=2, request_id=generate_id("req")
    )
    assert [row["run_id"] for row in next_page] == ["run-a"]


def test_session_and_batch_round_trip(store) -> None:
    """Session, batch, and ordered batch-item rows round-trip."""
    principal_id = _register("swb-batch")
    created = "2026-03-01T00:00:00Z"
    create_simulation_result_record(
        _result_values(principal_id, "run-1", created), request_id=generate_id("req")
    )
    create_simulation_session_record(
        {
            "session_id": "session-1",
            "principal_id": principal_id,
            "run_id": "run-1",
            "mode": "practice",
            "evidence_class": "practice",
            "status": "active",
            "cursor": 10,
            "tick_count": 11,
            "completed": 0,
            "durable": 0,
            "state_hash": "a" * 64,
            "closed_at": None,
            "created_at": created,
            "updated_at": created,
        },
        request_id=generate_id("req"),
    )
    assert (
        len(
            read_simulation_session_record(
                "session-1", principal_id, request_id=generate_id("req")
            )
        )
        == 1
    )
    create_simulation_batch_record(
        {
            "batch_id": "batch-1",
            "principal_id": principal_id,
            "status": "running",
            "concurrency": 2,
            "name": "Batch One",
            "total_count": 2,
            "completed_count": 0,
            "failed_count": 0,
            "cancelled_count": 0,
            "finished_at": None,
            "created_at": created,
            "updated_at": created,
        },
        request_id=generate_id("req"),
    )
    rows = tuple(
        {
            "batch_id": "batch-1",
            "position": position,
            "run_id": f"run-{position}",
            "job_id": f"job-{position}",
            "status": "queued",
            "error": None,
            "created_at": created,
            "updated_at": created,
        }
        for position in range(2)
    )
    assert (
        create_simulation_batch_item_records(rows, request_id=generate_id("req")) == 2
    )
    batch = read_simulation_batch_record(
        "batch-1", principal_id, request_id=generate_id("req")
    )
    assert len(batch) == 1
    assert batch[0]["total_count"] == 2
    items = read_simulation_batch_items(
        "batch-1", principal_id, request_id=generate_id("req")
    )
    assert [item["position"] for item in items] == [0, 1]
