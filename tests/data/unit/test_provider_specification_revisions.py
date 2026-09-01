"""Unit evidence for immutable provider-specification revisions."""

from datetime import UTC, datetime, timedelta

import pytest
from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_digest
from app.services.data import (
    get_provider_specification_revision,
    register_provider_specification_revision,
    run_data_migrations,
)
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.datasets.migrations import (
    PROVIDER_SPECIFICATION_MIGRATION_STEP,
)

_OBSERVED = datetime(2026, 8, 15, 10, tzinfo=UTC)


def _snapshot(*, revision: str = "provider-r1") -> dict[str, object]:
    """Return one bounded canonical snapshot mapping."""
    payload: dict[str, object] = {
        "broker": "mt5",
        "server": "demo-server",
        "environment": "demo",
        "account_digest": "a" * 64,
        "provider_symbol": "EURUSD",
        "terminal_build": "5000",
        "source_revision": revision,
        "observed_at": _OBSERVED.isoformat(),
        "retrieval_provenance": "sanitized-demo-fixture",
    }
    payload["checksum"] = canonical_digest(payload)
    return payload


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    """Configure and migrate one isolated Data database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///provider-history.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    request_id = generate_id("req")
    response = run_data_migrations(request_id)
    unwrap_data_response(
        response,
        operation="test.provider_history.migrate",
        request_id=request_id,
    )


def test_fr_data_214_migration_and_checksum_are_immutable() -> None:
    """FR-DATA-214 owns one checksummed immutable migration step."""
    step = PROVIDER_SPECIFICATION_MIGRATION_STEP
    assert step.migration_id == "010_provider_specification_revisions"
    assert len(step.checksum) == 64
    assert "data_provider_specification_revisions" in "\n".join(step.statements)


def test_fr_data_214_rejects_snapshot_checksum_tampering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """FR-DATA-214 rejects changed payload under an old checksum."""
    _configure(monkeypatch, tmp_path)
    snapshot = _snapshot()
    snapshot["server"] = "tampered"
    with pytest.raises(DataError, match="DATA_QUALITY_FAILED"):
        register_provider_specification_revision(
            snapshot, request_id=generate_id("req")
        )


def test_fr_data_215_requires_provenance_for_pre_observation_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """FR-DATA-215 blocks unproved historical backdating."""
    _configure(monkeypatch, tmp_path)
    with pytest.raises(DataError, match="POLICY_BLOCKED"):
        register_provider_specification_revision(
            _snapshot(),
            effective_from=_OBSERVED - timedelta(days=1),
            request_id=generate_id("req"),
        )


def test_fr_data_216_as_of_returns_detached_coverage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """FR-DATA-216 returns exact point-in-time coverage."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    register_provider_specification_revision(_snapshot(), request_id=request_id)
    result = get_provider_specification_revision(
        provider="mt5",
        server="demo-server",
        environment="demo",
        account_digest="a" * 64,
        symbol="EURUSD",
        as_of=_OBSERVED,
        request_id=request_id,
    )
    assert result["complete_coverage"] is True
    assert result["snapshot_checksum"] == _snapshot()["checksum"]
