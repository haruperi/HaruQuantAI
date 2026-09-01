"""Bounded in-process live what-if sessions over the deterministic engine.

A live session is a prepared run whose timeline is advanced in increments
instead of all at once. It exists so an analyst can walk a completed strategy
forward and ask "what if this had been different" without touching the
recorded run it started from.

Three properties are deliberate:

* **Practice sessions can be durable without serialising the engine.** The
  immutable request, replay cursor, canonical state digest, and cursor-bound
  manual intents are persisted. Restart creates a distinct recovery journal,
  rebuilds from the exact dataset revision, and remains exposure-blocked until
  digest verification and explicit rearm. Ephemeral advisory sessions remain
  available to bounded internal callers that do not request durability.

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
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id, generate_id
from app.kernel.serialization import canonical_digest, canonical_json
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.simulator.errors import SimulationError, unwrap_simulation_response
from app.services.simulator.execution import SimTrader
from app.services.simulator.persistence import (
    append_interactive_intent_and_checkpoint,
    create_interactive_session_record,
    create_simulator_persistence_store,
    read_interactive_intent_records,
    read_interactive_session_record,
    update_interactive_session_record,
)
from app.services.simulator.run.orchestrator import (
    RunContext,
    advance_run_timeline,
    prepare_run_context,
    submit_orders_before,
)

if TYPE_CHECKING:
    from app.services.simulator.run.contracts import (
        SimulationBacktestRequest,
        SimulationRunDependencies,
    )

logger = get_logger(__name__)

_MAX_LIVE_SESSIONS = 16
_LIVE_SESSION_TTL = timedelta(seconds=1_800)
_MAX_STEP_TICKS = 10_000
_MAX_SEEK_TICKS = 100_000
DEFAULT_VIEWPORT_BEFORE = 300
MAX_VIEWPORT_BEFORE = 5_000
VIEWPORT_AFTER = 0

COMMAND_TYPES: tuple[str, ...] = (
    "submit_order",
    "modify_pending_order",
    "cancel_pending_order",
    "close_position",
    "reduce_position",
    "close_all_practice_exposure",
)


class _LiveSession:
    """One in-process what-if session bound to a prepared run context."""

    __slots__ = (
        "branch_of",
        "context",
        "created_at",
        "cursor",
        "divergence_index",
        "durable",
        "finalized_at",
        "last_used_at",
        "receipts",
        "recovery_generation",
        "recovery_run_id",
        "recovery_state",
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
        durable: bool = False,
    ) -> None:
        """Bind one prepared context to a session identity.

        Args:
            session_id: Session identity.
            run_id: Journal run identity for this session.
            request: Receiver-owned backtest request driving the session.
            context: Prepared deterministic run context.
            branch_of: Parent session identity when this is a branch.
            divergence_index: Tick index at which this branch diverged.
            durable: Whether every cursor and manual intent must be persisted.
        """
        now = utc_now()
        self.session_id = session_id
        self.run_id = run_id
        self.request = request
        self.context = context
        self.branch_of = branch_of
        self.divergence_index = divergence_index
        self.durable = durable
        self.finalized_at: datetime | None = None
        self.recovery_generation = 0
        self.recovery_run_id: str | None = None
        self.recovery_state = "running"
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


def _permitted_actions(session: _LiveSession) -> tuple[str, ...]:
    """Return the actions this session currently accepts.

    A finalized session is sealed: it may still be read and closed, but it
    accepts no further advance, command, or branch. A recovered session accepts
    only rearm until an operator approves it explicitly.

    Args:
        session: Live session to describe.

    Returns:
        Ordered tuple of permitted action names.
    """
    if session.finalized_at is not None:
        return ("read", "reproduce", "close")
    if session.recovery_state != "running":
        return ("read", "rearm", "close")
    if session.cursor >= len(session.context.timeline):
        return ("read", "finalize", "branch", "close")
    return ("read", "step", "seek", "command", "branch", "finalize", "close")


def _require_active(session_id: str) -> _LiveSession:
    """Return one live session that still accepts mutating operations.

    Args:
        session_id: Session identity.

    Returns:
        The bound live session.

    Raises:
        SimulationError: `SIMULATION_SESSION_FINALIZED` when the session was
            sealed, or `SIM_RECOVERY_STATE_INVALID` when it awaits rearm.
    """
    session = _require(session_id)
    if session.finalized_at is not None:
        raise SimulationError(
            "SIMULATION_SESSION_FINALIZED",
            "Finalized session accepts no further mutation",
        )
    if session.recovery_state != "running":
        raise SimulationError(
            "SIM_RECOVERY_STATE_INVALID", "Recovered session requires explicit rearm"
        )
    return session


def _project(session: _LiveSession) -> Mapping[str, object]:
    """Build one immutable non-secret session projection.

    Args:
        session: Live session to project.

    Returns:
        Detached read-only session state.
    """
    total = len(session.context.timeline)
    replay_timestamp = (
        None
        if session.cursor == 0
        else session.context.timeline[session.cursor - 1].timestamp
    )
    account_state = unwrap_simulation_response(
        session.context.engine.snapshot(),
        operation="simulation.state.live_session.snapshot",
    )
    return MappingProxyType(
        {
            "session_id": session.session_id,
            "run_id": session.run_id,
            "cursor": session.cursor,
            "replay_timestamp": replay_timestamp,
            "dataset_ref": session.request.data_ref,
            "dataset_revision": session.request.data_version,
            "dataset_hash": session.request.data_hash,
            "tick_count": total,
            "complete": session.cursor >= total,
            "receipt_count": len(session.receipts),
            "pending_intents": len(session.unsent),
            "branch_of": session.branch_of,
            "divergence_index": session.divergence_index,
            "advisory": True,
            "durable": session.durable,
            "recovery_state": session.recovery_state,
            "exposure_blocked": session.recovery_state != "running"
            or session.finalized_at is not None,
            "finalized": session.finalized_at is not None,
            "finalized_at": (
                None
                if session.finalized_at is None
                else format_utc_timestamp(session.finalized_at)
            ),
            "permitted_actions": _permitted_actions(session),
            "account_state": account_state,
        }
    )


def _store() -> object:
    """Create one opaque Simulator persistence handle.

    Returns:
        Private handle delegating transactions through Data.
    """
    return create_simulator_persistence_store(lambda value: value)


def _state_hash(session: _LiveSession) -> str:
    """Hash the complete reproducible interactive-session projection.

    Returns:
        Canonical SHA-256 state digest.
    """
    projected = _project(session)
    return canonical_digest(
        {
            "cursor": session.cursor,
            "dataset_ref": projected["dataset_ref"],
            "dataset_revision": projected["dataset_revision"],
            "dataset_hash": projected["dataset_hash"],
            "tick_count": projected["tick_count"],
            "receipt_count": projected["receipt_count"],
            "pending_intents": projected["pending_intents"],
            "account_state": projected["account_state"],
        }
    )


def _checkpoint(session: _LiveSession, *, request_id: str) -> None:
    """Persist one durable cursor and state digest.

    Args:
        session: Durable interactive session.
        request_id: Trace identity for the Data transaction.

    Raises:
        SimulationError: If the checkpoint cannot be confirmed.
    """
    if not session.durable:
        return
    now = format_utc_timestamp(utc_now())
    status = (
        "completed" if session.cursor >= len(session.context.timeline) else "running"
    )
    if not update_interactive_session_record(
        _store(),
        session_id=session.session_id,
        cursor=session.cursor,
        status=status,
        state_hash=_state_hash(session),
        recovery_generation=session.recovery_generation,
        recovery_run_id=session.recovery_run_id,
        updated_at=now,
        request_id=request_id,
    ):
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED", "Interactive session checkpoint failed"
        )


async def submit_live_simulation_order(session_id: str, intent: object) -> object:
    """Submit one unchanged Trading intent to an active historical session.

    Args:
        session_id: Active dataset-bound session identity.
        intent: Trading-owned approved OrderIntent.

    Returns:
        Trading-owned execution receipt produced by the session engine.

    Raises:
        SimulationError: If the session is absent, complete, or the intent is
            not bound to the selected session.
    """
    session = _require_active(session_id)
    if session.cursor >= len(session.context.timeline):
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION", "Completed session cannot accept orders"
        )
    if getattr(intent, "simulation_session_id", None) != session_id:
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Order is not bound to the active session"
        )
    if session.durable:
        now = format_utc_timestamp(utc_now())
        material = cast("Any", intent).model_dump(mode="json", warnings=False)
        accepted = append_interactive_intent_and_checkpoint(
            _store(),
            intent={
                "session_id": session.session_id,
                "sequence": len(session.receipts),
                "accepted_cursor": session.cursor,
                "intent": material,
                "intent_hash": canonical_digest(material),
                "created_at": now,
            },
            checkpoint={
                "session_id": session.session_id,
                "cursor": session.cursor,
                "status": "running",
                "state_hash": _state_hash(session),
                "recovery_generation": session.recovery_generation,
                "recovery_run_id": session.recovery_run_id,
                "updated_at": now,
            },
            request_id=str(getattr(intent, "request_id", generate_id("req"))),
        )
        if not accepted:
            raise SimulationError(
                "SIM_PERSISTENCE_FAILED", "Interactive intent checkpoint failed"
            )
    trader = SimTrader(session.context.engine)
    response = await trader.submit_order(intent)
    receipt = unwrap_simulation_response(
        response,
        operation="simulation.state.submit_live_simulation_order",
    )
    session.receipts.append(receipt)
    _checkpoint(
        session,
        request_id=str(getattr(intent, "request_id", generate_id("req"))),
    )
    return receipt


def create_live_simulation_session(
    request: SimulationBacktestRequest,
    dependencies: SimulationRunDependencies,
    *,
    request_id: str,
    durable: bool = False,
) -> Mapping[str, object]:
    """Open one bounded live what-if session at the start of a timeline.

    Args:
        request: Receiver-owned backtest request.
        dependencies: Explicit Simulator run dependency bundle.
        request_id: Operation request identifier.
        durable: Persist the request, cursor, state hash, and manual intents.

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
    session = _LiveSession(session_id, run_id, request, context, durable=durable)
    _SESSIONS[session_id] = session
    if durable:
        now = format_utc_timestamp(utc_now())
        create_interactive_session_record(
            _store(),
            {
                "session_id": session_id,
                "run_id": run_id,
                "request": request.model_dump(mode="json", warnings=False),
                "cursor": 0,
                "status": "running",
                "state_hash": _state_hash(session),
                "created_at": now,
                "updated_at": now,
            },
            request_id=request_id,
        )
    return _project(session)


