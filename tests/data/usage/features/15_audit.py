"""Demonstrate FEAT-DATA-15 audit evidence persistence and query operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_audit_event_query,
    build_data_settings,
    data_settings_context,
    persist_audit_event,
    query_audit_events,
    run_data_migrations,
)
from app.utils import create_audit_event, create_auth_context, generate_id

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(hours=1)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_data_021() -> None:
    """FR-DATA-021: Stage 1 — Create and persist immutable AuditEvent records to the database ledger."""
    _header(
        "Stage 1: Audit Event Creation & Persistence - Persist Audit Event (FR-DATA-021)"
    )
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
    print(_format_result(event))

    res = persist_audit_event(event)
    print(_format_result(res))
    if res.status == "success" and res.data:
        print(f"Data -> AuditPersistenceResult(persisted={res.data.persisted})")


def fr_data_077() -> None:
    """FR-DATA-077: Stage 2 — Query persisted audit events with authorized RBAC AuthContext filtering."""
    _header(
        "Stage 2: Audit Event Querying & RBAC Filtering - Query Audit Events (FR-DATA-077)"
    )
    req_id = generate_id("req")
    query = build_audit_event_query(
        start=_START,
        end=_END,
        limit=10,
        request_id=req_id,
    )
    print(_format_result(query))

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

    res_q = query_audit_events(query, auth)
    print(_format_result(res_q))
    if res_q.status == "success" and res_q.data:
        print(f"Data -> AuditEventPage(count={len(res_q.data.events)})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
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
            print("=" * 80)
            print("FEATURE: FEAT-DATA-15 - Data Audit and Compliance")
            print(
                "PURPOSE: Create, persist, and query immutable audit event logs with authorized RBAC controls"
            )
            print(
                "MODULE FLOW: Stage 1 (Creation & Persistence) -> Stage 2 (Querying & RBAC Filtering)"
            )
            print("=" * 80)

            fr_data_021()
            fr_data_077()
            print("SUCCESS: FEAT-DATA-15 completed")


if __name__ == "__main__":
    main()
