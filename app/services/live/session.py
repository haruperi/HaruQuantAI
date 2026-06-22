"""Live session lifecycle management.

Handles live session startup, shutdown, recovery diagnostics, and
runtime status emission. This module orchestrates live runtime startup/
shutdown sequencing and structured runtime status events for approved
consumers.

OS signal handling (``SIGTERM``, ``SIGINT``) is the responsibility of
the application entry point, which should call ``stop_live_session``
in its signal handlers. This module does not register signal handlers
directly so that it remains importable in async and multi-threaded
environments without side effects.

Ownership:
    - Owns live session state machine, startup/shutdown sequencing,
      and runtime status/event emission.
    - Does NOT own broker adapters, strategy lifecycle, risk policy,
      or UI.

Public exports:
    LiveSession, LiveSessionStatus, start_live_session,
    stop_live_session, recover_live_session, get_live_session_status.

Side effects:
    None on import. No sessions are opened, no sockets are created,
    no threads are started, and no secret values are resolved at
    import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.utils.errors import ValidationError
from app.utils.logger import logger
from app.utils.settings import Settings, validate_config


class LiveSessionStatus(StrEnum):
    """Enumeration of live session lifecycle states.

    States follow a strict one-directional promotion ladder:

    ``INACTIVE`` → ``STARTING`` → ``ACTIVE`` → ``STOPPING``
    → ``STOPPED`` (terminal).

    Or from any non-``STOPPED`` state → ``ERROR`` (terminal).

    Attributes:
        INACTIVE: No session is running.
        STARTING: Session is being initialised.
        ACTIVE: Session is running and accepting requests.
        PAUSED: Session is running but blocked pending operator
            review (e.g. unknown outcomes from a previous run).
        STOPPING: Session is shutting down.
        STOPPED: Session has terminated successfully (terminal).
        ERROR: Session encountered an unrecoverable error (terminal).
    """

    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LiveSessionEvent:
    """Immutable record of a live session state transition event.

    Attributes:
        event_type: Type of event (e.g. ``'session_started'``).
        timestamp: UTC timestamp of the event.
        details: Structured, redacted event details (no secrets).
        request_id: Optional trace identifier propagated from the
            caller.
    """

    event_type: str
    timestamp: datetime
    details: dict[str, Any]
    request_id: str | None = None


@dataclass
class LiveSession:
    """Snapshot of the current live session state.

    This is an immutable data transfer object. All mutation must go
    through the session lifecycle functions (``start_live_session``,
    ``stop_live_session``, ``recover_live_session``).

    Attributes:
        session_id: Unique identifier for this session.
        status: Current ``LiveSessionStatus``.
        started_at: UTC timestamp when the session entered ACTIVE
            state, or ``None`` before activation.
        stopped_at: UTC timestamp when the session was stopped or
            errored, or ``None`` while active.
        live_enabled: Whether live mutation was enabled for this
            session.
        live_mode: Live promotion ladder rung for this session.
        events: Ordered list of session lifecycle events.
        recovery_context: Optional structured recovery diagnostics.
        request_id: Trace identifier from the start request.
    """

    session_id: str
    status: LiveSessionStatus
    started_at: datetime | None
    stopped_at: datetime | None
    live_enabled: bool
    live_mode: str
    events: list[LiveSessionEvent]
    recovery_context: dict[str, Any] | None
    request_id: str | None


# Module-level in-memory session store (single active session).
# In production this is replaced by an injected LiveStateStore port.
_active_session: LiveSession | None = None

# States in which a new session cannot be started.
_BLOCKING_STATUSES = frozenset(
    {
        LiveSessionStatus.STARTING,
        LiveSessionStatus.ACTIVE,
        LiveSessionStatus.PAUSED,
    }
)


def start_live_session(
    *,
    config: Settings,
    session_id: str,
    request_id: str | None = None,
) -> LiveSession:
    """Start a live runtime session after validating config.

    Validates the live configuration, checks that live mode is
    appropriately set, and transitions the session to ACTIVE. Does
    NOT call broker adapters or open network connections.

    Live mutation remains disabled by default unless explicitly enabled
    via configuration. The session records ``live_enabled`` and
    ``live_mode`` at startup so they cannot be changed mid-session
    without a restart.

    Args:
        config: Validated ``Settings`` instance for this session.
        session_id: Unique stable session identifier (caller-provided).
        request_id: Optional trace identifier propagated through all
            events.

    Returns:
        ``LiveSession`` snapshot of the newly started session in
        ``ACTIVE`` status.

    Raises:
        ValidationError: If ``session_id`` is empty or config
            validation fails.
        RuntimeError: If a session is already active (single-session
            guard).
    """
    global _active_session  # noqa: PLW0603

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValidationError(
            "session_id must be a non-empty string.",
            code="INVALID_INPUT",
        )
    session_id = session_id.strip()

    if (
        _active_session is not None
        and _active_session.status in _BLOCKING_STATUSES
    ):
        raise RuntimeError(
            f"A live session is already active "
            f"(session_id={_active_session.session_id!r}). "
            "Stop it before starting a new one."
        )

    validation_errors = validate_config(config)
    if validation_errors:
        logger.warning(
            "live_session.start_rejected.config_invalid "
            "session_id=%r request_id=%r error_count=%r",
            session_id,
            request_id,
            len(validation_errors),
        )
        raise ValidationError(
            f"Live configuration is invalid "
            f"({len(validation_errors)} error(s)): "
            + "; ".join(validation_errors),
            code="CONFIGURATION_ERROR",
        )

    now = datetime.now(UTC)
    start_event = LiveSessionEvent(
        event_type="session_started",
        timestamp=now,
        details={
            "live_enabled": config.live_enabled,
            "live_mode": config.live_mode,
            "live_workflow_timeout_seconds": (
                config.live_workflow_timeout_seconds
            ),
            "live_max_staleness_seconds": (
                config.live_max_staleness_seconds
            ),
        },
        request_id=request_id,
    )

    session = LiveSession(
        session_id=session_id,
        status=LiveSessionStatus.ACTIVE,
        started_at=now,
        stopped_at=None,
        live_enabled=config.live_enabled,
        live_mode=config.live_mode,
        events=[start_event],
        recovery_context=None,
        request_id=request_id,
    )

    _active_session = session
    logger.info(
        "live_session.started session_id=%r "
        "live_enabled=%r live_mode=%r request_id=%r",
        session_id,
        config.live_enabled,
        config.live_mode,
        request_id,
    )
    return session


def stop_live_session(
    *,
    session_id: str,
    reason: str = "operator_stop",
    request_id: str | None = None,
) -> LiveSession:
    """Stop the active live session and flush audit evidence.

    Transitions the session to ``STOPPED``, stops accepting new
    mutation requests, and records the stop event. In a production
    implementation this flushes pending audit evidence to the
    ``AuditSink`` and reports any unresolved live work before
    completing. That flush is the responsibility of the application
    layer that holds the ``AuditSink`` reference.

    Args:
        session_id: Session identifier to stop. Must match the active
            session.
        reason: Human-readable stop reason (e.g. ``'operator_stop'``,
            ``'kill_switch'``).
        request_id: Optional trace identifier.

    Returns:
        ``LiveSession`` snapshot of the stopped session.

    Raises:
        ValidationError: If ``session_id`` is empty or does not match
            the active session.
        RuntimeError: If no active session exists.
    """
    global _active_session  # noqa: PLW0603

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValidationError(
            "session_id must be a non-empty string.",
            code="INVALID_INPUT",
        )

    if _active_session is None:
        raise RuntimeError("No active live session to stop.")

    if _active_session.session_id != session_id.strip():
        raise ValidationError(
            f"session_id mismatch: expected "
            f"{_active_session.session_id!r}, "
            f"got {session_id.strip()!r}.",
            code="INVALID_INPUT",
        )

    now = datetime.now(UTC)
    stop_event = LiveSessionEvent(
        event_type="session_stopped",
        timestamp=now,
        details={"reason": reason},
        request_id=request_id,
    )

    events = [*_active_session.events, stop_event]
    stopped = LiveSession(
        session_id=_active_session.session_id,
        status=LiveSessionStatus.STOPPED,
        started_at=_active_session.started_at,
        stopped_at=now,
        live_enabled=_active_session.live_enabled,
        live_mode=_active_session.live_mode,
        events=events,
        recovery_context=_active_session.recovery_context,
        request_id=_active_session.request_id,
    )

    _active_session = None
    logger.info(
        "live_session.stopped session_id=%r "
        "reason=%r request_id=%r",
        session_id,
        reason,
        request_id,
    )
    return stopped


def recover_live_session(
    *,
    session_id: str,
    recovery_context: dict[str, Any],
    config: Settings,
    request_id: str | None = None,
) -> LiveSession:
    """Recover a live session from persisted state after a restart.

    Runs recovery diagnostics and produces a session with ``ACTIVE``
    status only when the recovery context is clean. If unknown outcomes,
    in-flight reconciliation, or startup mismatches are detected, the
    session starts in ``PAUSED`` status and must be reviewed before
    mutations are allowed.

    This function does NOT call broker adapters or open connections.

    Args:
        session_id: Unique session identifier for the recovered session.
        recovery_context: Structured persisted state from the previous
            session.
        config: Validated ``Settings`` instance for the new session.
        request_id: Optional trace identifier.

    Returns:
        ``LiveSession`` recovered session snapshot in ``ACTIVE`` or
        ``PAUSED`` status depending on recovery diagnostics.

    Raises:
        ValidationError: If ``session_id`` is empty, ``recovery_context``
            is not a dict, or config validation fails.
    """
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValidationError(
            "session_id must be a non-empty string.",
            code="INVALID_INPUT",
        )
    if not isinstance(recovery_context, dict):
        raise ValidationError(
            "recovery_context must be a dict.",
            code="INVALID_INPUT",
        )

    session_id = session_id.strip()
    validation_errors = validate_config(config)
    if validation_errors:
        raise ValidationError(
            "Live configuration is invalid during recovery: "
            + "; ".join(validation_errors),
            code="CONFIGURATION_ERROR",
        )

    now = datetime.now(UTC)
    has_unknowns = recovery_context.get("has_unknown_outcomes", False)
    has_reconciliation_pending = recovery_context.get(
        "reconciliation_pending", False
    )

    if has_unknowns or has_reconciliation_pending:
        status = LiveSessionStatus.PAUSED
        logger.warning(
            "live_session.recovery.paused_pending_review "
            "session_id=%r has_unknown_outcomes=%r "
            "reconciliation_pending=%r request_id=%r",
            session_id,
            has_unknowns,
            has_reconciliation_pending,
            request_id,
        )
    else:
        status = LiveSessionStatus.ACTIVE
        logger.info(
            "live_session.recovery.active "
            "session_id=%r request_id=%r",
            session_id,
            request_id,
        )

    recover_event = LiveSessionEvent(
        event_type="session_recovered",
        timestamp=now,
        details={
            "has_unknown_outcomes": has_unknowns,
            "reconciliation_pending": has_reconciliation_pending,
            "recovery_context_keys": list(recovery_context.keys()),
        },
        request_id=request_id,
    )

    return LiveSession(
        session_id=session_id,
        status=status,
        started_at=now,
        stopped_at=None,
        live_enabled=config.live_enabled,
        live_mode=config.live_mode,
        events=[recover_event],
        recovery_context=recovery_context,
        request_id=request_id,
    )


def get_live_session_status(
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Return the current live session status envelope.

    Returns a structured status envelope with session ID, status, live
    mode, and whether the session is accepting new requests. Never
    exposes secret values or raw broker payloads.

    Args:
        request_id: Optional trace identifier.

    Returns:
        Standard status envelope dict with keys:

        * ``status`` — ``'active'`` | ``'inactive'`` | status value
        * ``session_id`` — ``str | None``
        * ``live_enabled`` — ``bool | None``
        * ``live_mode`` — ``str | None``
        * ``started_at`` — ISO 8601 string | ``None``
        * ``accepting_requests`` — ``bool``
        * ``request_id`` — ``str | None``
    """
    if _active_session is None:
        return {
            "status": LiveSessionStatus.INACTIVE,
            "session_id": None,
            "live_enabled": None,
            "live_mode": None,
            "started_at": None,
            "accepting_requests": False,
            "request_id": request_id,
        }

    accepting = _active_session.status == LiveSessionStatus.ACTIVE
    started_at_iso = (
        _active_session.started_at.isoformat()
        if _active_session.started_at
        else None
    )
    return {
        "status": _active_session.status,
        "session_id": _active_session.session_id,
        "live_enabled": _active_session.live_enabled,
        "live_mode": _active_session.live_mode,
        "started_at": started_at_iso,
        "accepting_requests": accepting,
        "request_id": request_id,
    }
