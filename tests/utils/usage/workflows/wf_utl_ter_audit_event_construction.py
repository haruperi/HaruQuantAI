"""WF-UTL-TER: construct and persist one redacted audit event."""

from __future__ import annotations

import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_audit_event_query,
    build_data_settings,
    data_settings_context,
    persist_audit_event,
    query_audit_events,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import (
    canonical_digest,
    canonical_json,
    create_audit_event,
    create_auth_context,
    generate_id,
    redact_mapping_value,
    utc_now,
    validate_id,
)

WORKFLOW_ID = "WF-UTL-TER"
STAGES = (
    "Accept domain action facts and trace context.",
    "Generate and validate IDs and an aware UTC timestamp.",
    "Redact and canonicalize the payload.",
    "Construct a bounded AuditEvent v1.",
    "Persist and read the event through Data's audit boundary.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented audit workflow from facts to durable evidence."""
    print(f"{WORKFLOW_ID} — Audit-Event Construction")
    print("INPUT BOUNDARY — domain-owned action facts and trace context")

    # Stage 1 — Accept domain action facts and trace context.
    _stage(1)
    action = "workflow_completed"
    raw_payload = {"status": "accepted", "api_token": "synthetic-secret"}
    print("Action and payload keys:", action, tuple(raw_payload))

    # Stage 2 — Generate and validate IDs and an aware UTC timestamp.
    _stage(2)
    request_id = validate_id(generate_id("req"), expected_prefix="req")
    workflow_id = validate_id(generate_id("wf"), expected_prefix="wf")
    correlation_id = validate_id(generate_id("cor"), expected_prefix="cor")
    event_id = validate_id(generate_id("evt"), expected_prefix="evt")
    timestamp = utc_now()
    print("Validated trace prefixes:", request_id[:3], workflow_id[:2], event_id[:3])

    # Stage 3 — Redact and canonicalize the payload.
    _stage(3)
    redaction = redact_mapping_value(raw_payload)
    assert isinstance(redaction.value, dict)
    serialized = canonical_json(redaction.value)
    digest = canonical_digest(redaction.value)
    assert "synthetic-secret" not in serialized
    print("Canonical payload digest:", digest)

    # Stage 4 — Construct a bounded AuditEvent v1.
    _stage(4)
    event = create_audit_event(
        event_id=event_id,
        timestamp=timestamp,
        domain="utils",
        action=action,
        request_id=request_id,
        correlation_id=correlation_id,
        payload=redaction.value,
    )
    print("Constructed event:", event.event_id, event.action)

    # Stage 5 — Persist and read the event through Data's audit boundary.
    _stage(5)
    with tempfile.TemporaryDirectory(prefix="wf-utl-003-") as directory:
        settings = build_data_settings(
            database_url="sqlite:///audit.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
        )
        auth = create_auth_context(
            principal_id="workflow-reader",
            principal_type="SERVICE_ACCOUNT",
            roles=("admin",),
            permissions=("audit:read",),
            scopes=(),
            tenant_or_environment="dev",
            request_id=request_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
            issued_at=timestamp,
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            persisted = unwrap_data_response(
                persist_audit_event(event),
                operation="data.audit.persist_audit_event",
                request_id=event.request_id,
            )
            query = build_audit_event_query(
                start=timestamp - timedelta(seconds=1),
                end=timestamp + timedelta(seconds=1),
                domain="utils",
                limit=10,
                request_id=generate_id("req"),
            )
            page = unwrap_data_response(
                query_audit_events(query, auth),
                operation="data.audit.query_audit_events",
                request_id=query.request_id,
            )
        assert persisted.persisted
        assert tuple(item.event_id for item in page.events) == (event.event_id,)
        print("Persisted and read event:", page.events[0].event_id)

    print("OUTPUT BOUNDARY — persisted redacted AuditEvent v1")


if __name__ == "__main__":
    main()
