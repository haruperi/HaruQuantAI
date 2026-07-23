"""Demonstrate FEAT-DATA-15 audit evidence persistence and query operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.audit import persist_audit_event, query_audit_events
from app.services.data.audit.contracts import AuditEventQuery
from app.utils import AuditEvent, AuthContext, generate_id

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(hours=1)


def main() -> None:
    """Exercise audit event creation, persistence, and authorized query."""
    req_id = generate_id("req")

    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=_START,
        domain="data",
        action="usage_test",
        principal_id="user_admin",
        request_id=req_id,
        correlation_id=generate_id("cor"),
        causation_id=generate_id("cau"),
        payload={"status": "ok"},
    )
    print("AuditEvent:", event.event_id, event.domain, event.action)

    try:
        res = persist_audit_event(event)
        print("persist_audit_event:", res.persisted)
    except Exception as err:
        print("persist_audit_event handled:", type(err).__name__)

    query = AuditEventQuery(
        start=_START,
        end=_END,
        limit=10,
        request_id=req_id,
    )
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user_admin",
        principal_type="USER",
        roles=("admin", "auditor"),
        permissions=("audit:read",),
        scopes=("data:read",),
        tenant_or_environment="research",
        request_id=req_id,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_START,
    )
    print("AuditEventQuery:", query.start, query.limit)
    print("AuthContext:", auth.principal_id)

    try:
        page = query_audit_events(query, auth)
        print("query_audit_events count:", len(page.events))
    except Exception as err:
        print("query_audit_events handled:", type(err).__name__)


if __name__ == "__main__":
    main()
