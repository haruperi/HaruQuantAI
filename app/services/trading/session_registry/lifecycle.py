"""Fail-closed authority lifecycle for durable execution sessions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime

from app.services.trading.persistence import update_execution_session_record
from app.services.trading.session_registry.contracts import _SessionRecord
from app.services.trading.session_registry.registry import (
    get_execution_session,
    list_execution_sessions,
)
from app.utils import get_logger

logger = get_logger(__name__)
type AuthorityStart = Callable[[Mapping[str, object]], Awaitable[Mapping[str, object]]]
type AuthorityStop = Callable[[Mapping[str, object]], Awaitable[Mapping[str, object]]]


def _record(session_id: str) -> _SessionRecord:
    """Require one durable registry record.

    Returns:
        Durable SessionRecord instance.

    Raises:
        ValueError: If session is unavailable.
    """
    value = get_execution_session(session_id)
    if not isinstance(value, _SessionRecord):
        raise ValueError("execution session is unavailable")  # noqa: TRY004

    return value


async def start_execution_session(
    session_id: str,
    *,
    expected_version: int,
    authority_start: AuthorityStart,
    request_id: str,
) -> object:
    """Verify an authority, then admit exactly one foreground session.

    Returns:
        Started durable SessionRecord object.

    Raises:
        ValueError: If state, authority verification, or mode mismatch fails.
    """
    session = _record(session_id)
    logger.info("Starting Trading execution session %s", session_id)
    if session.version != expected_version or session.lifecycle_state not in {
        "draft",
        "stopped",
        "verified",
        "error",
    }:
        raise ValueError("execution session cannot be started from its current state")
    evidence = await authority_start(session.model_dump(mode="json"))
    if not bool(evidence.get("verified")):
        raise ValueError("execution session authority verification failed")
    actual_mode = evidence.get("mode")
    if actual_mode != session.mode:
        raise ValueError("execution session authority mode mismatch")
    now = datetime.now(UTC).isoformat()
    # Deactivate any prior foreground session before enabling the verified one.
    for previous in list_execution_sessions(
        principal_id=session.principal_id, environment_id=session.environment_id
    ):
        if isinstance(previous, _SessionRecord) and previous.is_active:
            if previous.lifecycle_state == "running":
                raise ValueError("active execution session must be stopped first")
            update_execution_session_record(
                previous.session_id,
                expected_version=previous.version,
                changes={"is_active": False, "updated_at": now},
                event_type="deactivated",
                request_id=request_id,
            )
    changes: dict[str, object] = {
        "lifecycle_state": "running",
        "recovery_state": "running",
        "is_active": True,
        "started_at": now,
        "last_reconciled_at": now,
        "last_error_code": None,
        "updated_at": now,
    }
    account_name = evidence.get("account_name")
    if session.mode != "sim" and isinstance(account_name, str) and account_name.strip():
        changes["provider_account_ref"] = account_name.strip()
    simulation_runtime_ref = evidence.get("simulation_runtime_ref")
    if isinstance(simulation_runtime_ref, str):
        changes["simulation_runtime_ref"] = simulation_runtime_ref
    update_execution_session_record(
        session_id,
        expected_version=expected_version,
        changes=changes,
        event_type="started",
        request_id=request_id,
    )
    logger.info("Started Trading execution session %s", session_id)
    return _record(session_id)


async def stop_execution_session(
    session_id: str,
    *,
    expected_version: int,
    authority_stop: AuthorityStop,
    request_id: str,
) -> object:
    """Disable admission, reconcile, then stop one running authority.

    Returns:
        Stopped durable SessionRecord object.

    Raises:
        ValueError: If session is not running or authority stop fails.
    """
    session = _record(session_id)
    logger.info("Stopping Trading execution session %s", session_id)
    if session.version != expected_version or session.lifecycle_state != "running":
        raise ValueError("execution session is not running")
    evidence = await authority_stop(session.model_dump(mode="json"))
    if not bool(evidence.get("safe_to_stop")):
        raise ValueError("execution session has unresolved authority state")
    now = datetime.now(UTC).isoformat()
    update_execution_session_record(
        session_id,
        expected_version=expected_version,
        changes={
            "lifecycle_state": "stopped",
            "recovery_state": "not_required",
            "is_active": False,
            "stopped_at": now,
            "last_reconciled_at": now,
            "updated_at": now,
        },
        event_type="stopped",
        request_id=request_id,
    )
    logger.info("Stopped Trading execution session %s", session_id)
    return _record(session_id)


def resolve_active_execution_session(
    *, principal_id: str, environment_id: str, mode: str | None = None
) -> object | None:
    """Resolve the sole running foreground session for one exact scope.

    Returns:
        Active SessionRecord if found, otherwise None.

    Raises:
        ValueError: If multiple active sessions exist for the scope.
    """
    active = [
        item
        for item in list_execution_sessions(
            principal_id=principal_id, environment_id=environment_id, mode=mode
        )
        if isinstance(item, _SessionRecord)
        and item.is_active
        and item.lifecycle_state == "running"
    ]
    if len(active) > 1:
        raise ValueError("multiple active execution sessions violate registry policy")
    return None if not active else active[0]


__all__ = [
    "resolve_active_execution_session",
    "start_execution_session",
    "stop_execution_session",
]
