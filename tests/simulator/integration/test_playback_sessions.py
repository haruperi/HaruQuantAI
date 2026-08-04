"""Integration tests for durable Simulation playback sessions."""

from pathlib import Path

import pytest
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.simulator import (
    build_simulation_state_store,
    create_simulation_session,
    execute_simulation_state_store_operation,
    get_simulation_migrations,
    read_simulation_session,
    unwrap_simulation_response,
)
from app.services.simulator.errors import SimulationError
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings for one test database."""
    return build_data_settings(
        database_url="sqlite:///simulation-playback.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _migrate() -> None:
    """Apply the complete Simulator migration manifest."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_domain_migrations(
            build_migration_request(
                domain="simulator",
                steps=get_simulation_migrations(),
                request_id=request_id,
            )
        ),
        operation="tests.simulation.playback.migrations",
        request_id=request_id,
    )


def test_completed_run_creates_durable_playback_session(tmp_path: Path) -> None:
    """A completed run may open a durable session with cursor minus one."""
    with data_settings_context(_settings(tmp_path)):
        _migrate()
        store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
        run_request_id = generate_id("req")
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "record_idempotency",
                run_request_id,
                "a" * 64,
                "run-playback",
                "completed",
                {"status": "completed"},
            ),
            operation="tests.simulation.playback.complete",
        )
        session = unwrap_simulation_response(
            create_simulation_session(
                "run-playback",
                request_id=generate_id("req"),
            ),
            operation="tests.simulation.playback.create",
        )
        loaded = unwrap_simulation_response(
            read_simulation_session(str(session["session_id"])),
            operation="tests.simulation.playback.read",
        )
        assert loaded is not None
        assert loaded["run_id"] == "run-playback"
        assert loaded["status"] == "active"
        assert loaded["cursor"] == -1


def test_incomplete_run_cannot_create_playback_session(tmp_path: Path) -> None:
    """Missing completed-run evidence fails closed."""
    with data_settings_context(_settings(tmp_path)):
        _migrate()
        response = create_simulation_session(
            "run-missing",
            request_id=generate_id("req"),
        )
        with pytest.raises(SimulationError) as captured:
            unwrap_simulation_response(
                response,
                operation="tests.simulation.playback.missing",
            )
        assert captured.value.code == "SIM_SESSION_NOT_FOUND"
