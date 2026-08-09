"""Unit evidence for FEAT-SIM-13 recovery and replay integrity."""

from datetime import UTC, datetime

import pytest
from app.services.simulator import (
    branch_recovery_checkpoint,
    build_replay_identity,
    create_recovery_checkpoint,
    explicitly_rearm_simulation_session,
    restore_simulation_session,
    verify_recovery_checkpoints,
)
from app.services.simulator.errors import SimulationError

_HASH = "a" * 64


def _identity() -> object:
    """Build one canonical replay identity."""
    return build_replay_identity(
        run_id="run-1",
        scenario_id="scenario-1",
        scenario_version="v1",
        scenario_hash=_HASH,
        data_ref="dataset-1",
        data_hash=_HASH,
        execution_profile_id="profile-1",
        execution_profile_hash=_HASH,
        rules_version="v1",
        seed=7,
    )


def test_verified_chain_remains_blocked_until_explicit_rearm() -> None:
    """Restore latest state without exposure authority until explicit approval."""
    identity = _identity()
    checkpoint = create_recovery_checkpoint(
        session_id="session-1",
        sequence=0,
        previous_hash=None,
        replay_identity=identity,
        state_payload={"orders": [], "positions": []},
        created_at=datetime.now(UTC),
    )
    assert verify_recovery_checkpoints(
        (checkpoint,), expected_replay_id=identity.replay_id
    )
    restored = restore_simulation_session(
        (checkpoint,), expected_replay_id=identity.replay_id
    )
    assert restored["exposure_blocked"] is True
    running = explicitly_rearm_simulation_session(restored, approved=True)
    assert running["recovery_state"] == "RUNNING"
    assert running["exposure_blocked"] is False


def test_integrity_failure_and_scored_rewind_fail_closed() -> None:
    """Reject modified hashes and branch attempts on scored sessions."""
    identity = _identity()
    checkpoint = create_recovery_checkpoint(
        session_id="session-1",
        sequence=0,
        previous_hash=None,
        replay_identity=identity,
        state_payload={"orders": []},
        created_at=datetime.now(UTC),
    )
    corrupted = checkpoint.model_copy(update={"checkpoint_hash": "0" * 64})
    with pytest.raises(SimulationError, match="verification failed"):
        verify_recovery_checkpoints((corrupted,), expected_replay_id=identity.replay_id)
    with pytest.raises(SimulationError, match="cannot branch"):
        branch_recovery_checkpoint(
            checkpoint, practice=False, created_at=datetime.now(UTC)
        )
