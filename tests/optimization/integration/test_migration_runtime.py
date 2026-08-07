# ruff: noqa: INP001 - standalone integration namespace by repository policy.
"""Integration evidence for authoritative Optimization migration execution."""

from pathlib import Path

import pytest
from app.services.optimization import run_optimization_migrations


def _configure(monkeypatch: pytest.MonkeyPatch, data_directory: Path) -> None:
    """Configure one isolated non-production SQLite database."""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///optimization.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def test_complete_manifest_applies_and_then_skips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply the checksummed manifest once and verify ledger idempotency."""
    _configure(monkeypatch, tmp_path)
    first = run_optimization_migrations("req-11111111-1111-4111-8111-111111111111")
    second = run_optimization_migrations("req-22222222-2222-4222-8222-222222222222")
    assert first.status == "success"
    assert first.data.applied_ids == ("001_optimization_schema_v1",)
    assert second.status == "success"
    assert second.data.skipped_ids == ("001_optimization_schema_v1",)
