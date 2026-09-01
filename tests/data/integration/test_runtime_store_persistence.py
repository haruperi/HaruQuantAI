"""Integration tests for Data-owned durable runtime records."""

import json
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_simulator_runtime_store,
    data_settings_context,
    execute_runtime_store_operation,
    run_runtime_store_migrations,
    unwrap_data_response,
)


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings value.
    """
    return build_data_settings(
        database_url="sqlite:///runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _codec() -> tuple[object, object]:
    """Return a deterministic JSON codec pair.

    Returns:
        Encoder and decoder callables.
    """
    return (lambda value: json.dumps(value, sort_keys=True), json.loads)


def test_runtime_records_survive_handle_reconstruction(tmp_path: Path) -> None:
    """Committed records are durable and CAS remains revision guarded."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.data.runtime_store.migrations",
            request_id=request_id,
        )
        first = build_simulator_runtime_store({"run": _codec()})  # type: ignore[dict-item]
        assert (
            execute_runtime_store_operation(
                first,
                "put_once",
                collection="runs",
                key="run-1",
                kind="run",
                value={"state": "created"},
            )
            == 1
        )
        assert (
            execute_runtime_store_operation(
                first,
                "compare_and_swap",
                collection="runs",
                key="run-1",
                kind="run",
                value={"state": "completed"},
                expected_revision=1,
            )
            == 2
        )
        second = build_simulator_runtime_store({"run": _codec()})  # type: ignore[dict-item]
        assert execute_runtime_store_operation(
            second,
            "get",
            collection="runs",
            key="run-1",
        ) == {"state": "completed"}
        with pytest.raises(ValueError, match="revision conflict"):
            execute_runtime_store_operation(
                second,
                "compare_and_swap",
                collection="runs",
                key="run-1",
                kind="run",
                value={"state": "invalid"},
                expected_revision=1,
            )


def test_runtime_records_can_be_read_across_partitions(tmp_path: Path) -> None:
    """Read a bounded deterministic operational view across exact partitions."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.data.runtime_store.migrations",
            request_id=request_id,
        )
        store = build_simulator_runtime_store({"run": _codec()})  # type: ignore[dict-item]
        for sequence, partition in ((2, "second"), (1, "first")):
            execute_runtime_store_operation(
                store,
                "append",
                collection="events",
                key=f"event-{partition}",
                partition=partition,
                sequence=sequence,
                kind="run",
                value={"partition": partition},
            )
        assert execute_runtime_store_operation(
            store,
            "list_all_partitions",
            collection="events",
            limit=10,
        ) == ({"partition": "first"}, {"partition": "second"})
