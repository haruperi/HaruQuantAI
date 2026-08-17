"""Recoverable archival operations for Trading-owned session records."""

from datetime import UTC, datetime

from app.services.trading.persistence.read import read_execution_session_record
from app.services.trading.persistence.update import update_execution_session_record


def archive_execution_session_record(
    session_id: str, *, expected_version: int, request_id: str
) -> None:
    """Archive a stopped, inactive, non-default session without deleting evidence.

    Raises:
        ValueError: If session is unavailable, running, active, or default.
    """
    current = read_execution_session_record(session_id)
    if current is None:
        raise ValueError("execution session is unavailable")
    if current["lifecycle_state"] not in {"draft", "stopped", "error"}:
        raise ValueError("only a non-running execution session can be archived")
    if current["is_active"] or current["is_default"]:
        raise ValueError("active or default execution session cannot be archived")
    now = datetime.now(UTC).isoformat()
    update_execution_session_record(
        session_id,
        expected_version=expected_version,
        changes={
            "lifecycle_state": "archived",
            "archived_at": now,
            "updated_at": now,
        },
        event_type="archived",
        request_id=request_id,
    )


__all__ = ["archive_execution_session_record"]
