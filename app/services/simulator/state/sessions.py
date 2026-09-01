"""Durable lifecycle and frame delivery for Simulation playback sessions."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from datetime import timedelta
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id, generate_id
from app.kernel.serialization import canonical_json
from app.kernel.time import format_utc_timestamp, parse_utc_timestamp, utc_now
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal.playback import stream_journal_events
from app.services.simulator.persistence import (
    create_session_record,
    create_simulator_persistence_store,
    read_completed_run_record,
    read_session_record,
    update_session_record,
)

if TYPE_CHECKING:
    from app.services.simulator.journal.contracts import JournalEvent

logger = get_logger(__name__)

_SESSION_TTL = timedelta(seconds=3_600)


def _store() -> object:
    """Create one private persistence handle for session records.

    Returns:
        Opaque Simulator persistence handle.
    """
    return create_simulator_persistence_store(lambda value: value)


def _immutable(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a detached immutable session projection."""
    return MappingProxyType(dict(value))


def create_simulation_session(
    run_id: str,
    *,
    request_id: str,
) -> Mapping[str, object]:
    """Create one playback session for a completed canonical run.

    Args:
        run_id: Completed Simulation run identity.
        request_id: Trace identifier for persistence and stable session identity.

    Returns:
        Immutable persisted playback-session projection.

    Raises:
        SimulationError: If the run is incomplete or persistence fails.
    """
    logger.info("Creating Simulation journal playback session")
    if not run_id or run_id != run_id.strip() or not request_id:
        raise SimulationError("SIM_INVALID_CONFIG", "Session identity is invalid")
    store = _store()
    try:
        completed = read_completed_run_record(store, run_id)
    except (KeyError, TypeError, ValueError) as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Completed run lookup failed"
        ) from error
    if not completed:
        raise SimulationError(
            "SIM_SESSION_NOT_FOUND", "Completed Simulation run was not found"
        )
    try:
        created_at = utc_now()
        value: Mapping[str, object] = {
            "session_id": derive_stable_id(
                "id",
                canonical_json(
                    {
                        "kind": "simulation_playback_session",
                        "request_id": request_id,
                        "run_id": run_id,
                    }
                ),
            ),
            "run_id": run_id,
            "status": "active",
            "cursor": -1,
            "created_at": format_utc_timestamp(created_at),
            "expires_at": format_utc_timestamp(created_at + _SESSION_TTL),
        }
        create_session_record(store, value, request_id=request_id)
        return _immutable(value)
    except SimulationError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Playback session creation failed"
        ) from error


def read_simulation_session(session_id: str) -> Mapping[str, object] | None:
    """Read one playback session and materialize expiry truth.

    Args:
        session_id: Stable playback-session identity.

    Returns:
        Immutable session projection or ``None`` when absent.

    Raises:
        SimulationError: If stored session material is invalid.
    """
    logger.info("Reading Simulation journal playback session")
    if not session_id or session_id != session_id.strip():
        raise SimulationError("SIM_INVALID_CONFIG", "Session identity is invalid")
    store = _store()
    try:
        row = read_session_record(store, session_id)
        if row is None:
            return None
        value = dict(row)
        if value["status"] == "active" and utc_now() >= parse_utc_timestamp(
            str(value["expires_at"])
        ):
            value["status"] = "expired"
        return _immutable(value)
    except SimulationError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Stored playback session is invalid"
        ) from error


def _journal_path(dependencies: object, run_id: str) -> Path:
    """Resolve one finalized journal inside the approved artifact root.

    Returns:
        Safe finalized journal path.

    Raises:
        SimulationError: If dependencies or the resolved path are unsafe.
    """
    artifact_root = getattr(dependencies, "artifact_root", None)
    if not isinstance(artifact_root, Path):
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Simulation playback dependencies are unavailable"
        )
    root = artifact_root.resolve()
    path = (root / run_id / "journal.jsonl").resolve()
    if root not in path.parents:
        raise SimulationError("SIM_INVALID_CONFIG", "Journal path is invalid")
    return path


async def stream_simulation_session_frames(
    session_id: str,
    *,
    resume_after: int | None,
    dependencies: object,
) -> AsyncIterator[JournalEvent]:
    """Yield one completed run's validated journal frames.

    Args:
        session_id: Stable playback-session identity.
        resume_after: Optional client-observed journal sequence.
        dependencies: Opaque canonical Simulation dependency bundle.

    Yields:
        Ordered journal events after the effective cursor.

    Raises:
        SimulationError: If the session, cursor, dependencies, or journal fail.
    """
    session = read_simulation_session(session_id)
    if session is None:
        raise SimulationError("SIM_SESSION_NOT_FOUND", "Playback session was not found")
    if session["status"] == "expired":
        update_session_record(
            _store(),
            session_id=session_id,
            status="expired",
            cursor=int(cast("int", session["cursor"])),
            request_id=generate_id("req"),
        )
        raise SimulationError("SIM_SESSION_EXPIRED", "Playback session has expired")
    stored_cursor = int(cast("int", session["cursor"]))
    effective_cursor = stored_cursor if resume_after is None else resume_after
    store = _store()
    delivered_cursor = stored_cursor
    async for event in stream_journal_events(
        _journal_path(dependencies, str(session["run_id"])),
        str(session["run_id"]),
        resume_after=effective_cursor,
    ):
        yield event
        delivered_cursor = max(delivered_cursor, event.sequence)
        if not update_session_record(
            store,
            session_id=session_id,
            status="active",
            cursor=delivered_cursor,
            request_id=generate_id("req"),
        ):
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Playback cursor update failed"
            )
    if not update_session_record(
        store,
        session_id=session_id,
        status="completed",
        cursor=delivered_cursor,
        request_id=generate_id("req"),
    ):
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Playback completion update failed"
        )


__all__ = [
    "create_simulation_session",
    "read_simulation_session",
    "stream_simulation_session_frames",
]
