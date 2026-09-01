"""SQLite integration evidence for effective-dated provider history."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_digest
from app.services.data import (
    build_data_settings,
    data_settings_context,
    get_provider_specification_revision,
    get_provider_specification_revisions,
    register_provider_specification_revision,
    run_data_migrations,
    unwrap_data_response,
)

_FIRST = datetime(2026, 8, 15, 10, tzinfo=UTC)


def _snapshot(observed_at: datetime, revision: str) -> dict[str, object]:
    """Return one bounded checksummed snapshot mapping."""
    payload: dict[str, object] = {
        "broker": "mt5",
        "server": "demo-server",
        "environment": "demo",
        "account_digest": "a" * 64,
        "provider_symbol": "EURUSD",
        "terminal_build": "5000",
        "source_revision": revision,
        "observed_at": observed_at.isoformat(),
        "retrieval_provenance": "sanitized-demo-fixture",
    }
    payload["checksum"] = canonical_digest(payload)
    return payload


@pytest.fixture
def history(tmp_path: Path):
    """Yield one migrated isolated Data store."""
    settings = build_data_settings(
        database_url="sqlite:///provider-history.sqlite3",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=0.1,
        write_lock_lease_seconds=30,
    )
    with data_settings_context(settings):
        request_id = generate_id("req")
        response = run_data_migrations(request_id)
        unwrap_data_response(
            response,
            operation="test.provider_history.migrate",
            request_id=request_id,
        )
        yield


def _identity(request_id: str) -> dict[str, object]:
    """Return exact identity query keywords."""
    return {
        "provider": "mt5",
        "server": "demo-server",
        "environment": "demo",
        "account_digest": "a" * 64,
        "symbol": "EURUSD",
        "request_id": request_id,
    }


def test_fr_data_215_successor_closes_prior_interval_atomically(history: None) -> None:
    """FR-DATA-215 creates adjacent non-overlapping revisions."""
    request_id = generate_id("req")
    second = _FIRST + timedelta(hours=1)
    first_result = register_provider_specification_revision(
        _snapshot(_FIRST, "r1"), request_id=request_id
    )
    second_result = register_provider_specification_revision(
        _snapshot(second, "r2"), request_id=request_id
    )
    interval = get_provider_specification_revisions(
        **_identity(request_id),
        interval_start=_FIRST,
        interval_end=second + timedelta(hours=1),
    )
    assert interval["complete_coverage"] is True
    revisions = interval["revisions"]
    assert len(revisions) == 2
    assert revisions[0]["effective_to"] == second.isoformat()
    assert second_result["supersedes_revision_id"] == first_result["revision_id"]


def test_as_of_requires_complete_effective_coverage(history: None) -> None:
    """Standing guard: an uncovered instant fails rather than using nearest data."""
    request_id = generate_id("req")
    register_provider_specification_revision(
        _snapshot(_FIRST, "r1"), request_id=request_id
    )
    with pytest.raises(Exception, match="DATA_NOT_FOUND"):
        get_provider_specification_revision(
            **_identity(request_id), as_of=_FIRST - timedelta(microseconds=1)
        )


def test_fr_data_214_repeated_identical_registration_is_idempotent(
    history: None,
) -> None:
    """FR-DATA-214 returns the immutable row for exact repeated evidence."""
    request_id = generate_id("req")
    snapshot = _snapshot(_FIRST, "r1")
    first = register_provider_specification_revision(snapshot, request_id=request_id)
    repeated = register_provider_specification_revision(snapshot, request_id=request_id)
    assert repeated == first