def restore_live_simulation_session(
    session_id: str,
    dependencies: SimulationRunDependencies,
    *,
    request_id: str,
) -> Mapping[str, object]:
    """Reconstruct one durable historical session and leave exposure blocked.

    The immutable dataset revision is loaded again through the ordinary run
    dependency, cursor-bound manual intents are reapplied, and the resulting
    state must match the persisted digest. A distinct recovery run identity
    preserves the original journal.

    Args:
        session_id: Durable interactive session identity.
        dependencies: Exact Simulator run dependency bundle.
        request_id: Recovery trace identity.

    Returns:
        Verified projection requiring explicit rearm.

    Raises:
        SimulationError: If persistence, replay, or state integrity fails.
    """
    from app.services.simulator.run.contracts import SimulationBacktestRequest
    from app.services.trading import parse_order_intent

    record = read_interactive_session_record(_store(), session_id)
    if record is None or not isinstance(record.get("request"), Mapping):
        raise SimulationError(
            "SIM_SESSION_NOT_FOUND", "Durable interactive session was not found"
        )
    generation = int(str(record["recovery_generation"])) + 1
    recovery_run_id = f"recovery-{session_id}-{generation}"
    now = format_utc_timestamp(utc_now())
    if not update_interactive_session_record(
        _store(),
        session_id=session_id,
        cursor=int(str(record["cursor"])),
        status="recovery_locked",
        state_hash=str(record["state_hash"]),
        recovery_generation=generation,
        recovery_run_id=recovery_run_id,
        updated_at=now,
        request_id=request_id,
    ):
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Recovery lock failed")
    request = SimulationBacktestRequest.model_validate(record["request"])
    context = prepare_run_context(request, dependencies, recovery_run_id)
    session = _LiveSession(
        session_id,
        recovery_run_id,
        request,
        context,
        durable=True,
    )
    session.recovery_generation = generation
    session.recovery_run_id = recovery_run_id
    target_cursor = int(str(record["cursor"]))
    persisted = read_interactive_intent_records(_store(), session_id)
    by_cursor: dict[int, list[Mapping[str, object]]] = {}
    for row in persisted:
        by_cursor.setdefault(int(str(row["accepted_cursor"])), []).append(row)
    if target_cursor > 0:
        _submit_due_before_first_tick(session)
    for cursor in range(target_cursor + 1):
        for row in by_cursor.get(cursor, []):
            material = row.get("intent")
            if not isinstance(material, Mapping):
                raise SimulationError(
                    "SIM_INTEGRITY_FAILURE", "Persisted manual intent is malformed"
                )
            intent = parse_order_intent(material)
            receipt = unwrap_simulation_response(
                context.engine.submit_order(intent),
                operation="simulation.state.restore_live_session.intent",
            )
            session.receipts.append(receipt)
        if cursor < target_cursor:
            session.cursor = advance_run_timeline(
                context.engine,
                context.timeline,
                session.unsent,
                session.receipts,
                start_index=session.cursor,
                max_ticks=1,
            )
    if _state_hash(session) != record["state_hash"]:
        raise SimulationError(
            "SIM_INTEGRITY_FAILURE", "Interactive session reconstruction mismatched"
        )
    session.recovery_state = "verified"
    _SESSIONS[session_id] = session
    update_interactive_session_record(
        _store(),
        session_id=session_id,
        cursor=session.cursor,
        status="verified",
        state_hash=_state_hash(session),
        recovery_generation=generation,
        recovery_run_id=recovery_run_id,
        updated_at=format_utc_timestamp(utc_now()),
        request_id=request_id,
    )
    return _project(session)


