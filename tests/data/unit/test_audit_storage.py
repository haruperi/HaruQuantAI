"""Unit tests for governed local audit event logging and queries."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from app.services.data.contracts import AuditEventQuery
from app.services.data.contracts.errors import DataError
from app.services.data.storage.audit import (
    persist_audit_event,
    query_audit_events,
)
from app.utils.contracts.auth import AuthContext

from tests.data.helpers import END, START, make_audit_event


def _configure_audit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Helper to configure database and data directories."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10")
    from app.services.data.storage.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )


def make_auth(*, admin: bool = True) -> AuthContext:
    """Helper to construct authenticated context."""
    from app.utils import generate_id

    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user-1",
        principal_type="USER",
        roles=("admin",) if admin else ("viewer",),
        permissions=() if admin else ("other.read",),
        scopes=("data:read",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=START,
    )


def test_persist_audit_event_idempotency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that audit events are persisted exactly once (idempotent write)."""
    _configure_audit(monkeypatch, tmp_path)

    event = make_audit_event()

    # First persist call -> new insert
    res1 = persist_audit_event(event)
    assert res1.persisted
    assert not res1.idempotent

    # Second persist call -> idempotent skip
    res2 = persist_audit_event(event)
    assert not res2.persisted
    assert res2.idempotent


def test_query_audit_events_authorization(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that query raises PERMISSION_DENIED for unauthorized callers."""
    _configure_audit(monkeypatch, tmp_path)

    query = AuditEventQuery(
        start=START,
        end=END,
        limit=10,
        request_id="req-d99df517a5ee6b4c0f39be6fe7cfa0c4d86371b8cc7515ac97f2047f26c0cc0c",
    )

    # Authorized (admin role) -> Succeeds (returns empty page)
    auth_admin = make_auth(admin=True)
    page = query_audit_events(query, auth_admin)
    assert len(page.events) == 0

    # Unauthorized (viewer role, no permission) -> Raises PERMISSION_DENIED
    auth_viewer = make_auth(admin=False)
    with pytest.raises(DataError) as captured:
        query_audit_events(query, auth_viewer)
    assert captured.value.code == "PERMISSION_DENIED"


def test_query_filtering_and_keyset_pagination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify query filtering and keyset pagination cursor mechanics."""
    _configure_audit(monkeypatch, tmp_path)

    # Persist three sequential audit events
    evt1 = make_audit_event(timestamp=START)
    evt2 = make_audit_event(timestamp=START + timedelta(seconds=1))
    evt3 = make_audit_event(timestamp=START + timedelta(seconds=2))

    persist_audit_event(evt1)
    persist_audit_event(evt2)
    persist_audit_event(evt3)

    auth = make_auth(admin=True)

    # 1. Bounded query with limit=2 (page 1)
    query1 = AuditEventQuery(
        start=START - timedelta(seconds=1),
        end=START + timedelta(seconds=5),
        limit=2,
        request_id="req-fd73f938bae2baf88208bab837d9571375e87dfdf6fa0f4a20586570b8f53ced",
    )
    page1 = query_audit_events(query1, auth)
    assert len(page1.events) == 2
    assert page1.events[0].event_id == evt1.event_id
    assert page1.events[1].event_id == evt2.event_id
    assert page1.next_cursor is not None

    # 2. Fetch page 2 using cursor
    query2 = AuditEventQuery(
        start=START - timedelta(seconds=1),
        end=START + timedelta(seconds=5),
        cursor=page1.next_cursor,
        limit=2,
        request_id="req-edc607562832cec9ae86d7151ba1a16623fce4821ad5cec4ec7d34a10711aeed",
    )
    page2 = query_audit_events(query2, auth)
    assert len(page2.events) == 1
    assert page2.events[0].event_id == evt3.event_id
    assert page2.next_cursor is None


def test_query_filtering_optional_params(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify query filtering by optional parameters."""
    _configure_audit(monkeypatch, tmp_path)

    evt = make_audit_event(timestamp=START)
    persist_audit_event(evt)

    auth = make_auth(admin=True)

    # Filter matching all fields
    q_match = AuditEventQuery(
        start=START - timedelta(seconds=1),
        end=START + timedelta(seconds=1),
        limit=10,
        domain=evt.domain,
        action=evt.action,
        principal_id=evt.principal_id,
        correlation_id=evt.correlation_id,
        request_id="req-b55955461cceab6a12ba17c64b01f4264ea4a49351dd6c37f9587b60d80a38a5",
    )
    page_match = query_audit_events(q_match, auth)
    assert len(page_match.events) == 1

    # Filter with non-matching domain
    q_no_match = AuditEventQuery(
        start=START - timedelta(seconds=1),
        end=START + timedelta(seconds=1),
        limit=10,
        domain="non-existent-domain",
        request_id="req-af8a28424f1ac6303d6e5245c9e414706a1f4f4f47d68bb67898cd4085021a9e",
    )
    page_no_match = query_audit_events(q_no_match, auth)
    assert len(page_no_match.events) == 0


def test_query_malformed_cursor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that a malformed cursor raises INVALID_INPUT."""
    _configure_audit(monkeypatch, tmp_path)

    auth = make_auth(admin=True)
    query = AuditEventQuery(
        start=START,
        end=END,
        cursor="malformed_cursor_no_delimiter",
        limit=10,
        request_id="req-041131f35158458920b9da4a031da28bb0cfe05e63c1c4223bd2de2018daa542",
    )

    with pytest.raises(DataError) as captured:
        query_audit_events(query, auth)
    assert captured.value.code == "INVALID_INPUT"


def test_persist_audit_uncommitted_transaction_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that DB_WRITE_FAILED is raised if the commit fails."""
    _configure_audit(monkeypatch, tmp_path)

    import app.services.data.storage.audit as audit_mod
    from app.services.data.contracts import TransactionResult

    def mock_execute(*args, **kwargs):
        # Transaction committed = False
        return TransactionResult(
            committed=False,
            affected_rows=0,
            rows=(),
            request_id="req-4248ec040f25c337464d601a23be28bee0a2a9c01d8ff18ccdbc5913176bd0ff",
        )

    monkeypatch.setattr(audit_mod, "execute_transaction", mock_execute)

    event = make_audit_event()
    with pytest.raises(DataError) as captured:
        persist_audit_event(event)
    assert captured.value.code == "DB_WRITE_FAILED"


def test_persist_audit_exception_mapping(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify database write exception mapping in persist_audit_event."""
    _configure_audit(monkeypatch, tmp_path)

    import app.services.data.storage.audit as audit_mod

    def mock_execute(*args, **kwargs):
        raise ValueError("Mock write database error")

    monkeypatch.setattr(audit_mod, "execute_transaction", mock_execute)

    event = make_audit_event()
    with pytest.raises(DataError) as captured:
        persist_audit_event(event)
    assert captured.value.code == "DB_WRITE_FAILED"


def test_query_audit_exception_mapping(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify database query exception mapping in query_audit_events."""
    _configure_audit(monkeypatch, tmp_path)

    import app.services.data.storage.audit as audit_mod

    def mock_execute(*args, **kwargs):
        raise ValueError("Mock query database error")

    monkeypatch.setattr(audit_mod, "execute_transaction", mock_execute)

    auth = make_auth(admin=True)
    query = AuditEventQuery(
        start=START,
        end=END,
        limit=10,
        request_id="req-42c830675463ef92743a20f6bee6c830b821e4fdc3d1891624cae7366b9cb008",
    )

    with pytest.raises(DataError) as captured:
        query_audit_events(query, auth)
    assert captured.value.code == "DATABASE_ERROR"
