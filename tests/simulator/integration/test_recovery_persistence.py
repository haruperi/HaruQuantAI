"""Relational integration evidence for secured Simulator recovery."""

from pathlib import Path

from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.simulator import (
    build_replay_identity,
    build_simulation_state_store,
    create_recovery_checkpoint,
    create_simulation_session,
    execute_simulation_state_store_operation,
    load_recovery_checkpoints,
    persist_recovery_checkpoint,
    restore_simulation_session,
    run_simulator_migrations,
    secure_simulation_session,
    unwrap_simulation_response,
)
from app.utils import generate_id, utc_now


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings for secured-session persistence."""
    return build_data_settings(
        database_url="sqlite:///simulation-recovery.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def test_secured_checkpoint_survives_persistence_reconstruction(tmp_path: Path) -> None:
    """Persist, reload, verify, and restore one complete checkpoint chain."""
    with data_settings_context(_settings(tmp_path)):
        migration_id = generate_id("req")
        unwrap_data_response(
            run_simulator_migrations(migration_id),
            operation="tests.simulator.recovery.migrations",
            request_id=migration_id,
        )
        run_request_id = generate_id("req")
        store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "record_idempotency",
                run_request_id,
                "a" * 64,
                "run-recovery",
                "completed",
                {"schema_id": "simulation.recovery_fixture.v1"},
            ),
            operation="tests.simulator.recovery.run",
        )
        session_request_id = generate_id("req")
        session = unwrap_simulation_response(
            create_simulation_session("run-recovery", request_id=session_request_id),
            operation="tests.simulator.recovery.session",
        )
        identity = build_replay_identity(
            run_id="run-recovery",
            scenario_id="mission-1",
            scenario_version="v1",
            scenario_hash="b" * 64,
            data_ref="dataset-1",
            data_hash="c" * 64,
            execution_profile_id="profile-1",
            execution_profile_hash="d" * 64,
            rules_version="v1",
            seed=11,
        )
        secure_simulation_session(
            str(session["session_id"]),
            mode="Challenge",
            replay_identity=identity,
            state={"clock_state": {"cursor": 4}, "counters": {"score": 10}},
            request_id=generate_id("req"),
        )
        checkpoint = create_recovery_checkpoint(
            session_id=str(session["session_id"]),
            sequence=0,
            previous_hash=None,
            replay_identity=identity,
            state_payload={
                "orders": [],
                "fills": [],
                "positions": [],
                "alerts": [],
                "score_events": [],
            },
            created_at=utc_now(),
        )
        persist_recovery_checkpoint(checkpoint, request_id=generate_id("req"))
        loaded = load_recovery_checkpoints(str(session["session_id"]))
        restored = restore_simulation_session(
            loaded, expected_replay_id=identity.replay_id
        )
        assert restored["checkpoint_hash"] == checkpoint.checkpoint_hash
        assert restored["exposure_blocked"] is True
