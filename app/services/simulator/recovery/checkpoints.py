"""Construction and integrity verification for recovery checkpoints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from hashlib import sha256
from typing import Any

from app.services.simulator.errors import SimulationError
from app.services.simulator.recovery.contracts import RecoveryCheckpoint, ReplayIdentity
from app.utils import canonical_json, derive_stable_id


def build_replay_identity(**fields: object) -> ReplayIdentity:
    """Build the canonical replay identity from exact lineage fields.

    Args:
        **fields: Replay fields excluding the derived ``replay_id``.

    Returns:
        Validated immutable replay identity.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "simulator.replay_identity.v1",
        **fields,
    }
    replay_id = derive_stable_id("id", canonical_json(material))
    return ReplayIdentity.model_validate({**material, "replay_id": replay_id})


def _checkpoint_material(
    *,
    session_id: str,
    sequence: int,
    previous_hash: str | None,
    replay_identity: ReplayIdentity,
    state_payload: Mapping[str, Any],
    created_at: datetime,
) -> dict[str, object]:
    """Return the canonical checkpoint hash material."""
    return {
        "session_id": session_id,
        "sequence": sequence,
        "previous_hash": previous_hash,
        "replay_identity": replay_identity.model_dump(mode="json"),
        "state_payload": dict(state_payload),
        "created_at": created_at.isoformat(),
    }


def create_recovery_checkpoint(
    *,
    session_id: str,
    sequence: int,
    previous_hash: str | None,
    replay_identity: ReplayIdentity,
    state_payload: Mapping[str, Any],
    created_at: datetime,
) -> RecoveryCheckpoint:
    """Create one immutable hash-linked recovery checkpoint.

    Args:
        session_id: Secured simulation-session identity.
        sequence: Monotonic checkpoint sequence.
        previous_hash: Previous checkpoint hash, absent only at sequence zero.
        replay_identity: Canonical replay identity.
        state_payload: Complete bounded recovery state.
        created_at: Aware creation timestamp.

    Returns:
        Validated immutable checkpoint.
    """
    material = _checkpoint_material(
        session_id=session_id,
        sequence=sequence,
        previous_hash=previous_hash,
        replay_identity=replay_identity,
        state_payload=state_payload,
        created_at=created_at,
    )
    return RecoveryCheckpoint(
        session_id=session_id,
        sequence=sequence,
        previous_hash=previous_hash,
        replay_identity=replay_identity,
        state_payload=state_payload,
        created_at=created_at,
        checkpoint_hash=sha256(canonical_json(material).encode()).hexdigest(),
    )


def verify_recovery_checkpoints(
    checkpoints: Sequence[RecoveryCheckpoint],
    *,
    expected_replay_id: str,
) -> bool:
    """Verify sequence, linkage, identity, and content hashes fail-closed.

    Args:
        checkpoints: Ordered checkpoint chain.
        expected_replay_id: Required canonical replay identity.

    Returns:
        ``True`` for a valid complete chain.

    Raises:
        SimulationError: If any integrity invariant fails.
    """
    if not checkpoints:
        raise SimulationError("SIM_INTEGRITY_FAILURE", "Recovery chain is empty")
    prior: str | None = None
    for expected_sequence, checkpoint in enumerate(checkpoints):
        material = _checkpoint_material(
            session_id=checkpoint.session_id,
            sequence=checkpoint.sequence,
            previous_hash=checkpoint.previous_hash,
            replay_identity=checkpoint.replay_identity,
            state_payload=checkpoint.state_payload,
            created_at=checkpoint.created_at,
        )
        digest = sha256(canonical_json(material).encode()).hexdigest()
        if (
            checkpoint.sequence != expected_sequence
            or checkpoint.previous_hash != prior
            or checkpoint.replay_identity.replay_id != expected_replay_id
            or digest != checkpoint.checkpoint_hash
        ):
            raise SimulationError(
                "SIM_INTEGRITY_FAILURE", "Recovery checkpoint verification failed"
            )
        prior = checkpoint.checkpoint_hash
    return True


def branch_recovery_checkpoint(
    checkpoint: RecoveryCheckpoint,
    *,
    practice: bool,
    created_at: datetime,
) -> tuple[ReplayIdentity, RecoveryCheckpoint]:
    """Create an isolated practice branch and prohibit scored rewind.

    Args:
        checkpoint: Valid source checkpoint.
        practice: Whether the source session is unscored practice.
        created_at: Branch origin timestamp.

    Returns:
        Child identity and origin checkpoint.

    Raises:
        SimulationError: If a scored session attempts to branch.
    """
    if not practice:
        raise SimulationError(
            "SIM_RECOVERY_REWIND_DENIED", "Scored sessions cannot branch or rewind"
        )
    parent = checkpoint.replay_identity
    child = build_replay_identity(
        run_id=parent.run_id,
        scenario_id=parent.scenario_id,
        scenario_version=parent.scenario_version,
        scenario_hash=parent.scenario_hash,
        data_ref=parent.data_ref,
        data_hash=parent.data_hash,
        execution_profile_id=parent.execution_profile_id,
        execution_profile_hash=parent.execution_profile_hash,
        rules_version=parent.rules_version,
        seed=parent.seed,
        parent_replay_id=parent.replay_id,
        branch_point_sequence=checkpoint.sequence,
    )
    branch_session_id = derive_stable_id(
        "id",
        canonical_json(
            {
                "parent_session_id": checkpoint.session_id,
                "child_replay_id": child.replay_id,
            }
        ),
    )
    origin = create_recovery_checkpoint(
        session_id=branch_session_id,
        sequence=0,
        previous_hash=None,
        replay_identity=child,
        state_payload=checkpoint.state_payload,
        created_at=created_at,
    )
    return child, origin


__all__ = [
    "branch_recovery_checkpoint",
    "build_replay_identity",
    "create_recovery_checkpoint",
    "verify_recovery_checkpoints",
]
