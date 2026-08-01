"""Integration evidence for the durable Simulation runtime adapter."""

import hashlib
import json
from pathlib import Path

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.services.simulator import (
    build_simulation_state_store,
    execute_simulation_state_store_operation,
    unwrap_simulation_response,
)
from app.utils import generate_id


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///simulation-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def test_simulation_runtime_state_is_durable(tmp_path: Path) -> None:
    """Simulation lifecycle and journal state survive adapter reconstruction."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.simulation.runtime.migrations",
            request_id=request_id,
        )
        artifact_root = tmp_path / "artifacts"
        store = build_simulation_state_store(artifact_root=artifact_root)
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "record_idempotency",
                request_id,
                "a" * 64,
                "run-one",
                "started",
            ),
            operation="tests.simulation.runtime.record",
        )
        event = json.dumps(
            {"sequence": 0, "event_hash": "b" * 64},
            sort_keys=True,
            separators=(",", ":"),
        )
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "append_journal",
                "run-one",
                event,
            ),
            operation="tests.simulation.runtime.append",
        )
        checksum = unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "finalize_journal",
                "run-one",
                1,
                "b" * 64,
            ),
            operation="tests.simulation.runtime.finalize",
        )
        assert checksum == hashlib.sha256(f"{event}\n".encode()).hexdigest()

        reconstructed = build_simulation_state_store(artifact_root=artifact_root)
        row = unwrap_simulation_response(
            execute_simulation_state_store_operation(
                reconstructed,
                "load_run",
                request_id,
            ),
            operation="tests.simulation.runtime.load",
        )
        assert row is not None
        assert row["status"] == "started"
