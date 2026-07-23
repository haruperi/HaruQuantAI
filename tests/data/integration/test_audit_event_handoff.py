"""Data-owned persistence handoff for the Utils `AuditEvent v1` envelope.

This covers step 5 of `WF-UTL-003`: Data persists a redacted Utils-constructed
envelope through its own audit-storage boundary. The Utils-owned construction steps
are proven by `tests/utils/integration/test_audit_event_construction.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.data.audit import persist_audit_event
from app.services.data.persistence import run_data_migrations
from app.utils import AuditEvent, canonical_json, generate_id, redact_mapping_value


def test_persists_utils_audit_event_envelope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Persist one redacted Utils audit envelope through the Data boundary."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///utils-audit.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10")
    run_data_migrations(generate_id("req"))
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
    assert "abc123" not in canonical_json(event.payload)
    result = persist_audit_event(event)
    assert result.persisted
    assert result.event_id == event.event_id
