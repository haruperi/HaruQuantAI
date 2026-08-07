# ruff: noqa: INP001 - standalone integration namespace by repository policy.
"""Integration evidence for both Optimization-owned relational tables."""

from pathlib import Path

import pytest
from app.services.optimization import (
    build_optimization_evidence,
    create_optimization_state_store,
    load_optimization_result,
    load_search_checkpoint,
    persist_optimization_result,
    run_optimization_migrations,
    save_search_checkpoint,
)
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import checkpoint


def _configure(monkeypatch: pytest.MonkeyPatch, data_directory: Path) -> None:
    """Configure one isolated non-production SQLite database."""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///optimization.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def test_both_tables_reach_production_state_operations(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Persist and recover one checkpoint and result through public operations."""
    _configure(monkeypatch, tmp_path)
    assert (
        run_optimization_migrations("req-11111111-1111-4111-8111-111111111111").status
        == "success"
    )
    store = create_optimization_state_store(
        request_id="req-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )

    checkpoint_value = checkpoint()
    save_search_checkpoint(checkpoint_value, store)
    assert (
        load_search_checkpoint(
            search_id=checkpoint_value.search_id,
            reproducibility_hash=checkpoint_value.reproducibility_hash,
            store=store,
        )
        == checkpoint_value
    )

    result = build_optimization_evidence(evidence_request())
    persist_optimization_result(result, store)
    assert (
        load_optimization_result(
            search_id=result.search_id,
            reproducibility_hash=result.reproducibility_hash,
            store=store,
        )
        == result
    )
