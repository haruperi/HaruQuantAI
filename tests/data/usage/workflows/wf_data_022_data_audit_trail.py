"""WF-DATA-022: persist and read one bounded Data audit trail end to end."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_audit_event_query,
    build_data_settings,
    data_settings_context,
    persist_audit_event,
    query_audit_events,
    resolve_operation_request_id,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import create_audit_event, create_auth_context, generate_id


def _error_code(error: BaseException) -> str:
    """Return a safe public-boundary error identifier."""
    return str(getattr(error, "code", type(error).__name__))


WORKFLOW_ID = "WF-DATA-022"
STAGES = (
    "The emitting domain constructs and redacts its event at the shared boundary.",
    "Data validates the envelope and persists it under the write lock.",
    "The write commits transactionally with the action it records.",
    "Operators read bounded ordered pages of recorded events.",
    "Every read resolves its originating request identity for correlation.",
)

_START = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
_END = _START + timedelta(hours=1)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def _build_event(request_id: str) -> object:
    """Build one redacted audit event through the shared Utils boundary."""
    return create_audit_event(
        event_id=generate_id("evt"),
        timestamp=_START,
        domain="data",
        action="workflow_audit_trail",
        request_id=request_id,
        correlation_id=generate_id("cor"),
        payload={"symbol": "EURUSD", "records_examined": 512},
        principal_id="user_admin",
        causation_id=generate_id("cau"),
    )


def _authorized_reader(request_id: str) -> object:
    """Build the authorized operator context used for the audit read."""
    return create_auth_context(
        principal_id="user_admin",
        principal_type="USER",
        roles=("admin", "auditor"),
        permissions=("audit:read",),
        scopes=("data:read",),
        tenant_or_environment="research",
        request_id=request_id,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_START,
    )


def main() -> None:
    """Run the documented Data audit-trail workflow from event to bounded page."""
    print(f"{WORKFLOW_ID} — Data Audit Trail")
    print("INPUT BOUNDARY — redacted AuditEvent v1 or bounded audit query")

    request_id = generate_id("req")

    # Stage 1 — The emitting domain constructs and redacts its event at the shared boundary.
    _stage(1)
    event = _build_event(request_id)
    _report("event  ", "success", f"{event.event_id} {event.domain}.{event.action}")
    print("Event payload        :", event.payload)
    assert event.domain == "data"

    with TemporaryDirectory() as temporary:
        directory = Path(temporary)
        settings = build_data_settings(
            database_url="sqlite:///wf_data_022_audit.sqlite3",
            data_dir=directory,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=30.0,
            approved_storage_roots=(directory,),
        )
        with data_settings_context(settings):
            # Stage 2 — Data validates the envelope and persists it under the write lock.
            _stage(2)
            run_data_migrations(generate_id("req"))
            print("Migrations applied   : True")
            try:
                receipt_resp = persist_audit_event(event)
                receipt = unwrap_data_response(
                    receipt_resp, operation="persist_audit_event", request_id=request_id
                )
                _report("persist", "success", receipt.persisted)
            except Exception as error:
                _report("persist", "fail", _error_code(error))
                raise

            # Stage 3 — The write commits transactionally with the action it records.
            _stage(3)
            try:
                repeated_resp = persist_audit_event(event)
                repeated = unwrap_data_response(
                    repeated_resp,
                    operation="persist_audit_event",
                    request_id=request_id,
                )
                _report("repeat ", "success", repeated.persisted)
                print("Idempotent re-persist accepted: True")
            except Exception as error:  # noqa: BLE001
                _report("repeat ", "fail", _error_code(error))

            # Stage 4 — Operators read bounded ordered pages of recorded events.
            _stage(4)
            query = build_audit_event_query(
                start=_START,
                end=_END,
                limit=10,
                request_id=request_id,
            )
            auth = _authorized_reader(request_id)
            print("Query window         :", query.start, "->", query.end)
            print("Query limit          :", query.limit)
            try:
                page_resp = query_audit_events(query, auth)
                page = unwrap_data_response(
                    page_resp, operation="query_audit_events", request_id=request_id
                )
                _report("query  ", "success", f"{len(page.events)} event(s)")
                for recorded in page.events[:3]:
                    print("  -", recorded.event_id, recorded.action)
            except Exception as error:
                _report("query  ", "fail", _error_code(error))
                raise

            # Stage 5 — Every read resolves its originating request identity for correlation.
            _stage(5)
            resolved, _ = resolve_operation_request_id(request_id)
            _report("trace  ", "success", resolved)
            assert resolved
            print("Correlated to emitting request: True")

    print("\nOUTPUT BOUNDARY — durably persisted event or bounded ordered audit page")


if __name__ == "__main__":
    main()