def rearm_live_simulation_session(
    session_id: str, *, approved: bool, request_id: str
) -> Mapping[str, object]:
    """Explicitly rearm one verified reconstructed historical session.

    Args:
        session_id: Verified session identity.
        approved: Deterministic operator approval.
        request_id: Rearm trace identity.

    Returns:
        Running durable session projection.

    Raises:
        SimulationError: If verification or explicit approval is absent.
    """
    session = _require(session_id)
    if not approved or session.recovery_state != "verified":
        raise SimulationError(
            "SIM_RECOVERY_STATE_INVALID", "Verified explicit rearm is required"
        )
    session.recovery_state = "running"
    _checkpoint(session, request_id=request_id)
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
    session = _require_active(session_id)
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
    _checkpoint(session, request_id=generate_id("req"))
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


def list_live_simulation_sessions() -> tuple[Mapping[str, object], ...]:
    """Return every live session this process currently holds.

    Expired sessions are evicted first, so the listing describes sessions that
    can actually be acted on rather than identities that would fail on use.

    Returns:
        Ordered tuple of immutable session projections, oldest first.
    """
    _evict_expired(utc_now())
    return tuple(
        _project(session)
        for session in sorted(_SESSIONS.values(), key=lambda item: item.created_at)
    )


def read_live_simulation_viewport(
    session_id: str, *, before: int = DEFAULT_VIEWPORT_BEFORE
) -> Mapping[str, object]:
    """Return a bounded backwards-only market viewport for one live session.

    The viewport ends at the authoritative cursor and never includes a row the
    session has not reached. A visual practice surface that could see even one
    future bar would no longer be practising the decision it claims to.

    Args:
        session_id: Session identity.
        before: Number of rows to return ending at the cursor.

    Returns:
        Immutable viewport carrying only rows at or before the cursor.

    Raises:
        SimulationError: If the session is unknown, or `SIM_INVALID_CONFIG`
            when the row count is outside the bounded range.
    """
    if before < 1 or before > MAX_VIEWPORT_BEFORE:
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Viewport row count is outside the bounded range"
        )
    session = _require(session_id)
    timeline = session.context.timeline
    end = session.cursor
    start = max(0, end - before)
    rows = tuple(
        MappingProxyType(
            {
                "timestamp": getattr(tick, "timestamp", None),
                "bid": getattr(tick, "bid", None),
                "ask": getattr(tick, "ask", None),
                "volume": getattr(tick, "volume", None),
                "sequence": getattr(tick, "sequence", index),
                "forming": False,
            }
        )
        for index, tick in enumerate(timeline[start:end], start=start)
    )
    return MappingProxyType(
        {
            "session_id": session.session_id,
            "cursor": end,
            "before": before,
            "after": VIEWPORT_AFTER,
            "tick_count": len(timeline),
            "rows": rows,
        }
    )


