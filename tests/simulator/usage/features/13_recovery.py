"""Standalone usage for FEAT-SIM-13 secured-session recovery."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.kernel.time import utc_now
from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.simulator import (
    branch_recovery_checkpoint,
    build_replay_identity,
    build_simulation_state_store,
    create_recovery_checkpoint,
    create_simulation_recovery_state,
    create_simulation_session,
    execute_simulation_state_store_operation,
    explicitly_rearm_simulation_session,
    load_recovery_checkpoints,
    persist_recovery_checkpoint,
    persist_recovery_state,
    recover_simulation_unknown_outcome,
    restore_simulation_session,
    run_simulator_migrations,
    secure_simulation_session,
    unwrap_simulation_response,
    verify_recovery_checkpoints,
)


def _identity() -> object:
    """Build one bounded canonical replay identity."""
    return build_replay_identity(
        run_id="run-usage-recovery",
        scenario_id="mission-usage",
        scenario_version="v1",
        scenario_hash="a" * 64,
        data_ref="dataset-usage",
        data_hash="b" * 64,
        execution_profile_id="profile-usage",
        execution_profile_hash="c" * 64,
        rules_version="v1",
        seed=17,
    )


def _checkpoint(session_id: str = "session-usage") -> object:
    """Build one origin recovery checkpoint."""
    return create_recovery_checkpoint(
        session_id=session_id,
        sequence=0,
        previous_hash=None,
        replay_identity=_identity(),
        state_payload={"orders": [], "fills": [], "positions": [], "alerts": []},
        created_at=utc_now(),
    )


def fr_sim_124() -> None:
    """FR-SIM-124: Simulator shall own canonical `ReplayIdentity v1` across exact run, scenario, dataset, execution-profile, rules, seed, parent, and branch-point identity."""
    identity = _identity()
    print(f"SUCCESS: FR-SIM-124 identity built; Data -> {identity.replay_id}")


def fr_sim_125() -> None:
    """FR-SIM-125: Secured-session recovery shall follow `STARTING` through lock, restore, reconciliation, verification, explicit rearm, and running without undeclared or regressive transitions."""
    checkpoint = _checkpoint()
    restored = restore_simulation_session(
        (checkpoint,), expected_replay_id=checkpoint.replay_identity.replay_id
    )
    running = explicitly_rearm_simulation_session(restored, approved=True)
    print(f"SUCCESS: FR-SIM-125 recovery rearmed; Data -> {running['recovery_state']}")


def fr_sim_126() -> None:
    """FR-SIM-126: Simulator shall persist and restore immutable hash-linked checkpoints containing complete bounded orders, fills, positions, protection, portfolio-reference, lockout, cooldown, alert, checklist, counter, and score-event state."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///usage-recovery.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            migration_id = generate_id("req")
            unwrap_data_response(
                run_simulator_migrations(migration_id),
                operation="usage.simulator.recovery.migrations",
                request_id=migration_id,
            )
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=root / "artifacts")
            unwrap_simulation_response(
                execute_simulation_state_store_operation(
                    store,
                    "record_idempotency",
                    request_id,
                    "d" * 64,
                    "run-usage-recovery",
                    "completed",
                    {"schema_id": "simulation.recovery_usage.v1"},
                ),
                operation="usage.simulator.recovery.run",
            )
            session = unwrap_simulation_response(
                create_simulation_session(
                    "run-usage-recovery", request_id=generate_id("req")
                ),
                operation="usage.simulator.recovery.session",
            )
            session_id = str(session["session_id"])
            identity = _identity()
            secure_simulation_session(
                session_id,
                mode="Challenge",
                replay_identity=identity,
                state={"clock_state": {"cursor": 1}},
                request_id=generate_id("req"),
            )
            checkpoint = create_recovery_checkpoint(
                session_id=session_id,
                sequence=0,
                previous_hash=None,
                replay_identity=identity,
                state_payload={
                    "orders": [],
                    "fills": [],
                    "positions": [],
                    "protection": {},
                    "portfolio_references": [],
                    "lockouts": [],
                    "cooldowns": [],
                    "alerts": [],
                    "checklist": {},
                    "counters": {},
                    "score_events": [],
                },
                created_at=utc_now(),
            )
            persist_recovery_checkpoint(checkpoint, request_id=generate_id("req"))
            loaded = load_recovery_checkpoints(session_id)
            recovery_projection = {"replay_identity": identity.model_dump(mode="json")}
            for recovery_state in (
                "RECOVERY_LOCKED",
                "RESTORING",
                "RECONCILING",
                "VERIFIED",
            ):
                persist_recovery_state(
                    session_id,
                    recovery_state=recovery_state,
                    state=recovery_projection,
                    request_id=generate_id("req"),
                )
            print(
                f"SUCCESS: FR-SIM-126 checkpoint persisted; Data -> count={len(loaded)}"
            )


def fr_sim_127() -> None:
    """FR-SIM-127: Simulator shall isolate practice branches under child replay identity and prohibit scored-session branch or rewind."""
    child, branch = branch_recovery_checkpoint(
        _checkpoint(), practice=True, created_at=utc_now()
    )
    print(
        f"SUCCESS: FR-SIM-127 practice branch isolated; Data -> {child.replay_id}, sequence={branch.sequence}"
    )


def fr_sim_128() -> None:
    """FR-SIM-128: Checksum mismatch, missing sequence, broken hash linkage, or replay-identity mismatch shall enter integrity failure and leave exposure blocked until a complete verified chain receives explicit rearm."""
    checkpoint = _checkpoint()
    valid = verify_recovery_checkpoints(
        (checkpoint,), expected_replay_id=checkpoint.replay_identity.replay_id
    )
    restored = restore_simulation_session(
        (checkpoint,), expected_replay_id=checkpoint.replay_identity.replay_id
    )
    uncertain = create_simulation_recovery_state(
        command_id="usage-command",
        crash_point="after_response_receipt",
        outcome="unknown",
    )
    converged = recover_simulation_unknown_outcome(
        uncertain, authority_query=lambda _command_id: "accepted"
    )
    print(
        f"SUCCESS: FR-SIM-128 integrity verified; Data -> valid={valid}, exposure_blocked={restored['exposure_blocked']}, unknown_outcome={converged['outcome']}"
    )


def main() -> None:
    """Run every FEAT-SIM-13 requirement demonstration."""
    print("FEATURE: FEAT-SIM-13 — Session Recovery")
    fr_sim_124()
    fr_sim_125()
    fr_sim_126()
    fr_sim_127()
    fr_sim_128()


if __name__ == "__main__":
    main()
