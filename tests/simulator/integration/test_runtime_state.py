"""Integration evidence for the durable Simulation runtime adapter."""

import hashlib
import json
from pathlib import Path

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_statement_plan,
    build_transaction_request,
    data_settings_context,
    execute_transaction,
    unwrap_data_response,
)
from app.services.simulator import (
    build_simulation_state_store,
    execute_simulation_state_store_operation,
    run_simulator_migrations,
    unwrap_simulation_response,
)

from tests.simulator.unit.test_reporting_contracts import _result


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
            run_simulator_migrations(request_id),
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
        reconstructed_partial = build_simulation_state_store(
            artifact_root=artifact_root
        )
        second_event = json.dumps(
            {"sequence": 1, "event_hash": "c" * 64},
            sort_keys=True,
            separators=(",", ":"),
        )
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                reconstructed_partial,
                "append_journal",
                "run-one",
                second_event,
            ),
            operation="tests.simulation.runtime.append-reconstructed",
        )
        checksum = unwrap_simulation_response(
            execute_simulation_state_store_operation(
                reconstructed_partial,
                "finalize_journal",
                "run-one",
                2,
                "c" * 64,
            ),
            operation="tests.simulation.runtime.finalize",
        )
        assert (
            checksum
            == hashlib.sha256(f"{event}\n{second_event}\n".encode()).hexdigest()
        )
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "record_idempotency",
                request_id,
                "a" * 64,
                "run-one",
                "completed",
                {"journal_checksum": checksum},
            ),
            operation="tests.simulation.runtime.complete",
        )

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
        assert row["status"] == "completed"
        assert row["result_payload"] == {"journal_checksum": checksum}
        assert (artifact_root / "run-one" / "journal.jsonl").is_file()
        assert not (artifact_root / "run-one" / "journal.jsonl.partial").exists()

        count_request_id = generate_id("req")
        count = unwrap_data_response(
            execute_transaction(
                build_transaction_request(
                    plan=build_statement_plan(
                        statements=("SELECT COUNT(*) AS count FROM sim_runs",),
                        parameter_sets=((),),
                        max_rows=1,
                    ),
                    request_id=count_request_id,
                )
            ),
            operation="tests.simulation.runtime.count",
            request_id=count_request_id,
        )
        assert count.rows[0]["count"] == 1


def test_completed_result_round_trips_from_sim_runs(tmp_path: Path) -> None:
    """Completed owner contracts are reconstructed from the relational row."""
    with data_settings_context(_settings(tmp_path)):
        migration_request_id = generate_id("req")
        unwrap_data_response(
            run_simulator_migrations(migration_request_id),
            operation="tests.simulation.result.migrations",
            request_id=migration_request_id,
        )
        result = _result()
        request_id = generate_id("req")
        store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
        unwrap_simulation_response(
            execute_simulation_state_store_operation(
                store,
                "record_idempotency",
                request_id,
                result.request_hash,
                result.run_id,
                "completed",
                result.model_dump(mode="json", warnings=False),
            ),
            operation="tests.simulation.result.complete",
        )
        reconstructed = build_simulation_state_store(
            artifact_root=tmp_path / "artifacts"
        )
        loaded = unwrap_simulation_response(
            execute_simulation_state_store_operation(
                reconstructed,
                "load_result",
                result.run_id,
            ),
            operation="tests.simulation.result.load",
        )
        assert loaded == result
