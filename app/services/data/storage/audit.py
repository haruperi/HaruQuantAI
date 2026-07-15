"""Governed local audit event logging and querying."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final

from app.services.data.contracts import (
    AuditEventPage,
    AuditEventQuery,
    AuditPersistenceResult,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.contracts.errors import DataError
from app.services.data.storage.database import execute_transaction
from app.utils import AuditEvent, logger

if TYPE_CHECKING:
    from app.utils.contracts.auth import AuthContext

_INSERT_AUDIT_EVENT: Final = """
INSERT OR IGNORE INTO data_audit_events (
    event_id, timestamp, domain, action, principal_id,
    request_id, correlation_id, causation_id, payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()


def _raise_write_failed(event_id: str, request_id: str) -> None:
    """Helper to raise write failure to satisfy TRY301."""
    logger.debug("Running DATA function: _raise_write_failed")
    raise DataError(
        "DB_WRITE_FAILED",
        safe_details={
            "event_id": event_id,
            "reason": "Transaction rolled back or failed",
        },
        request_id=request_id,
    )


def persist_audit_event(event: AuditEvent) -> AuditPersistenceResult:
    """Idempotently persist a redacted AuditEvent version 1 into SQLite.

    Args:
        event: The audit event to persist.

    Returns:
        The audit persistence result.

    Raises:
        DataError: For database write failures.
    """
    try:
        payload_json = json.dumps(dict(event.payload))
        params = (
            event.event_id,
            event.timestamp.isoformat(),
            event.domain,
            event.action,
            event.principal_id,
            event.request_id,
            event.correlation_id,
            event.causation_id,
            payload_json,
        )

        tx_request = TransactionRequest(
            plan=StatementPlan(
                statements=(_INSERT_AUDIT_EVENT,),
                parameter_sets=(params,),
                max_rows=1,
            ),
            request_id=event.request_id,
        )

        result = execute_transaction(tx_request)
        if not result.committed:
            _raise_write_failed(event.event_id, event.request_id)

        if result.affected_rows == 0:
            # Event already existed, idempotent skip
            return AuditPersistenceResult(
                event_id=event.event_id,
                persisted=False,
                idempotent=True,
                request_id=event.request_id,
            )

        return AuditPersistenceResult(
            event_id=event.event_id,
            persisted=True,
            idempotent=False,
            request_id=event.request_id,
        )

    except Exception as error:
        logger.error("Audit event persistence failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "persist_audit_event"},
            request_id=event.request_id,
        ) from error


def _build_audit_query(request: AuditEventQuery) -> tuple[str, list[Any]]:
    """Build the SQL query and query parameters dynamically."""
    logger.debug("Building a bounded audit query")
    sql_parts = [
        "SELECT event_id, timestamp, domain, action, principal_id, request_id, "
        "correlation_id, causation_id, payload_json FROM data_audit_events "
        "WHERE timestamp >= ? AND timestamp <= ?"
    ]
    params: list[Any] = [request.start.isoformat(), request.end.isoformat()]

    if request.domain is not None:
        sql_parts.append("AND domain = ?")
        params.append(request.domain)
    if request.action is not None:
        sql_parts.append("AND action = ?")
        params.append(request.action)
    if request.principal_id is not None:
        sql_parts.append("AND principal_id = ?")
        params.append(request.principal_id)
    if request.correlation_id is not None:
        sql_parts.append("AND correlation_id = ?")
        params.append(request.correlation_id)

    # Keyset pagination cursor
    if request.cursor is not None:
        try:
            cursor_ts, cursor_evt = request.cursor.split("||", 1)
            sql_parts.append("AND (timestamp > ? OR (timestamp = ? AND event_id > ?))")
            params.extend([cursor_ts, cursor_ts, cursor_evt])
        except ValueError as ve:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"reason": "Malformed query pagination cursor"},
                request_id=request.request_id,
            ) from ve

    sql_parts.append("ORDER BY timestamp ASC, event_id ASC LIMIT ?")
    params.append(request.limit)

    return " ".join(sql_parts).strip(), params


def _parse_audit_events(rows: tuple[Mapping[str, Any], ...]) -> list[AuditEvent]:
    """Parse raw SQLite query result rows into AuditEvent objects."""
    logger.debug("Parsing persisted audit rows into Utils contracts")
    events = []
    for row in rows:
        ts_str = str(row["timestamp"])
        events.append(
            AuditEvent(
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


def query_audit_events(
    request: AuditEventQuery, auth_context: AuthContext
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
        query_sql, params = _build_audit_query(request)

        tx_request = TransactionRequest(
            plan=StatementPlan(
                statements=(query_sql,),
                parameter_sets=(tuple(params),),
                max_rows=request.limit,
            ),
            request_id=request.request_id,
        )

        result = execute_transaction(tx_request)
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
        logger.error("Audit query failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DATABASE_ERROR",
            safe_details={"operation": "query_audit_events"},
            request_id=request.request_id,
        ) from error
