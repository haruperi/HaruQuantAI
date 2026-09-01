"""Restore, verify, and explicitly rearm secured simulation sessions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import cast

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.kernel.time import format_utc_timestamp, parse_utc_timestamp, utc_now
from app.services.simulator.errors import SimulationError
from app.services.simulator.persistence import (
    create_recovery_checkpoint_record,
    create_simulator_persistence_store,
    read_recovery_checkpoint_records,
    read_session_record,
    update_secured_session_record,
)
from app.services.simulator.recovery.checkpoints import verify_recovery_checkpoints
from app.services.simulator.recovery.contracts import RecoveryCheckpoint, ReplayIdentity
from app.services.simulator.recovery.lifecycle import (
    RecoveryState,
    transition_recovery_state,
)

logger = get_logger(__name__)


def _store() -> object:
    """Create one private persistence handle for secured sessions.

    Returns:
        Opaque Simulator persistence handle.
    """
    return create_simulator_persistence_store(lambda value: value)


def secure_simulation_session(
    session_id: str,
    *,
    mode: str,
    replay_identity: ReplayIdentity,
    state: Mapping[str, object],
    request_id: str,
) -> Mapping[str, object]:
    """Mark an existing durable playback session as recovery-secured.

    Args:
        session_id: Existing durable session identity.
        mode: Supported simulation mode.
        replay_identity: Canonical Simulator replay identity.
        state: Initial secured aggregate state.
        request_id: Trace identifier for persistence.

    Returns:
        Updated normalized session projection.

    Raises:
        SimulationError: If the session is absent or cannot be secured.
    """
    logger.info("Securing durable Simulation session %s", session_id)
    store = _store()
    if read_session_record(store, session_id) is None:
        raise SimulationError(
            "SIM_SESSION_NOT_FOUND", "Simulation session was not found"
        )
    secured_at = format_utc_timestamp(utc_now())
    aggregate = {
        **dict(state),
        "replay_identity": replay_identity.model_dump(mode="json"),
    }
    if not update_secured_session_record(
        store,
        session_id=session_id,
        mode=mode,
        recovery_state="STARTING",
        secured_at=secured_at,
        state=aggregate,
        request_id=request_id,
    ):
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Session securing failed")
    result = read_session_record(store, session_id)
    if result is None:
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Secured session read failed")
    return MappingProxyType(dict(result))


def persist_recovery_checkpoint(
    checkpoint: RecoveryCheckpoint, *, request_id: str
) -> None:
    """Persist one validated immutable recovery checkpoint.

    Args:
        checkpoint: Validated recovery checkpoint.
        request_id: Trace identifier for persistence.
    """
    logger.info(
        "Persisting Simulation recovery checkpoint sequence %s",
        checkpoint.sequence,
    )
    create_recovery_checkpoint_record(
        _store(), checkpoint.model_dump(mode="json"), request_id=request_id
    )


def load_recovery_checkpoints(session_id: str) -> tuple[RecoveryCheckpoint, ...]:
    """Load and validate one session's ordered checkpoint chain.

    Args:
        session_id: Secured simulation-session identity.

    Returns:
        Ordered validated checkpoints.
    """
    logger.info("Loading recovery checkpoints for Simulation session %s", session_id)
    return tuple(
        RecoveryCheckpoint.model_validate(
            {
                **row,
                "created_at": parse_utc_timestamp(str(row["created_at"])),
            }
        )
        for row in read_recovery_checkpoint_records(_store(), session_id)
    )


def persist_recovery_state(
    session_id: str,
    *,
    recovery_state: str,
    state: Mapping[str, object],
    request_id: str | None = None,
) -> None:
    """Persist a verified recovery lifecycle and aggregate projection.

    Args:
        session_id: Secured simulation-session identity.
        recovery_state: Valid recovery lifecycle state.
        state: Complete aggregate state mapping.
        request_id: Optional trace identifier.

    Raises:
        SimulationError: If the secured session is absent or update fails.
    """
    logger.info("Persisting Simulation recovery transition for session %s", session_id)
    store = _store()
    current = read_session_record(store, session_id)
    if current is None or current.get("session_kind") != "secured":
        raise SimulationError("SIM_SESSION_NOT_FOUND", "Secured session was not found")
    current_state = cast("RecoveryState", str(current["recovery_state"]))
    target_state = cast("RecoveryState", recovery_state)
    accepted_state = transition_recovery_state(current_state, target_state)
    if not update_secured_session_record(
        store,
        session_id=session_id,
        mode=str(current["mode"]),
        recovery_state=accepted_state,
        secured_at=str(current["secured_at"]),
        state=state,
        request_id=request_id or generate_id("req"),
    ):
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Recovery state update failed")


def restore_simulation_session(
    checkpoints: Sequence[RecoveryCheckpoint], *, expected_replay_id: str
) -> Mapping[str, object]:
    """Restore the latest verified secured-session checkpoint.

    Args:
        checkpoints: Complete ordered checkpoint chain.
        expected_replay_id: Required canonical replay identity.

    Returns:
        Immutable verified state, still exposure-blocked pending explicit rearm.
    """
    logger.info("Verifying and restoring a secured Simulation checkpoint chain")
    state = transition_recovery_state("STARTING", "RECOVERY_LOCKED")
    state = transition_recovery_state(state, "RESTORING")
    verify_recovery_checkpoints(checkpoints, expected_replay_id=expected_replay_id)
    state = transition_recovery_state(state, "RECONCILING")
    state = transition_recovery_state(state, "VERIFIED")
    return MappingProxyType(
        {
            "recovery_state": state,
            "exposure_blocked": True,
            "session_id": checkpoints[-1].session_id,
            "sequence": checkpoints[-1].sequence,
            "checkpoint_hash": checkpoints[-1].checkpoint_hash,
            "state_payload": dict(checkpoints[-1].state_payload),
        }
    )


def explicitly_rearm_simulation_session(
    restored: Mapping[str, object], *, approved: bool
) -> Mapping[str, object]:
    """Rearm only an explicitly approved, previously verified session.

    Args:
        restored: Verified recovery projection.
        approved: Deterministic explicit-rearm approval.

    Returns:
        Immutable running projection.

    Raises:
        ValueError: If approval or verified state is absent.
    """
    logger.info("Evaluating explicit Simulation session rearm")
    if not approved or restored.get("recovery_state") != "VERIFIED":
        raise ValueError("verified explicit rearm approval is required")
    state = transition_recovery_state("VERIFIED", "EXPLICIT_REARM")
    state = transition_recovery_state(state, "RUNNING")
    return MappingProxyType(
        {**dict(restored), "recovery_state": state, "exposure_blocked": False}
    )


__all__ = [
    "explicitly_rearm_simulation_session",
    "load_recovery_checkpoints",
    "persist_recovery_checkpoint",
    "persist_recovery_state",
    "restore_simulation_session",
    "secure_simulation_session",
]
