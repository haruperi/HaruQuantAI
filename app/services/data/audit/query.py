"""Authorized, bounded, deterministically ordered audit event queries.

Split from ``storage/audit.py`` by ``CAP-DATA-026``. Holds the read half: every query
is authorized against an ``AuthContext``, bounded by ``AUDIT_QUERY_HARD_MAX_LIMIT``,
and returns a cursor page. No storage handle or unredacted payload crosses the
boundary.
"""

# Auth context is an opaque cross-domain Utils value at this private boundary.
# ruff: noqa: ANN401

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.services.data.audit.contracts import (
    AuditEventPage,
    AuditEventQuery,
)
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.persistence import read_audit_event_records
from app.utils import create_audit_event, get_logger

type AuthContext = Any

logger = get_logger(__name__)

_AUDIT_CURSOR_PART_COUNT = 2


def _parse_audit_cursor(request: AuditEventQuery) -> tuple[str | None, str | None]:
    """Parse one keyset-pagination cursor into its storage identities."""
    if request.cursor is None:
        return None, None
    parts = request.cursor.split("||", 1)
    if len(parts) != _AUDIT_CURSOR_PART_COUNT:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"reason": "Malformed query pagination cursor"},
            request_id=request.request_id,
        )
    return parts[0], parts[1]


def _parse_audit_events(rows: tuple[Mapping[str, Any], ...]) -> list[Any]:
    """Parse raw SQLite query result rows into AuditEvent objects."""
    logger.debug("Parsing persisted audit rows into Utils contracts")
    events = []
    for row in rows:
        ts_str = str(row["timestamp"])
        events.append(
            create_audit_event(
                contract_version="v1",
                schema_id="utils.audit_event.v1",
                event_id=str(row["event_id"]),
                timestamp=datetime.fromisoformat(ts_str),
                domain=str(row["domain"]),
                action=str(row["action"]),
                principal_id=(
                    str(row["principal_id"]) if row["principal_id"] else None
                ),
                request_id=str(row["request_id"]),
                correlation_id=str(row["correlation_id"]),
                causation_id=(
                    str(row["causation_id"]) if row["causation_id"] else None
                ),
                payload=json.loads(str(row["payload_json"])),
            )
        )
    return events


def _query_audit_events_raw(
    request: AuditEventQuery, auth_context: Any
) -> AuditEventPage:
    """Authorize and execute a bounded cursor-paginated audit query in SQLite.

    Args:
        request: The audit event query filters and limits.
        auth_context: The authenticated caller context.

    Returns:
        An AuditEventPage containing the ordered events.

    Raises:
        DataError: For permission or query validation errors.
    """
    # Enforce role/permission checks
    if (
        "admin" not in auth_context.roles
        and "audit:read" not in auth_context.permissions
        and "audit.read" not in auth_context.permissions
    ):
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={
                "principal_id": auth_context.principal_id,
                "reason": "Principal lacks admin or audit reader permissions",
            },
            request_id=request.request_id,
        )

    try:
        cursor_timestamp, cursor_event_id = _parse_audit_cursor(request)
        result = read_audit_event_records(
            start=request.start.isoformat(),
            end=request.end.isoformat(),
            domain=request.domain,
            action=request.action,
            principal_id=request.principal_id,
            correlation_id=request.correlation_id,
            cursor_timestamp=cursor_timestamp,
            cursor_event_id=cursor_event_id,
            limit=request.limit,
            request_id=request.request_id,
        )
        events = _parse_audit_events(result.rows)

        # Determine if a next page cursor should be generated
        next_cursor = None
        if len(events) == request.limit:
            next_cursor = f"{events[-1].timestamp.isoformat()}||{events[-1].event_id}"

        return AuditEventPage(
            events=tuple(events),
            next_cursor=next_cursor,
            request_id=request.request_id,
        )

    except Exception as error:
        logger.exception("Audit query failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "query_audit_events"},
            request_id=request.request_id,
        ) from error


def query_audit_events(
    request: AuditEventQuery, auth_context: AuthContext
) -> StandardResponse[AuditEventPage]:
    """Authorize and execute a bounded cursor-paginated audit query in SQLite.

    Args:
        request: The audit event query filters and limits.
        auth_context: The authenticated caller context.

    Returns:
        Standard response carrying an AuditEventPage of ordered events.
    """
    return run_data_operation(
        operation="data.audit.query_audit_events",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _query_audit_events_raw(request, auth_context),
    )


__all__ = ["query_audit_events"]