def seek_live_simulation(session_id: str, target_cursor: int) -> Mapping[str, object]:
    """Advance one live session forward to an absolute cursor.

    Seeking is forward-only. A simulation that could move backwards would let a
    later decision be taken with knowledge of an outcome that has already been
    observed, so a target behind the current cursor is refused rather than
    silently reinterpreted as a branch.

    Args:
        session_id: Session identity.
        target_cursor: Absolute tick index to advance to.

    Returns:
        Immutable session state after advancing.

    Raises:
        SimulationError: `SIMULATION_SEEK_REWIND_FORBIDDEN` for a target behind
            the cursor, `SIMULATION_SEEK_LIMIT_EXCEEDED` for a delta above the
            bound, or `SIM_INVALID_CONFIG` for a target beyond the timeline.
    """
    session = _require_active(session_id)
    total = len(session.context.timeline)
    if target_cursor < session.cursor:
        raise SimulationError(
            "SIMULATION_SEEK_REWIND_FORBIDDEN",
            "Seek target is behind the authoritative cursor",
        )
    delta = target_cursor - session.cursor
    if delta > _MAX_SEEK_TICKS:
        raise SimulationError(
            "SIMULATION_SEEK_LIMIT_EXCEEDED",
            "Seek distance exceeds the bounded tick limit",
        )
    if target_cursor > total:
        raise SimulationError(
            "SIM_INVALID_CONFIG", "Seek target is beyond the session timeline"
        )
    if delta == 0:
        return _project(session)

    context = session.context
    if session.cursor == 0:
        _submit_due_before_first_tick(session)
    session.cursor = advance_run_timeline(
        context.engine,
        context.timeline,
        session.unsent,
        session.receipts,
        start_index=session.cursor,
        max_ticks=delta,
    )
    _checkpoint(session, request_id=generate_id("req"))
    return _project(session)


