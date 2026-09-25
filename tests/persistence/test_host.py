"""Tests for the host_* CRUD surface of app.persistence.host.

Every test runs against an isolated temporary database created by
ensure_schema; the live database under data/ is never opened for writing.
Column shapes below were captured read-only from the live
data/database/haruquantai.db on 2026-09-25.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from app.persistence.host import (
    ACTIVE_LEASE_STATE,
    EXPIRED_LEASE_STATE,
    HostGridLeaseRecord,
    HostGridNodeRecord,
    HostJobAttemptRecord,
    HostJobEventRecord,
    HostJobRecord,
    HostPersistenceConflictError,
    HostPersistenceError,
    HostPersistenceSchemaError,
    HostPersistenceValueError,
    HostSettingRecord,
    HostStore,
    _raise_for_integrity,
    ensure_schema,
    read_settings,
    utc_now_iso,
    verify_schema,
)

# (column name, declared type, NOT NULL flag, primary-key position) per table,
# recorded from the live database schema on 2026-09-25.
LIVE_COLUMN_SHAPES: dict[str, tuple[tuple[str, str, int, int], ...]] = {
    "host_settings": (
        ("scope", "TEXT", 1, 1),
        ("key", "TEXT", 1, 2),
        ("value_json", "TEXT", 1, 0),
        ("schema_version", "INTEGER", 1, 0),
        ("updated_at_utc", "TEXT", 1, 0),
    ),
    "host_jobs": (
        ("job_id", "TEXT", 0, 1),
        ("group_id", "TEXT", 1, 0),
        ("operation", "TEXT", 1, 0),
        ("state", "TEXT", 1, 0),
        ("priority", "INTEGER", 1, 0),
        ("resource_class", "TEXT", 1, 0),
        ("config_hash", "TEXT", 1, 0),
        ("payload_json", "TEXT", 1, 0),
        ("progress_percent", "REAL", 1, 0),
        ("progress_message", "TEXT", 1, 0),
        ("checkpoint_json", "TEXT", 0, 0),
        ("created_at_utc", "TEXT", 1, 0),
        ("started_at_utc", "TEXT", 0, 0),
        ("completed_at_utc", "TEXT", 0, 0),
        ("terminal_reason", "TEXT", 0, 0),
    ),
    "host_job_attempts": (
        ("attempt_id", "TEXT", 0, 1),
        ("job_id", "TEXT", 1, 0),
        ("worker_id", "TEXT", 1, 0),
        ("sequence", "INTEGER", 1, 0),
        ("state", "TEXT", 1, 0),
        ("heartbeat_at_utc", "TEXT", 0, 0),
        ("checkpoint_json", "TEXT", 0, 0),
        ("created_at_utc", "TEXT", 1, 0),
        ("completed_at_utc", "TEXT", 0, 0),
    ),
    "host_job_events": (
        ("event_id", "TEXT", 0, 1),
        ("job_id", "TEXT", 1, 0),
        ("attempt_id", "TEXT", 0, 0),
        ("from_state", "TEXT", 0, 0),
        ("to_state", "TEXT", 1, 0),
        ("details_json", "TEXT", 1, 0),
        ("created_at_utc", "TEXT", 1, 0),
    ),
    "host_grid_nodes": (
        ("node_id", "TEXT", 0, 1),
        ("host", "TEXT", 1, 0),
        ("port", "INTEGER", 1, 0),
        ("cores", "INTEGER", 1, 0),
        ("memory_mb", "INTEGER", 1, 0),
        ("state", "TEXT", 1, 0),
        ("last_heartbeat_utc", "TEXT", 1, 0),
    ),
    "host_grid_leases": (
        ("lease_id", "TEXT", 0, 1),
        ("node_id", "TEXT", 1, 0),
        ("job_id", "TEXT", 1, 0),
        ("leased_at_utc", "TEXT", 1, 0),
        ("expires_at_utc", "TEXT", 1, 0),
        ("state", "TEXT", 1, 0),
    ),
}

LIVE_INDEX_SHAPES: dict[str, set[str]] = {
    "host_settings": set(),
    "host_jobs": {"idx_workspace_jobs_state", "idx_workspace_jobs_group"},
    "host_job_attempts": {"idx_workspace_attempts_job"},
    "host_job_events": {"idx_workspace_events_job"},
    "host_grid_nodes": set(),
    "host_grid_leases": {"idx_workspace_leases_node", "idx_workspace_leases_job"},
}


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "database" / "host.db"
    ensure_schema(path)
    return path


@pytest.fixture()
def store(database_path: Path) -> HostStore:
    return HostStore(database_path)


def setting(
    scope: str = "application",
    key: str = "app.general",
    value_json: str = '{"theme": "dark"}',
    schema_version: int = 1,
    updated_at_utc: str = "2026-09-25T10:00:00+00:00",
) -> HostSettingRecord:
    return HostSettingRecord(
        scope=scope,
        key=key,
        value_json=value_json,
        schema_version=schema_version,
        updated_at_utc=updated_at_utc,
    )


def job(job_id: str = "job-1", **overrides: Any) -> HostJobRecord:
    values: dict[str, Any] = {
        "job_id": job_id,
        "group_id": "group-1",
        "operation": "simulate",
        "state": "queued",
        "priority": 5,
        "resource_class": "cpu",
        "config_hash": "hash-1",
        "payload_json": '{"symbol": "EURUSD"}',
        "progress_percent": 0.0,
        "progress_message": "",
        "checkpoint_json": None,
        "created_at_utc": "2026-09-25T10:00:00+00:00",
        "started_at_utc": None,
        "completed_at_utc": None,
        "terminal_reason": None,
    }
    values.update(overrides)
    return HostJobRecord(**values)


def attempt(attempt_id: str = "att-1", job_id: str = "job-1") -> HostJobAttemptRecord:
    return HostJobAttemptRecord(
        attempt_id=attempt_id,
        job_id=job_id,
        worker_id="worker-1",
        sequence=1,
        state="running",
        heartbeat_at_utc=None,
        checkpoint_json=None,
        created_at_utc="2026-09-25T10:01:00+00:00",
        completed_at_utc=None,
    )


def event(event_id: str = "evt-1", job_id: str = "job-1") -> HostJobEventRecord:
    return HostJobEventRecord(
        event_id=event_id,
        job_id=job_id,
        to_state="queued",
        details_json='{"reason": "created"}',
        created_at_utc="2026-09-25T10:00:00+00:00",
    )


def node(node_id: str = "node-1") -> HostGridNodeRecord:
    return HostGridNodeRecord(
        node_id=node_id,
        host="127.0.0.1",
        port=9001,
        cores=16,
        memory_mb=32768,
        state="online",
        last_heartbeat_utc="2026-09-25T10:00:00+00:00",
    )


def lease(
    lease_id: str = "lease-1",
    node_id: str = "node-1",
    job_id: str = "job-1",
    expires_at_utc: str = "2026-09-25T11:00:00+00:00",
) -> HostGridLeaseRecord:
    return HostGridLeaseRecord(
        lease_id=lease_id,
        node_id=node_id,
        job_id=job_id,
        leased_at_utc="2026-09-25T10:05:00+00:00",
        expires_at_utc=expires_at_utc,
        state=ACTIVE_LEASE_STATE,
    )


@pytest.fixture()
def seeded_store(store: HostStore) -> HostStore:
    """Seed one job, node, and active lease for grid tests."""
    store.insert_job(job())
    store.upsert_node(node())
    store.insert_lease(lease())
    return store


def stored_event(store: HostStore, event_id: str) -> HostJobEventRecord | None:
    """Read one event through the public list API for assertions."""
    for record in store.list_events("job-1"):
        if record.event_id == event_id:
            return record
    return None


# -- schema management ------------------------------------------------------


def test_ensure_schema_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "database" / "host.db"
    ensure_schema(path)
    assert path.is_file()


def test_ensure_schema_is_idempotent(database_path: Path) -> None:
    ensure_schema(database_path)
    assert HostStore(database_path).list_jobs() == []


def test_ensure_schema_matches_live_table_shapes(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        for table, expected in LIVE_COLUMN_SHAPES.items():
            actual = tuple(
                (str(row[1]), str(row[2]), int(row[3]), int(row[5]))
                for row in connection.execute(f"PRAGMA table_info({table})")
            )
            assert actual == expected, table
    finally:
        connection.close()


def test_ensure_schema_matches_live_index_names(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    try:
        for table, expected in LIVE_INDEX_SHAPES.items():
            actual = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND tbl_name=? AND sql IS NOT NULL",
                    (table,),
                )
            }
            assert actual == expected, table
    finally:
        connection.close()


def test_verify_schema_rejects_missing_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(HostPersistenceSchemaError):
        verify_schema(missing)
    assert not missing.exists()


def test_verify_schema_rejects_non_sqlite_file(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_text("this is not a database", encoding="utf-8")
    with pytest.raises(HostPersistenceSchemaError):
        verify_schema(corrupt)


def test_verify_schema_rejects_missing_table(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    connection.execute("DROP TABLE host_grid_leases")
    connection.commit()
    connection.close()
    with pytest.raises(HostPersistenceSchemaError):
        verify_schema(database_path)


def test_verify_schema_rejects_drifted_table(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    connection.execute("DROP TABLE host_settings")
    connection.execute("CREATE TABLE host_settings (scope TEXT)")
    connection.commit()
    connection.close()
    with pytest.raises(HostPersistenceSchemaError):
        verify_schema(database_path)


def test_store_rejects_drifted_schema(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    connection.execute("ALTER TABLE host_grid_nodes DROP COLUMN memory_mb")
    connection.commit()
    connection.close()
    with pytest.raises(HostPersistenceSchemaError):
        HostStore(database_path)


def test_utc_now_iso_is_explicit_utc() -> None:
    stamp = utc_now_iso()
    parsed = datetime.fromisoformat(stamp)
    assert stamp.endswith("+00:00")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None


# -- host_settings ------------------------------------------------------------


def test_upsert_and_get_setting_round_trip(store: HostStore) -> None:
    record = setting()
    store.upsert_setting(record)
    assert store.get_setting("application", "app.general") == record


def test_get_setting_missing_returns_none(store: HostStore) -> None:
    assert store.get_setting("application", "app.general") is None


def test_upsert_setting_canonicalizes_object_json(store: HostStore) -> None:
    store.upsert_setting(setting(value_json='{"b": 2, "a": 1}'))
    stored = store.get_setting("application", "app.general")
    assert stored is not None
    assert stored.value_json == '{"a": 1, "b": 2}'


def test_upsert_setting_replaces_existing_record(store: HostStore) -> None:
    store.upsert_setting(setting(value_json='{"a": 1}'))
    store.upsert_setting(
        setting(value_json='{"a": 2}', updated_at_utc="2026-09-25T12:00:00+00:00")
    )
    stored = store.get_setting("application", "app.general")
    assert stored is not None
    assert stored.value_json == '{"a": 2}'
    assert stored.updated_at_utc == "2026-09-25T12:00:00+00:00"


def test_upsert_setting_rejects_non_object_json(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.upsert_setting(setting(value_json="[1, 2]"))


def test_upsert_setting_rejects_malformed_json(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.upsert_setting(setting(value_json='{"a": '))


def test_upsert_setting_rejects_non_finite_constant(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.upsert_setting(setting(value_json='{"a": NaN}'))


def test_list_settings_orders_and_filters_by_scope(store: HostStore) -> None:
    store.upsert_setting(setting(scope="application", key="app.general"))
    store.upsert_setting(setting(scope="application", key="app.network"))
    store.upsert_setting(setting(scope="host", key="host.runtime"))
    assert [r.key for r in store.list_settings()] == [
        "app.general",
        "app.network",
        "host.runtime",
    ]
    assert [r.key for r in store.list_settings(scope="host")] == ["host.runtime"]


def test_delete_setting_reports_presence(store: HostStore) -> None:
    store.upsert_setting(setting())
    assert store.delete_setting("application", "app.general") is True
    assert store.delete_setting("application", "app.general") is False


# -- host_jobs ----------------------------------------------------------------


def test_insert_and_get_job_round_trip(store: HostStore) -> None:
    record = job()
    store.insert_job(record)
    assert store.get_job("job-1") == record


def test_get_job_missing_returns_none(store: HostStore) -> None:
    assert store.get_job("job-1") is None


def test_insert_job_rejects_duplicate(store: HostStore) -> None:
    store.insert_job(job())
    with pytest.raises(HostPersistenceConflictError):
        store.insert_job(job())


def test_insert_job_rejects_malformed_payload(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.insert_job(job(payload_json="not json"))


def test_insert_job_rejects_out_of_range_progress(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.insert_job(job(progress_percent=100.5))


def test_list_jobs_orders_by_priority_then_age(store: HostStore) -> None:
    store.insert_job(job("low", priority=1, created_at_utc="2026-09-25T09:00:00+00:00"))
    store.insert_job(
        job("high", priority=9, created_at_utc="2026-09-25T10:00:00+00:00")
    )
    store.insert_job(job("mid", priority=5, created_at_utc="2026-09-25T08:00:00+00:00"))
    assert [r.job_id for r in store.list_jobs()] == ["high", "mid", "low"]


def test_list_jobs_equal_priority_is_fifo(store: HostStore) -> None:
    store.insert_job(job("second", created_at_utc="2026-09-25T10:00:00+00:00"))
    store.insert_job(job("first", created_at_utc="2026-09-25T09:00:00+00:00"))
    assert [r.job_id for r in store.list_jobs()] == ["first", "second"]


def test_list_jobs_filters_by_state_group_and_both(store: HostStore) -> None:
    store.insert_job(job("a", state="queued", group_id="g1"))
    store.insert_job(job("b", state="running", group_id="g1"))
    store.insert_job(job("c", state="queued", group_id="g2"))
    assert [r.job_id for r in store.list_jobs(state="queued")] == ["a", "c"]
    assert [r.job_id for r in store.list_jobs(group_id="g1")] == ["a", "b"]
    assert [r.job_id for r in store.list_jobs(state="queued", group_id="g1")] == ["a"]


def test_update_job_progress(store: HostStore) -> None:
    store.insert_job(job())
    assert (
        store.update_job_progress(
            "job-1", progress_percent=50.0, progress_message="half"
        )
        is True
    )
    stored = store.get_job("job-1")
    assert stored is not None
    assert stored.progress_percent == 50.0
    assert stored.progress_message == "half"


def test_update_job_progress_boundaries_are_inclusive(store: HostStore) -> None:
    store.insert_job(job())
    assert store.update_job_progress("job-1", progress_percent=0.0, progress_message="")
    assert store.update_job_progress(
        "job-1", progress_percent=100.0, progress_message=""
    )


def test_update_job_progress_rejects_out_of_range(store: HostStore) -> None:
    store.insert_job(job())
    with pytest.raises(HostPersistenceValueError):
        store.update_job_progress("job-1", progress_percent=-0.1, progress_message="")


def test_update_job_progress_missing_job_returns_false(store: HostStore) -> None:
    assert (
        store.update_job_progress("job-1", progress_percent=1.0, progress_message="")
        is False
    )


def test_update_job_checkpoint(store: HostStore) -> None:
    store.insert_job(job())
    assert store.update_job_checkpoint("job-1", checkpoint_json='{"step": 3}') is True
    stored = store.get_job("job-1")
    assert stored is not None
    assert stored.checkpoint_json == '{"step": 3}'
    with pytest.raises(HostPersistenceValueError):
        store.update_job_checkpoint("job-1", checkpoint_json="{")
    assert store.update_job_checkpoint("job-9", checkpoint_json="{}") is False


def test_transition_job_moves_state_and_fills_timestamps(store: HostStore) -> None:
    store.insert_job(job())
    moved = store.transition_job(
        "job-1",
        from_state="queued",
        to_state="running",
        started_at_utc="2026-09-25T10:02:00+00:00",
    )
    assert moved.state == "running"
    assert moved.started_at_utc == "2026-09-25T10:02:00+00:00"
    assert store.get_job("job-1") == moved


def test_transition_job_preserves_timestamps_not_supplied(store: HostStore) -> None:
    store.insert_job(job())
    store.transition_job(
        "job-1", from_state="queued", to_state="running", started_at_utc="T1"
    )
    done = store.transition_job(
        "job-1",
        from_state="running",
        to_state="completed",
        completed_at_utc="T2",
        terminal_reason="finished",
    )
    assert done.started_at_utc == "T1"
    assert done.completed_at_utc == "T2"
    assert done.terminal_reason == "finished"


def test_transition_job_rejects_wrong_expected_state(store: HostStore) -> None:
    store.insert_job(job())
    with pytest.raises(HostPersistenceConflictError):
        store.transition_job("job-1", from_state="running", to_state="completed")


def test_transition_job_rejects_missing_job(store: HostStore) -> None:
    with pytest.raises(HostPersistenceConflictError):
        store.transition_job("job-1", from_state="queued", to_state="running")


def test_delete_job_cascades_children(seeded_store: HostStore) -> None:
    seeded_store.create_attempt(attempt())
    seeded_store.record_event(event())
    assert seeded_store.delete_job("job-1") is True
    assert seeded_store.get_job("job-1") is None
    assert seeded_store.get_attempt("att-1") is None
    assert seeded_store.list_events("job-1") == []
    assert seeded_store.get_lease("lease-1") is None
    assert seeded_store.delete_job("job-1") is False


# -- host_job_attempts ---------------------------------------------------------


def test_create_and_get_attempt_round_trip(store: HostStore) -> None:
    store.insert_job(job())
    record = attempt()
    store.create_attempt(record)
    assert store.get_attempt("att-1") == record


def test_get_attempt_missing_returns_none(store: HostStore) -> None:
    assert store.get_attempt("att-1") is None


def test_create_attempt_rejects_missing_parent(store: HostStore) -> None:
    with pytest.raises(HostPersistenceConflictError):
        store.create_attempt(attempt())


def test_create_attempt_rejects_duplicate(store: HostStore) -> None:
    store.insert_job(job())
    store.create_attempt(attempt())
    with pytest.raises(HostPersistenceConflictError):
        store.create_attempt(attempt())


def test_create_attempt_rejects_malformed_checkpoint(store: HostStore) -> None:
    store.insert_job(job())
    with pytest.raises(HostPersistenceValueError):
        store.create_attempt(replace(attempt(), checkpoint_json="{bad"))


def test_list_attempts_orders_by_sequence(store: HostStore) -> None:
    store.insert_job(job())
    store.create_attempt(replace(attempt("att-2"), sequence=2))
    store.create_attempt(replace(attempt("att-1"), sequence=1))
    assert [a.attempt_id for a in store.list_attempts("job-1")] == ["att-1", "att-2"]


def test_update_attempt_heartbeat(store: HostStore) -> None:
    store.insert_job(job())
    store.create_attempt(attempt())
    assert store.update_attempt_heartbeat("att-1", heartbeat_at_utc="T1") is True
    stored = store.get_attempt("att-1")
    assert stored is not None
    assert stored.heartbeat_at_utc == "T1"
    assert store.update_attempt_heartbeat("att-9", heartbeat_at_utc="T1") is False


def test_update_attempt_checkpoint(store: HostStore) -> None:
    store.insert_job(job())
    store.create_attempt(attempt())
    assert store.update_attempt_checkpoint("att-1", checkpoint_json="[1]") is True
    stored = store.get_attempt("att-1")
    assert stored is not None
    assert stored.checkpoint_json == "[1]"
    with pytest.raises(HostPersistenceValueError):
        store.update_attempt_checkpoint("att-1", checkpoint_json="nope")


def test_complete_attempt_sets_terminal_fields(store: HostStore) -> None:
    store.insert_job(job())
    store.create_attempt(attempt())
    assert (
        store.complete_attempt("att-1", state="succeeded", completed_at_utc="T2")
        is True
    )
    stored = store.get_attempt("att-1")
    assert stored is not None
    assert stored.state == "succeeded"
    assert stored.completed_at_utc == "T2"
    assert (
        store.complete_attempt("att-9", state="succeeded", completed_at_utc="T2")
        is False
    )


# -- host_job_events -------------------------------------------------------------


def test_record_and_list_events_round_trip(store: HostStore) -> None:
    store.insert_job(job())
    record = event()
    store.record_event(record)
    assert store.list_events("job-1") == [record]


def test_event_optional_fields_persist(store: HostStore) -> None:
    store.insert_job(job())
    store.record_event(
        HostJobEventRecord(
            event_id="evt-x",
            job_id="job-1",
            to_state="running",
            details_json="{}",
            created_at_utc="2026-09-25T10:00:00+00:00",
        )
    )
    stored = stored_event(store, "evt-x")
    assert stored is not None
    assert stored.attempt_id is None
    assert stored.from_state is None


def test_list_events_orders_by_time_then_id(store: HostStore) -> None:
    store.insert_job(job())
    store.record_event(event("evt-b"))
    store.record_event(
        replace(event("evt-a"), created_at_utc="2026-09-25T09:00:00+00:00")
    )
    assert [e.event_id for e in store.list_events("job-1")] == ["evt-a", "evt-b"]


def test_record_event_rejects_malformed_details(store: HostStore) -> None:
    with pytest.raises(HostPersistenceValueError):
        store.record_event(replace(event(), details_json="{bad"))


def test_record_event_rejects_duplicate(store: HostStore) -> None:
    store.insert_job(job())
    store.record_event(event())
    with pytest.raises(HostPersistenceConflictError):
        store.record_event(event())


# -- host_grid_nodes and host_grid_leases ------------------------------------------


def test_upsert_node_inserts_then_refreshes(store: HostStore) -> None:
    store.upsert_node(node())
    store.upsert_node(replace(node(), port=9002, cores=8))
    stored = store.get_node("node-1")
    assert stored is not None
    assert stored.port == 9002
    assert stored.cores == 8
    assert stored.host == "127.0.0.1"


def test_get_and_list_nodes(store: HostStore) -> None:
    store.upsert_node(node("node-2"))
    store.upsert_node(node("node-1"))
    assert store.get_node("node-9") is None
    assert [n.node_id for n in store.list_nodes()] == ["node-1", "node-2"]


def test_update_node_heartbeat(store: HostStore) -> None:
    store.upsert_node(node())
    assert store.update_node_heartbeat("node-1", heartbeat_at_utc="T1") is True
    stored = store.get_node("node-1")
    assert stored is not None
    assert stored.last_heartbeat_utc == "T1"
    assert store.update_node_heartbeat("node-9", heartbeat_at_utc="T1") is False


def test_delete_node_blocked_by_active_lease(seeded_store: HostStore) -> None:
    with pytest.raises(HostPersistenceConflictError):
        seeded_store.delete_node("node-1")


def test_delete_node_blocked_until_lease_history_removed(
    seeded_store: HostStore,
) -> None:
    assert seeded_store.release_lease("lease-1", state="released") is True
    with pytest.raises(HostPersistenceConflictError):
        seeded_store.delete_node("node-1")
    assert seeded_store.delete_lease("lease-1") is True
    assert seeded_store.delete_node("node-1") is True
    assert seeded_store.get_node("node-1") is None
    assert seeded_store.delete_node("node-1") is False


def test_insert_and_get_lease_round_trip(seeded_store: HostStore) -> None:
    assert seeded_store.get_lease("lease-1") == lease()


def test_insert_lease_rejects_missing_node(store: HostStore) -> None:
    store.insert_job(job())
    with pytest.raises(HostPersistenceConflictError):
        store.insert_lease(lease())


def test_insert_lease_rejects_missing_job(store: HostStore) -> None:
    store.upsert_node(node())
    with pytest.raises(HostPersistenceConflictError):
        store.insert_lease(lease())


def test_insert_lease_rejects_duplicate(seeded_store: HostStore) -> None:
    with pytest.raises(HostPersistenceConflictError):
        seeded_store.insert_lease(lease())


def test_list_leases_filters_by_state(seeded_store: HostStore) -> None:
    seeded_store.insert_lease(
        lease("lease-2", expires_at_utc="2026-09-25T12:00:00+00:00")
    )
    assert [e.lease_id for e in seeded_store.list_leases()] == ["lease-1", "lease-2"]
    active = seeded_store.list_leases(state=ACTIVE_LEASE_STATE)
    assert [e.lease_id for e in active] == ["lease-1", "lease-2"]


def test_release_lease(seeded_store: HostStore) -> None:
    assert seeded_store.release_lease("lease-1", state="released") is True
    stored = seeded_store.get_lease("lease-1")
    assert stored is not None
    assert stored.state == "released"
    assert seeded_store.release_lease("lease-9", state="released") is False


def test_expire_leases_flips_only_strictly_expired(seeded_store: HostStore) -> None:
    seeded_store.insert_lease(
        lease("lease-future", expires_at_utc="2026-09-25T12:00:00+00:00")
    )
    expired = seeded_store.expire_leases(now_utc="2026-09-25T11:00:01+00:00")
    assert [e.lease_id for e in expired] == ["lease-1"]
    stored = seeded_store.get_lease("lease-1")
    assert stored is not None
    assert stored.state == EXPIRED_LEASE_STATE
    future = seeded_store.get_lease("lease-future")
    assert future is not None
    assert future.state == ACTIVE_LEASE_STATE


def test_expire_leases_boundary_equality_stays_active(seeded_store: HostStore) -> None:
    expired = seeded_store.expire_leases(now_utc="2026-09-25T11:00:00+00:00")
    assert expired == []
    boundary = seeded_store.get_lease("lease-1")
    assert boundary is not None
    assert boundary.state == ACTIVE_LEASE_STATE


def test_delete_lease(seeded_store: HostStore) -> None:
    assert seeded_store.delete_lease("lease-1") is True
    assert seeded_store.get_lease("lease-1") is None
    assert seeded_store.delete_lease("lease-1") is False


# -- integrity translation --------------------------------------------------------


def test_unrecognized_integrity_error_is_wrapped() -> None:
    error = sqlite3.IntegrityError("NOT NULL constraint failed: host_jobs.state")
    with pytest.raises(HostPersistenceError) as info:
        _raise_for_integrity(error, context="Job")
    assert not isinstance(info.value, HostPersistenceConflictError)


def test_unique_integrity_error_becomes_conflict() -> None:
    error = sqlite3.IntegrityError("UNIQUE constraint failed: host_jobs.job_id")
    with pytest.raises(HostPersistenceConflictError, match="already exists"):
        _raise_for_integrity(error, context="Job")


def test_foreign_key_integrity_error_becomes_conflict() -> None:
    error = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
    with pytest.raises(HostPersistenceConflictError, match="missing"):
        _raise_for_integrity(error, context="Job attempt")


def test_shared_store_survives_repeated_use(store: HostStore) -> None:
    for index in range(5):
        store.upsert_setting(
            setting(key=f"key.{index}", value_json=f'{{"i": {index}}}')
        )
    assert len(store.list_settings()) == 5


# -- read-only settings access -------------------------------------------------


def test_read_settings_returns_every_record_ordered(store: HostStore) -> None:
    store.upsert_setting(setting(scope="host", key="host.runtime"))
    store.upsert_setting(setting(scope="application", key="app.network"))
    store.upsert_setting(setting(scope="application", key="app.general"))
    records = read_settings(store._path)
    assert [(r.scope, r.key) for r in records] == [
        ("application", "app.general"),
        ("application", "app.network"),
        ("host", "host.runtime"),
    ]


def test_read_settings_rejects_missing_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(HostPersistenceSchemaError):
        read_settings(missing)
    assert not missing.exists()


def test_read_settings_rejects_non_sqlite_file(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_text("this is not a database", encoding="utf-8")
    with pytest.raises(HostPersistenceSchemaError):
        read_settings(corrupt)


def test_read_settings_rejects_drifted_table(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    connection.execute("DROP TABLE host_settings")
    connection.execute("CREATE TABLE host_settings (scope TEXT)")
    connection.commit()
    connection.close()
    with pytest.raises(HostPersistenceSchemaError):
        read_settings(database_path)


def test_read_settings_does_not_create_or_modify(store: HostStore) -> None:
    store.upsert_setting(setting())
    before = hashlib.sha256(store._path.read_bytes()).digest()
    assert read_settings(store._path)[0].key == "app.general"
    assert hashlib.sha256(store._path.read_bytes()).digest() == before


def test_read_settings_tolerates_absent_other_tables(
    database_path: Path, store: HostStore
) -> None:
    store.upsert_setting(setting())
    connection = sqlite3.connect(database_path)
    for table in (
        "host_grid_leases",
        "host_grid_nodes",
        "host_job_events",
        "host_job_attempts",
        "host_jobs",
    ):
        connection.execute(f"DROP TABLE {table}")
    connection.commit()
    connection.close()
    records = read_settings(database_path)
    assert [r.key for r in records] == ["app.general"]
