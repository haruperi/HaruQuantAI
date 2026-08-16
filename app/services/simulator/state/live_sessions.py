"""Bounded in-process live what-if sessions over the deterministic engine.

A live session is a prepared run whose timeline is advanced in increments
instead of all at once. It exists so an analyst can walk a completed strategy
forward and ask "what if this had been different" without touching the
recorded run it started from.

Three properties are deliberate:

* **Sessions are not durable.** A session holds a live
  ``EventDrivenExecutionEngine`` with an open journal writer, which cannot be
  serialised. Rather than invent a persistence format for engine internals,
  sessions live in a bounded registry and are lost on restart. The registry is
  capped and sessions expire, so an abandoned exploration cannot pin memory.
  Official runs remain fully durable; only exploration is ephemeral.

* **A branch never mutates its parent.** Branching replays the parent's
  deterministic inputs from the first tick to the divergence point and then
  continues under the overridden request. The parent's engine is untouched, so
  a recorded outcome stays immutable — the property the original exclusion of
  live what-if protected. Because the branch is defined by its lineage rather
  than by a copied object, it is independently reproducible.

* **Branch results are advisory.** Each branch journals under its own run
  identity and is never published as an official ``SimulationResult``. A
  what-if answer is evidence for a human, not a recorded run.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING

from app.services.simulator.errors import SimulationError
from app.services.simulator.run.orchestrator import (
    RunContext,
    advance_run_timeline,
    prepare_run_context,
    submit_orders_before,
)
from app.utils import canonical_json, derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from app.services.simulator.run.contracts import (
        SimulationBacktestRequest,
        SimulationRunDependencies,
    )

logger = get_logger(__name__)

_MAX_LIVE_SESSIONS = 16
_LIVE_SESSION_TTL = timedelta(seconds=1_800)
_MAX_STEP_TICKS = 10_000


class _LiveSession:
    """One in-process what-if session bound to a prepared run context."""

    __slots__ = (
        "branch_of",
        "context",
        "created_at",
        "cursor",
        "divergence_index",
        "last_used_at",
        "receipts",
        "request",
        "run_id",
        "session_id",
        "unsent",
    )

    def __init__(
        self,
        session_id: str,
        run_id: str,
        request: SimulationBacktestRequest,
        context: RunContext,
        *,
        branch_of: str | None = None,
        divergence_index: int | None = None,
    ) -> None:
        """Bind one prepared context to a session identity.

        Args:
            session_id: Session identity.
            run_id: Journal run identity for this session.
            request: Receiver-owned backtest request driving the session.
            context: Prepared deterministic run context.
            branch_of: Parent session identity when this is a branch.
            divergence_index: Tick index at which this branch diverged.
        """
        now = utc_now()
        self.session_id = session_id
        self.run_id = run_id
        self.request = request
        self.context = context
        self.branch_of = branch_of
        self.divergence_index = divergence_index
        self.cursor = 0
        self.unsent = list(context.order_intents)
        self.receipts: list[object] = []
        self.created_at = now
        self.last_used_at = now


_SESSIONS: dict[str, _LiveSession] = {}


def _session_identity(
    request_id: str, *, parent: str | None, divergence: int | None
) -> str:
    """Derive one deterministic live-session identity.

    Uses the same stable-identity convention as playback sessions rather than a
    random identifier, so a session's identity is reproducible from its lineage.

    Args:
        request_id: Operation request identifier.
        parent: Parent session identity when branching.
        divergence: Tick index at which a branch diverged.

    Returns:
        Stable session identifier.
    """
    return derive_stable_id(
        "id",
        canonical_json(
            {
                "kind": "simulation_live_session",
                "request_id": request_id,
                "parent": parent,
                "divergence": divergence,
            }
        ),
    )


def _evict_expired(now: datetime) -> None:
    """Drop sessions whose idle window has elapsed.

    Args:
        now: Current UTC instant.
    """
    expired = [
        key
        for key, session in _SESSIONS.items()
        if now - session.last_used_at > _LIVE_SESSION_TTL
    ]
    for key in expired:
        logger.info("Expiring idle live Simulation session %s", key)
        del _SESSIONS[key]


def _require(session_id: str) -> _LiveSession:
    """Return one live session or fail closed.

    Args:
        session_id: Session identity.

    Returns:
        The bound live session.

    Raises:
        SimulationError: If the session is unknown or has expired.
    """
    _evict_expired(utc_now())
    session = _SESSIONS.get(session_id)
    if session is None:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION",
            "Live session is unknown or has expired",
        )
    session.last_used_at = utc_now()
    return session


def _project(session: _LiveSession) -> Mapping[str, object]:
    """Build one immutable non-secret session projection.

    Args:
        session: Live session to project.

    Returns:
        Detached read-only session state.
    """
    total = len(session.context.timeline)
    return MappingProxyType(
        {
            "session_id": session.session_id,
            "run_id": session.run_id,
            "cursor": session.cursor,
            "tick_count": total,
            "complete": session.cursor >= total,
            "receipt_count": len(session.receipts),
            "pending_intents": len(session.unsent),
            "branch_of": session.branch_of,
            "divergence_index": session.divergence_index,
            "advisory": True,
        }
    )


def create_live_simulation_session(
    request: SimulationBacktestRequest,
    dependencies: SimulationRunDependencies,
    *,
    request_id: str,
) -> Mapping[str, object]:
    """Open one bounded live what-if session at the start of a timeline.

    Args:
        request: Receiver-owned backtest request.
        dependencies: Explicit Simulator run dependency bundle.
        request_id: Operation request identifier.

    Session identity is derived from the request, so opening twice with the
    same ``request_id`` re-opens the same session rather than silently starting
    a second engine over the same work. That mirrors how playback sessions
    behave and makes the operation safely retryable.

    Returns:
        Immutable session state; positioned before the first tick on first open.

    Raises:
        SimulationError: If the session registry is at capacity.
    """
    logger.info("Opening live Simulation session for %s", request_id)
    _evict_expired(utc_now())
    session_id = _session_identity(request_id, parent=None, divergence=None)
    existing = _SESSIONS.get(session_id)
    if existing is not None:
        existing.last_used_at = utc_now()
        return _project(existing)
    if len(_SESSIONS) >= _MAX_LIVE_SESSIONS:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION",
            "Live session capacity reached; close a session before opening another",
        )
    run_id = f"whatif-{session_id}"
    context = prepare_run_context(request, dependencies, run_id)
    session = _LiveSession(session_id, run_id, request, context)
    _SESSIONS[session_id] = session
    return _project(session)


def step_live_simulation(session_id: str, ticks: int) -> Mapping[str, object]:
    """Advance one live session by a bounded number of ticks.

    Args:
        session_id: Session identity.
        ticks: Positive tick count to advance.

    Returns:
        Immutable session state after advancing.

    Raises:
        SimulationError: If the session is unknown, expired, or the tick count
            is not a bounded positive integer.
    """
    if ticks < 1 or ticks > _MAX_STEP_TICKS:
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            "Step size must be a positive bounded tick count",
        )
    session = _require(session_id)
    context = session.context
    if session.cursor == 0:
        _submit_due_before_first_tick(session)
    session.cursor = advance_run_timeline(
        context.engine,
        context.timeline,
        session.unsent,
        session.receipts,
        start_index=session.cursor,
        max_ticks=ticks,
    )
    return _project(session)


def _submit_due_before_first_tick(session: _LiveSession) -> None:
    """Submit intents created before the timeline opens.

    Mirrors the official run, which drains pre-timeline intents before the
    first tick so a session that steps and a run that completes see the same
    order sequence.

    Args:
        session: Live session about to execute its first tick.
    """
    submit_orders_before(
        session.context.engine,
        session.unsent,
        session.receipts,
        session.context.timeline[0].timestamp,
    )


def read_live_simulation_state(session_id: str) -> Mapping[str, object]:
    """Return the current state of one live session.

    Args:
        session_id: Session identity.

    Returns:
        Immutable session state.

    Raises:
        SimulationError: If the session is unknown or has expired.
    """
    return _project(_require(session_id))


def branch_live_simulation(
    session_id: str,
    overrides: Mapping[str, object],
    dependencies: SimulationRunDependencies,
    *,
    request_id: str,
) -> Mapping[str, object]:
    """Fork one session into an independent what-if branch.

    The branch replays the parent's deterministic inputs from the first tick to
    the parent's current cursor, then continues under the overridden request.
    The parent is never mutated, and the branch journals under its own run
    identity, so neither can be mistaken for the other.

    Args:
        session_id: Parent session identity.
        overrides: Field overrides applied to the parent's request.
        dependencies: Explicit Simulator run dependency bundle.
        request_id: Operation request identifier.

    Returns:
        Immutable state of the new branch, replayed to the divergence point.

    Raises:
        SimulationError: If the parent is unknown, the registry is at capacity,
            or the overrides do not produce a valid request.
    """
    logger.info("Branching live Simulation session %s for %s", session_id, request_id)
    parent = _require(session_id)
    _evict_expired(utc_now())
    if len(_SESSIONS) >= _MAX_LIVE_SESSIONS:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION",
            "Live session capacity reached; close a session before branching",
        )
    divergence = parent.cursor
    branched_request = _apply_overrides(parent.request, overrides)
    branch_id = _session_identity(
        request_id, parent=parent.session_id, divergence=divergence
    )
    run_id = f"whatif-{branch_id}"
    context = prepare_run_context(branched_request, dependencies, run_id)
    branch = _LiveSession(
        branch_id,
        run_id,
        branched_request,
        context,
        branch_of=parent.session_id,
        divergence_index=divergence,
    )
    if divergence > 0:
        _submit_due_before_first_tick(branch)
        branch.cursor = advance_run_timeline(
            context.engine,
            context.timeline,
            branch.unsent,
            branch.receipts,
            start_index=0,
            max_ticks=divergence,
        )
    _SESSIONS[branch_id] = branch
    return _project(branch)


def _apply_overrides(
    request: SimulationBacktestRequest, overrides: Mapping[str, object]
) -> SimulationBacktestRequest:
    """Build one overridden copy of a receiver-owned request.

    Args:
        request: Parent backtest request.
        overrides: Field overrides to apply.

    Returns:
        New request carrying the overrides.

    Raises:
        SimulationError: If the request cannot be copied with the overrides.
    """
    try:
        return request.model_copy(update=dict(overrides))
    except Exception as error:
        raise SimulationError(
            "SIM_INVALID_CONFIG",
            "What-if overrides do not produce a valid request",
        ) from error


def close_live_simulation_session(session_id: str) -> Mapping[str, object]:
    """Close one live session and release its engine.

    Args:
        session_id: Session identity.

    Returns:
        Immutable final state of the closed session.

    Raises:
        SimulationError: If the session is unknown or has expired.
    """
    session = _require(session_id)
    state = _project(session)
    del _SESSIONS[session_id]
    logger.info("Closed live Simulation session %s", session_id)
    return state


def reset_live_simulation_sessions() -> None:
    """Drop every live session.

    Test support and shutdown hook; production callers close their own
    sessions. Exposed because an abandoned registry would otherwise outlive a
    test module and leak engine state between cases.
    """
    _SESSIONS.clear()


__all__ = (
    "branch_live_simulation",
    "close_live_simulation_session",
    "create_live_simulation_session",
    "read_live_simulation_state",
    "reset_live_simulation_sessions",
    "step_live_simulation",
)