def _decimal_or_none(value: object) -> Decimal | None:
    """Coerce one supplied level to an exact decimal.

    Args:
        value: Candidate level.

    Returns:
        Exact decimal, or None when the caller supplied no level.

    Raises:
        SimulationError: `SIM_INVALID_PRICE` when the level cannot be read
            exactly.
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError) as error:
        raise SimulationError(
            "SIM_INVALID_PRICE", "Command level is not an exact decimal"
        ) from error


def _require_command_field(command: Mapping[str, object], field: str) -> object:
    """Return one required command field.

    Args:
        command: Manual command mapping.
        field: Required field name.

    Returns:
        The supplied field value.

    Raises:
        SimulationError: `SIM_INVALID_CONFIG` when the field is absent.
    """
    value = command.get(field)
    if value is None:
        raise SimulationError(
            "SIM_INVALID_CONFIG", f"Command requires the {field} field"
        )
    return value


def _close_all_practice_exposure(trader: SimTrader) -> list[object]:
    """Close every open practice position at the authoritative tick.

    Args:
        trader: Session-bound simulated trading facade.

    Returns:
        Ordered close evidence, one entry per closed position.
    """
    snapshot = unwrap_simulation_response(
        trader.snapshot(),
        operation="simulation.state.execute_live_simulation_command.snapshot",
    )
    positions = cast("tuple[Mapping[str, object], ...]", snapshot.get("positions", ()))
    closed: list[object] = []
    for position in positions:
        volume = Decimal(str(position["volume"]))
        if volume <= 0:
            continue
        closed.append(
            unwrap_simulation_response(
                trader.close_position(str(position["position_id"]), volume),
                operation="simulation.state.execute_live_simulation_command",
            )
        )
    return closed


async def execute_live_simulation_command(
    session_id: str, command: Mapping[str, object]
) -> Mapping[str, object]:
    """Execute one manual command against an active practice session.

    Every command resolves to an engine operation that produces a real receipt.
    Nothing here fabricates a fill: a command the engine refuses raises, and a
    command that changes only order levels returns a receipt with no filled
    quantity.

    Args:
        session_id: Active session identity.
        command: Manual command carrying a supported ``command`` discriminator.

    Returns:
        Mapping of the owner receipt evidence and the refreshed session state.

    Raises:
        SimulationError: `SIM_UNSUPPORTED_OPERATION` for an unknown
            discriminator or a completed session, `SIM_INVALID_CONFIG` for a
            missing field, or any engine code raised while executing.
    """
    session = _require_active(session_id)
    discriminator = command.get("command")
    if discriminator not in COMMAND_TYPES:
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION", "Unknown manual command discriminator"
        )
    if session.cursor >= len(session.context.timeline):
        raise SimulationError(
            "SIM_UNSUPPORTED_OPERATION", "Completed session accepts no command"
        )

    trader = SimTrader(session.context.engine)
    receipts: list[object] = []

    if discriminator == "submit_order":
        intent = _require_command_field(command, "intent")
        if getattr(intent, "simulation_session_id", None) != session_id:
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Order is not bound to the active session"
            )
        receipts.append(
            unwrap_simulation_response(
                await trader.submit_order(intent),
                operation="simulation.state.execute_live_simulation_command",
            )
        )
    elif discriminator == "cancel_pending_order":
        receipts.append(
            unwrap_simulation_response(
                trader.cancel_pending_order(
                    str(_require_command_field(command, "order_id"))
                ),
                operation="simulation.state.execute_live_simulation_command",
            )
        )
    elif discriminator == "modify_pending_order":
        receipts.append(
            unwrap_simulation_response(
                trader.modify_pending_order(
                    str(_require_command_field(command, "order_id")),
                    price=_decimal_or_none(command.get("price")),
                    stop_loss=_decimal_or_none(command.get("stop_loss")),
                    take_profit=_decimal_or_none(command.get("take_profit")),
                ),
                operation="simulation.state.execute_live_simulation_command",
            )
        )
    elif discriminator in {"close_position", "reduce_position"}:
        position_id = str(_require_command_field(command, "position_id"))
        volume = _decimal_or_none(_require_command_field(command, "volume"))
        if volume is None or volume <= 0:
            raise SimulationError(
                "SIM_INVALID_VOLUME", "Close volume must be a positive decimal"
            )
        receipts.append(
            unwrap_simulation_response(
                trader.close_position(position_id, volume),
                operation="simulation.state.execute_live_simulation_command",
            )
        )
    else:
        receipts.extend(_close_all_practice_exposure(trader))

    session.receipts.extend(receipts)
    _checkpoint(session, request_id=generate_id("req"))
    return MappingProxyType(
        {
            "receipts": tuple(receipts),
            "session": _project(session),
        }
    )


def finalize_live_simulation_session(
    session_id: str, *, request_id: str
) -> Mapping[str, object]:
    """Seal one session advisory journal.

    Finalization records that a practice session is complete and stops further
    mutation. It stays advisory: a sealed practice session is still not an
    official run, and reproducing it creates a separate canonical job rather
    than promoting this evidence.

    Args:
        session_id: Session identity.
        request_id: Trace identity for the durable checkpoint.

    Returns:
        Immutable sealed session state.

    Raises:
        SimulationError: `SIMULATION_SESSION_FINALIZED` when the session was
            already sealed, or `SIM_RECOVERY_STATE_INVALID` when it awaits
            rearm.
    """
    session = _require_active(session_id)
    session.finalized_at = utc_now()
    _checkpoint(session, request_id=request_id)
    logger.info("Finalized advisory Simulation session %s", session_id)
    return _project(session)


def reset_live_simulation_sessions() -> None:
    """Drop every live session.

    Test support and shutdown hook; production callers close their own
    sessions. Exposed because an abandoned registry would otherwise outlive a
    test module and leak engine state between cases.
    """
    _SESSIONS.clear()


def read_live_simulation_request(session_id: str) -> Mapping[str, object] | None:
    """Read one durable session's immutable canonical request.

    The stored request is the exact evidence a reproduction must re-execute,
    so it is returned verbatim and never merged with live session state.

    Args:
        session_id: Durable interactive session identity.

    Returns:
        Immutable canonical request mapping, or ``None`` when the durable
        record or its request is absent.
    """
    record = read_interactive_session_record(_store(), session_id)
    if record is None:
        return None
    request = record.get("request")
    if not isinstance(request, Mapping):
        return None
    return request


__all__ = (
    "COMMAND_TYPES",
    "branch_live_simulation",
    "close_live_simulation_session",
    "create_live_simulation_session",
    "execute_live_simulation_command",
    "finalize_live_simulation_session",
    "list_live_simulation_sessions",
    "read_live_simulation_request",
    "read_live_simulation_state",
    "read_live_simulation_viewport",
    "rearm_live_simulation_session",
    "reset_live_simulation_sessions",
    "restore_live_simulation_session",
    "seek_live_simulation",
    "step_live_simulation",
    "submit_live_simulation_order",
)
