"""Unit tests for the 002_economic_events additive migration step (FR-DATA-128)."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.migrations import (
    DATA_MIGRATION_STEPS,
    run_data_migrations,
    run_domain_migrations,
)
from app.services.data.persistence.transactions import execute_transaction
from app.utils import generate_id


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Configure one isolated database for migration runs."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///economic_migration.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return tmp_path / "economic_migration.sqlite3"


def _table_exists(name: str, request_id: str) -> bool:
    """Return True when a named table exists on the configured database."""
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    result = _unwrap(
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(sql,),
                    parameter_sets=((name,),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )
    )
    return any(row.get("name") == name for row in result.rows)


def test_economic_events_step_is_additive_and_second() -> None:
    """002_economic_events is the second ordered canonical migration step."""
    ids = tuple(step.migration_id for step in DATA_MIGRATION_STEPS)
    assert ids == (
        "001_initial_data_schema",
        "002_economic_events",
        "003_research_sources",
        "004_research_source_providers",
    )


def test_run_data_migrations_creates_economic_events_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The canonical DATA migration runner creates ``data_economic_events``."""
    _configure(monkeypatch, tmp_path)

    _unwrap(run_data_migrations(generate_id("req")))

    request_id = generate_id("req")
    assert _table_exists("data_economic_events", request_id)


def test_run_data_migrations_is_idempotent_on_re_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A second run skips both steps and changes no state."""
    _configure(monkeypatch, tmp_path)

    first = _unwrap(run_data_migrations(generate_id("req")))
    second = _unwrap(run_data_migrations(generate_id("req")))

    expected_ids = (
        "001_initial_data_schema",
        "002_economic_events",
        "003_research_sources",
        "004_research_source_providers",
    )
    assert tuple(first.applied_ids) == expected_ids
    assert tuple(second.applied_ids) == ()
    assert tuple(second.skipped_ids) == expected_ids


def test_running_only_step_one_before_step_two_can_be_repaired_by_running_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Running step 001 alone first preserves deterministic checksums."""
    _configure(monkeypatch, tmp_path)
    step_one_only = (DATA_MIGRATION_STEPS[0],)
    run_domain_migrations_with_steps(step_one_only)
    _unwrap(run_data_migrations(generate_id("req")))


def run_domain_migrations_with_steps(steps: tuple[object, ...]) -> None:
    """Delegate wrapper kept here so the demo stays self-contained."""
    from app.services.data.persistence.contracts import MigrationRequest

    _unwrap(
        run_domain_migrations(
            MigrationRequest(
                domain="data",
                steps=tuple(steps),  # type: ignore[arg-type]
                request_id=generate_id("req"),
            )
        )
    )


def test_checksum_mismatch_on_economic_events_step_blocks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Modifying the applied 002 checksum fails migration invariance."""
    _configure(monkeypatch, tmp_path)

    _unwrap(run_data_migrations(generate_id("req")))

    from app.services.data.persistence.contracts import MigrationRequest, MigrationStep

    bad_step = MigrationStep(
        domain="data",
        migration_id="002_economic_events",
        checksum="tampered",
        statements=("SELECT 1",),
    )
    response = run_domain_migrations(
        MigrationRequest(
            domain="data",
            steps=(DATA_MIGRATION_STEPS[0], bad_step),
            request_id=generate_id("req"),
        )
    )
    assert response.status == "error"
    assert response.error is not None
