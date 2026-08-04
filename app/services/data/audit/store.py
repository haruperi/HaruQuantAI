"""Durable, idempotent persistence of Utils-owned redacted audit events.

Split from ``storage/audit.py`` by ``CAP-DATA-026``. ``audit`` is its own module folder
rather than a ``persistence`` file because it owns a cross-domain contract
(``AuditEventQuery`` / ``AuditEventPage``) with its own authorization semantics,
consumed by UI/API and Risk. ``persistence`` owns storage mechanics; ``audit`` owns
what an audit query means and who may run one.

This module holds the write half. The authorized read half is ``audit/query.py``;
it does not import this module, so the two halves stay independently testable.
"""

# Audit events are opaque cross-domain Utils values at this private boundary.
# ruff: noqa: ANN401

from __future__ import annotations

import json
from typing import Any

from app.services.data.audit.contracts import (
    AuditPersistenceResult,
)
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.persistence import create_audit_event_record
from app.utils import get_logger

logger = get_logger(__name__)


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


def _persist_audit_event_raw(event: Any) -> AuditPersistenceResult:
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

        result = create_audit_event_record(params, request_id=event.request_id)
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
        logger.exception("Audit event persistence failed")
        if isinstance(error, DataError):
            raise
        raise DataError(
            "DB_WRITE_FAILED",
            safe_details={"operation": "persist_audit_event"},
            request_id=event.request_id,
        ) from error


def persist_audit_event(
    event: Any,
) -> StandardResponse[AuditPersistenceResult]:
    """Idempotently persist a redacted AuditEvent version 1 into SQLite.

    Args:
        event: The audit event to persist.

    Returns:
        Standard response carrying the audit persistence result.
    """
    return run_data_operation(
        operation="data.audit.persist_audit_event",
        request_id=event.request_id,
        start_time=data_start_time(),
        raw=lambda: _persist_audit_event_raw(event),
    )


__all__ = ["persist_audit_event"]
