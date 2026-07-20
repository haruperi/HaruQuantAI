from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.data.storage import persist_audit_event
from app.services.data.storage.migrations import run_data_migrations
from app.utils import (
    AuditEvent,
    canonical_json,
    generate_id,
    redact_mapping_value,
)


def test_redacted_canonical_audit_event_reaches_data_persistence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Persist one genuinely redacted Utils audit envelope through Data."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///utils-audit.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10")
    migration_request_id = generate_id("req")
    run_data_migrations(migration_request_id)
    safe_payload = redact_mapping_value({"account": "demo", "token": "abc123"}).value
    assert isinstance(safe_payload, dict)
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=datetime.now(UTC),
        domain="trading",
        action="request_received",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload=safe_payload,
    )
    serialized = canonical_json(event.payload)
    assert "abc123" not in serialized
    assert "[REDACTED]" in serialized
    result = persist_audit_event(event)
    assert result.persisted
    assert result.event_id == event.event_id
