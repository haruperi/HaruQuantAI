"""Demonstrate FEAT-DATA-15 audit evidence persistence and query operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_audit_event_query,
    build_data_settings,
    data_settings_context,
    persist_audit_event,
    query_audit_events,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import create_audit_event, create_auth_context, generate_id


def _error_code(error: BaseException) -> str:
    """Return a safe public-boundary error identifier."""
    return str(getattr(error, "code", type(error).__name__))


_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(hours=1)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _demonstrate_feature() -> None:
    """Exercise audit event creation, persistence, and authorized query."""
    with TemporaryDirectory(prefix="usage-audit-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            _demonstrate_audit_operations()


def _demonstrate_audit_operations() -> None:
    """Run the audit persist and query operations inside an active context."""
    req_id = generate_id("req")

    event = create_audit_event(
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
        res_data = unwrap_data_response(
            res, operation="persist_audit_event", request_id=req_id
        )
        print("persist_audit_event:", res_data.persisted)
    except Exception as error:  # noqa: BLE001 - domain error classes stay internal.
        print("persist_audit_event handled:", _error_code(error))

    query = build_audit_event_query(
        start=_START,
        end=_END,
        limit=10,
        request_id=req_id,
    )
    auth = create_auth_context(
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
        res_q = query_audit_events(query, auth)
        res_q_data = unwrap_data_response(
            res_q, operation="query_audit_events", request_id=req_id
        )
        print("query_audit_events count:", len(res_q_data.events))
    except Exception as error:  # noqa: BLE001 - domain error classes stay internal.
        print("query_audit_events handled:", _error_code(error))


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_021() -> None:
    _header("fr_data_021")
    _demonstrate_once()


def fr_data_077() -> None:
    _header("fr_data_077")
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_021,
        fr_data_077,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
