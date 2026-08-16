"""Function-only facade for the internal Trading live session."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.services.trading.live.session import LiveSession

type StandardResponse[T] = Any
type JsonValue = Any


def create_live_session(**values: object) -> LiveSession:
    """Construct one internal live/demo session.

    Args:
        **values: Session dependency values.

    Returns:
        Internal live/demo session.
    """
    return LiveSession(**cast("Any", values))


async def start_live_session(
    session: LiveSession,
    config: Mapping[str, JsonValue],
    evidence: Mapping[str, JsonValue],
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Start a live/demo session through its validated lifecycle.

    Args:
        session: Internal session returned by :func:`create_live_session`.
        config: Runtime configuration.
        evidence: Startup authority evidence.

    Returns:
        Canonical startup response.
    """
    return await session.start(config, evidence)


def get_live_session_status(
    session: LiveSession,
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Return current live/demo session status.

    Args:
        session: Internal session returned by :func:`create_live_session`.

    Returns:
        Canonical status response.
    """
    return session.status()


async def stop_live_session(
    session: LiveSession,
) -> StandardResponse[Mapping[str, JsonValue]]:
    """Stop a live/demo session through its safe shutdown lifecycle.

    Args:
        session: Internal session returned by :func:`create_live_session`.

    Returns:
        Canonical shutdown response.
    """
    return await session.stop()


def is_live_session_started(session: LiveSession) -> bool:
    """Return whether a live/demo session has started.

    Args:
        session: Internal session returned by :func:`create_live_session`.

    Returns:
        True when startup completed.
    """
    return session.started


def is_live_session_admission_enabled(session: LiveSession) -> bool:
    """Return whether a live/demo session admits new actions.

    Args:
        session: Internal session returned by :func:`create_live_session`.

    Returns:
        True when new actions may enter the session.
    """
    return session.admission_enabled


def is_live_session_reconciliation_ready(session: LiveSession) -> bool:
    """Return whether startup reconciliation is ready.

    Args:
        session: Internal session returned by :func:`create_live_session`.

    Returns:
        True when reconciliation authority is ready.
    """
    return session.reconciliation_ready


__all__ = [
    "create_live_session",
    "get_live_session_status",
    "is_live_session_admission_enabled",
    "is_live_session_reconciliation_ready",
    "is_live_session_started",
    "start_live_session",
    "stop_live_session",
]
