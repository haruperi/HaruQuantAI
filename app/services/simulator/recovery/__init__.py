"""Secured simulation-session recovery feature API."""

from app.services.simulator.recovery.checkpoints import (
    branch_recovery_checkpoint,
    build_replay_identity,
    create_recovery_checkpoint,
    verify_recovery_checkpoints,
)
from app.services.simulator.recovery.contracts import RecoveryCheckpoint, ReplayIdentity
from app.services.simulator.recovery.lifecycle import transition_recovery_state
from app.services.simulator.recovery.service import (
    explicitly_rearm_simulation_session,
    load_recovery_checkpoints,
    persist_recovery_checkpoint,
    persist_recovery_state,
    restore_simulation_session,
    secure_simulation_session,
)

__all__ = [
    "RecoveryCheckpoint",
    "ReplayIdentity",
    "branch_recovery_checkpoint",
    "build_replay_identity",
    "create_recovery_checkpoint",
    "explicitly_rearm_simulation_session",
    "load_recovery_checkpoints",
    "persist_recovery_checkpoint",
    "persist_recovery_state",
    "restore_simulation_session",
    "secure_simulation_session",
    "transition_recovery_state",
    "verify_recovery_checkpoints",
]
