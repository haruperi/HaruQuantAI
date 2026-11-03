"""Isolated test suite for HostPersistence SQLite isolation, WAL mode, and schemas.

Description:
    Tests schema creation idempotency, transaction scopes, parameter binding,
    foreign key enforcement, and bounded CRUD operations on temporary isolated stores.
Purpose:
    FEAT-HOST-PERSISTENCE: Maintain host schema and transaction authority.
Key Capabilities:
    - FR-test-host-persistence: Verify ACID transactions, SQLite isolation,
      bounded CRUD, and host schema integrity.
Python API Usage:
    Run pytest against this module.
CLI Usage:
    uv run pytest tests/core/host/test_persistence.py --no-cov
"""

import ast
import json
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from app.core.host.persistence import (
    HostPersistence,
    PersistenceTransactionError,
    RecordFilter,
)


@pytest.fixture
def gateway(tmp_path):
    path = tmp_path / "database.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE items (
            ID INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'default',
            score REAL NOT NULL DEFAULT 0 CHECK (score >= 0),
            payload BLOB,
            doubled REAL GENERATED ALWAYS AS (score * 2) VIRTUAL
        );
        CREATE TABLE children (
            id INTEGER PRIMARY KEY,
            item_id INTEGER REFERENCES items(ID) ON DELETE CASCADE
        );
        CREATE TABLE pairs (
            scope TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (scope, key)
        ) WITHOUT ROWID;
        CREATE TABLE pair_children (
            id INTEGER PRIMARY KEY, scope TEXT, key TEXT,
            FOREIGN KEY (scope, key) REFERENCES pairs ON DELETE SET NULL
        );
        CREATE TABLE nullable_keys (id TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE "odd table" ("a""b" TEXT PRIMARY KEY);
    """)
    connection.close()
    return HostPersistence(path)


def records(response):
    assert response["success"], response
    json.dumps(response, allow_nan=False)
    return response["data"]["records"]


def error_code(response, expected):
    assert response["success"] is False, response
    assert response["data"] is None
    assert response["error"]["code"] == expected
    assert not response["metadata"]["side_effects"]


def test_crud_defaults_wal_and_blob(gateway):
    result = gateway.create_records("items", {"name": "one", "payload": b"\xff\x00"})
    row = records(result)[0]
    assert row["ID"] == 1
    assert row["category"] == "default"
    assert row["payload"] == {"$binary": "/wA="}
    assert result["metadata"]["side_effects"]
    updated = gateway.update_record("items", {"score": 3}, filters={"ID": 1})
    assert records(updated)[0]["doubled"] == 6
    assert records(gateway.read_records("items", filters={"ID": 1}))[0]["score"] == 3
    assert (
        records(gateway.delete_record("items", filters={"ID": 1}))[0]["name"] == "one"
    )
    assert records(gateway.read_records("items")) == []
    connection = sqlite3.connect(gateway.database_path)
    try:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    finally:
        connection.close()


def test_batch_is_atomic_for_constraints_and_invalid_later_rows(gateway):
    result = gateway.create_records(
        "items", [{"name": "duplicate"}, {"name": "duplicate"}]
    )
    error_code(result, "conflict")
    assert records(gateway.read_records("items")) == []
    result = gateway.create_records("items", [{"name": "valid"}, {"unknown": 1}])
    error_code(result, "validation")
    assert records(gateway.read_records("items")) == []
    error_code(
        gateway.create_records("items", {"name": "bad", "score": -1}), "conflict"
    )


def test_batch_defaults_and_quoted_identifiers(gateway):
    result = gateway.create_records("items", [{"name": "a"}, {"name": "b", "score": 2}])
    assert [row["score"] for row in records(result)] == [0, 2]
    assert records(gateway.create_records("children", {}))[0]["item_id"] is None
    assert (
        records(gateway.create_records("odd table", {'a"b': "safe"}))[0]['a"b']
        == "safe"
    )


def test_parameter_binding_and_identifier_validation(gateway):
    attack = "'; DROP TABLE items; --"
    records(gateway.create_records("items", {"name": attack}))
    assert (
        records(gateway.read_records("items", filters={"name": attack}))[0]["name"]
        == attack
    )
    error_code(gateway.read_records("items; DROP TABLE items"), "not_found")
    error_code(gateway.read_records("items", filters={"ID OR 1=1": 1}), "validation")
    error_code(
        gateway.read_records("items", order_by=["ID DESC; DROP TABLE items"]),
        "validation",
    )
    error_code(
        gateway.create_records("items", {"name": "x", "doubled": 4}), "validation"
    )
    error_code(gateway.read_records("sqlite_sequence"), "validation")
    assert len(records(gateway.read_records("items"))) == 1


def test_filter_operators_projection_and_offset_pagination(gateway):
    records(
        gateway.create_records(
            "items", [{"name": f"item-{i}", "score": i} for i in range(5)]
        )
    )
    result = gateway.read_records(
        "items",
        filters=[
            RecordFilter("score", "gte", 1),
            RecordFilter("name", "like", "item-%"),
        ],
        columns=["name"],
        order_by=["score"],
        descending=True,
        limit=2,
        offset=1,
    )
    assert records(result) == [{"name": "item-3"}, {"name": "item-2"}]
    assert result["data"]["pagination"]["next_offset"] == 3
    assert (
        len(
            records(
                gateway.read_records(
                    "items", filters=[RecordFilter("ID", "in", [1, 3])]
                )
            )
        )
        == 2
    )
    assert (
        records(gateway.read_records("items", filters=[RecordFilter("ID", "in", [])]))
        == []
    )
    assert (
        len(
            records(
                gateway.read_records(
                    "items", filters=[RecordFilter("ID", "not_in", [])]
                )
            )
        )
        == 5
    )
    assert len(records(gateway.read_records("items", filters={"payload": None}))) == 5
    assert (
        records(
            gateway.read_records("items", filters=[RecordFilter("payload", "ne", None)])
        )
        == []
    )


@pytest.mark.parametrize("descending", [False, True])
def test_composite_cursor_pagination_without_skips(gateway, descending):
    keys = [("a", "1"), ("a", "2"), ("b", "1"), ("b", "2"), ("c", "1")]
    records(
        gateway.create_records(
            "pairs", [{"scope": scope, "key": key} for scope, key in keys]
        )
    )
    seen = []
    cursor = None
    while True:
        response = gateway.read_records(
            "pairs",
            pagination="cursor",
            cursor=cursor,
            limit=2,
            descending=descending,
        )
        seen.extend((row["scope"], row["key"]) for row in records(response))
        cursor = response["data"]["pagination"]["next_cursor"]
        if cursor is None:
            break
    assert seen == sorted(keys, reverse=descending)


def test_single_key_cursor_works_when_key_not_projected(gateway):
    records(gateway.create_records("items", [{"name": "a"}, {"name": "b"}]))
    response = gateway.read_records(
        "items", pagination="cursor", limit=1, columns=["name"]
    )
    assert records(response) == [{"name": "a"}]
    cursor = response["data"]["pagination"]["next_cursor"]
    assert cursor == {"ID": 1}
    response = gateway.read_records(
        "items", pagination="cursor", limit=1, columns=["name"], cursor=cursor
    )
    assert records(response) == [{"name": "b"}]
    assert not response["data"]["pagination"]["has_more"]


def test_null_primary_keys_require_offset_mode(gateway):
    records(gateway.create_records("nullable_keys", {"value": "null key"}))
    error_code(gateway.read_records("nullable_keys", pagination="cursor"), "validation")
    assert len(records(gateway.read_records("nullable_keys"))) == 1


@pytest.mark.parametrize(
    "options",
    [
        {"limit": 0},
        {"limit": 1001},
        {"limit": True},
        {"offset": -1},
        {"pagination": "unknown"},
        {"pagination": "cursor", "offset": 1},
        {"cursor": {"ID": 1}},
        {"columns": []},
        {"order_by": []},
        {"pagination": "cursor", "cursor": {"unknown": 1}},
        {"filters": [RecordFilter("name", "eq OR 1=1", "x")]},
        {"filters": [RecordFilter("ID", "in", [None])]},
    ],
)
def test_invalid_read_arguments(gateway, options):
    error_code(gateway.read_records("items", **options), "validation")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 2**63, {"nested": 1}])
def test_invalid_values(gateway, value):
    error_code(
        gateway.create_records("items", {"name": "bad", "score": value}), "validation"
    )


def test_write_guards_missing_ambiguous_and_unbounded_targets(gateway):
    records(gateway.create_records("items", [{"name": "a"}, {"name": "b"}]))
    error_code(gateway.update_record("items", {"score": 2}, filters={}), "validation")
    error_code(gateway.delete_record("items", filters=None), "validation")
    error_code(
        gateway.update_record("items", {"score": 2}, filters={"category": "default"}),
        "conflict",
    )
    error_code(
        gateway.update_record("items", {"score": 2}, filters={"ID": 99}), "not_found"
    )
    assert all(row["score"] == 0 for row in records(gateway.read_records("items")))


def test_foreign_keys_enforced_and_cascade_deletion_guarded(gateway):
    error_code(gateway.create_records("children", {"item_id": 99}), "conflict")
    records(gateway.create_records("items", [{"name": "parent"}, {"name": "free"}]))
    records(gateway.create_records("children", {"item_id": 1}))
    error_code(
        gateway.delete_record("items", filters={"category": "default"}), "conflict"
    )
    assert len(records(gateway.read_records("items"))) == 2
    records(gateway.delete_record("children", filters={"item_id": 1}))
    assert (
        len(records(gateway.delete_record("items", filters={"category": "default"})))
        == 2
    )


def test_composite_implicit_foreign_keys_guard_set_null(gateway):
    records(gateway.create_records("pairs", {"scope": "a", "key": "1"}))
    records(gateway.create_records("pair_children", {"scope": "a", "key": "1"}))
    error_code(
        gateway.delete_record("pairs", filters={"scope": "a", "key": "1"}), "conflict"
    )
    assert records(gateway.read_records("pair_children"))[0]["scope"] == "a"


def test_grouped_commit_rollback_and_closed_scope(gateway):
    with gateway.transaction() as tx:
        result = tx.create_records("items", {"name": "committed"})
        records(result)
        assert result["metadata"]["extensions"]["provisional"]
        assert records(gateway.read_records("items")) == []
    assert len(records(gateway.read_records("items"))) == 1
    error_code(tx.read_records("items"), "conflict")
    with pytest.raises(PersistenceTransactionError):
        with gateway.transaction() as tx:
            records(tx.create_records("items", {"name": "rolled back"}))
            error_code(tx.create_records("items", {"name": "committed"}), "conflict")
            error_code(tx.read_records("items"), "conflict")
    assert [row["name"] for row in records(gateway.read_records("items"))] == [
        "committed"
    ]
    with pytest.raises(RuntimeError, match="caller failed"):
        with gateway.transaction() as tx:
            records(tx.create_records("items", {"name": "exception rollback"}))
            raise RuntimeError("caller failed")
    assert len(records(gateway.read_records("items"))) == 1


def test_thread_safe_gateway_and_busy_failure(gateway):
    # Establish WAL before concurrent CRUD; changing journal mode is exclusive.
    records(gateway.read_records("items"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(
            pool.map(
                lambda i: gateway.create_records("items", {"name": f"item-{i}"}),
                range(12),
            )
        )
    assert all(response["success"] for response in responses), responses
    impatient = HostPersistence(gateway.database_path, timeout=0.05)
    with gateway.transaction() as tx:
        response = impatient.create_records("items", {"name": "blocked"})
        error_code(response, "unavailable")
        assert response["error"]["retryable"]
        assert len(records(gateway.read_records("items"))) == 12
        records(tx.update_record("items", {"score": 2}, filters={"ID": 1}))


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path / "missing.db"
    error_code(HostPersistence(path).read_records("items"), "unavailable")
    assert not path.exists()


def test_insert_batch_limit(gateway):
    error_code(gateway.create_records("items", []), "validation")
    error_code(gateway.create_records("items", [{"name": "x"}] * 1001), "validation")


def test_new_tables_discovered_without_recreating_gateway(gateway):
    connection = sqlite3.connect(gateway.database_path)
    try:
        connection.execute("CREATE TABLE added_later (id INTEGER PRIMARY KEY)")
    finally:
        connection.close()
    assert records(gateway.create_records("added_later", {}))[0]["id"] == 1


def test_database_imports_stay_in_gateway():
    root = Path(__file__).resolve().parents[3] / "app"
    for path in root.rglob("*.py"):
        if path == root / "core" / "host" / "persistence.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert all(
                    alias.name.split(".")[0] != "sqlite3" for alias in node.names
                ), path
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] != "sqlite3", path


def test_operation_logs_omit_record_values(gateway, caplog):
    secret = "private-value-not-for-logs"
    with caplog.at_level(logging.DEBUG, logger="app.core.host.persistence"):
        records(gateway.create_records("items", {"name": secret}))
        error_code(gateway.create_records("items", {"name": secret}), "conflict")
    assert "operation=create_records completed" in caplog.text
    assert "code=conflict" in caplog.text
    assert "cause=IntegrityError" in caplog.text
    assert secret not in caplog.text


def test_grouped_transaction_logs_commit_and_rollback(gateway, caplog):
    with caplog.at_level(logging.DEBUG, logger="app.core.host.persistence"):
        with gateway.transaction() as tx:
            records(tx.create_records("items", {"name": "committed"}))
        with pytest.raises(PersistenceTransactionError):
            with gateway.transaction() as tx:
                error_code(
                    tx.create_records("items", {"name": "committed"}), "conflict"
                )
    assert "Persistence transaction started" in caplog.text
    assert "Persistence transaction committed" in caplog.text
    assert "Persistence transaction rolled back" in caplog.text


def test_code_editor_schema_isolated(tmp_path, caplog):
    path = tmp_path / "ce.db"
    path.touch()
    gateway = HostPersistence(path)
    with caplog.at_level(logging.INFO, logger="app.core.host.persistence"):
        res = gateway.ensure_code_editor_schema()
    assert res["success"]
    assert "FR-host-code-editor-schema: verified" in caplog.text

    created = gateway.create_records(
        "code_editor_state", {"id": "session_1", "payload": '{"cursor": 10}'}
    )
    assert records(created)[0]["id"] == "session_1"


def test_custom_data_schema_isolated(tmp_path, caplog):
    path = tmp_path / "cd.db"
    path.touch()
    gateway = HostPersistence(path)
    with caplog.at_level(logging.INFO, logger="app.core.host.persistence"):
        res = gateway.ensure_custom_data_schema()
    assert res["success"]
    assert "FR-host-custom-data-schema: verified" in caplog.text

    gateway.create_records(
        "datamgr_custom",
        {
            "id": "ind_1",
            "name": "CustomRSI",
            "data_type": "indicator",
            "timeframe": "M1",
            "values_json": "[]",
            "system": 0,
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    val = gateway.create_records(
        "datamgr_custom_values",
        {
            "indicator_id": "ind_1",
            "timestamp": "2026-01-01T00:00:00Z",
            "values_json": "[1.0, 2.0]",
        },
    )
    assert records(val)[0]["indicator_id"] == "ind_1"


def test_datasets_schema_and_migrations_isolated(tmp_path, caplog):
    path = tmp_path / "datasets.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE datamgr_datasets (
            id TEXT PRIMARY KEY, source TEXT NOT NULL, symbol TEXT NOT NULL,
            underlying TEXT NOT NULL, timeframe TEXT NOT NULL, broker TEXT NOT NULL,
            timezone TEXT NOT NULL, category TEXT NOT NULL, date_from TEXT NOT NULL,
            date_to TEXT NOT NULL, bars INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            path TEXT NOT NULL DEFAULT '', data_kind TEXT NOT NULL DEFAULT 'bars',
            quality_score REAL NOT NULL DEFAULT 1.0, lineage_json TEXT NOT NULL DEFAULT '{}',
            schema_version INTEGER NOT NULL DEFAULT 1,
            instrument TEXT, broker_name TEXT
        );
        CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        INSERT INTO datamgr_broker (id, name) VALUES (1, '[[ Interactive Brokers ]]');
        INSERT INTO datamgr_datasets (
            id, source, symbol, underlying, timeframe, broker, timezone,
            category, date_from, date_to, created_at, updated_at, instrument, broker_name
        ) VALUES (
            'ds_1', 'csv', 'EURUSD', 'EURUSD', 'H1', '1', 'UTC',
            'Forex', '2026-01-01', '2026-01-02', '2026-01-01', '2026-01-02', 'legacy_inst', 'legacy_broker'
        );
    """)
    conn.close()

    gateway = HostPersistence(path)
    with caplog.at_level(logging.INFO, logger="app.core.host.persistence"):
        res = gateway.ensure_datasets_schema()
    assert res["success"]
    assert "FR-host-datasets-schema: verified" in caplog.text

    # Verify column removal and broker migration
    read = gateway.read_records("datamgr_datasets", filters={"id": "ds_1"})
    row = records(read)[0]
    assert row["broker"] == "Interactive Brokers"
    assert "instrument" not in row
    assert "broker_name" not in row
    assert "symbol_definition_id" in row
    assert "session_id" in row


def test_broker_cost_schema_isolated(tmp_path, caplog):
    path = tmp_path / "brokers.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE datamgr_broker (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        INSERT INTO datamgr_broker (id, name) VALUES (1, 'TestBroker');
    """)
    conn.close()

    gateway = HostPersistence(path)
    with caplog.at_level(logging.INFO, logger="app.core.host.persistence"):
        res = gateway.ensure_broker_cost_schema()
    assert res["success"]
    assert "FR-host-broker-cost-schema: verified" in caplog.text

    row = records(gateway.read_records("datamgr_broker", filters={"id": 1}))[0]
    assert row["spread_model_json"] == '{"model":"inherit"}'
    assert row["commission_model_json"] == '{"model":"inherit"}'


def test_databanks_schema_isolated(tmp_path, caplog):
    path = tmp_path / "databanks.db"
    path.touch()
    gateway = HostPersistence(path)
    with caplog.at_level(logging.INFO, logger="app.core.host.persistence"):
        res = gateway.ensure_databanks_schema()
    assert res["success"]
    assert "FR-host-databanks-schema: verified" in caplog.text

    gateway.create_records(
        "databank_results",
        {
            "id": "res_1",
            "databank_id": "db_main",
            "strategy_id": "strat_1",
            "strategy_name": "Strategy 1",
            "net_profit": 1500.0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    gateway.create_records(
        "databank_results",
        {
            "id": "res_2",
            "databank_id": "db_main",
            "strategy_id": "strat_2",
            "strategy_name": "Strategy 2",
            "net_profit": 2500.0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    rows = records(
        gateway.read_records(
            "databank_results",
            filters={"databank_id": "db_main"},
            order_by=["net_profit"],
            descending=True,
        )
    )
    assert len(rows) == 2
    assert rows[0]["id"] == "res_2"
    assert rows[1]["id"] == "res_1"


def test_timeout_and_transaction_edge_cases(tmp_path):
    path = tmp_path / "timeout.db"
    with pytest.raises(ValueError, match="timeout must be finite and positive"):
        HostPersistence(path, timeout=0)
    with pytest.raises(ValueError, match="timeout must be finite and positive"):
        HostPersistence(path, timeout=-1.0)
    with pytest.raises(ValueError, match="timeout must be finite and positive"):
        HostPersistence(path, timeout=float("nan"))
    with pytest.raises(ValueError, match="timeout must be finite and positive"):
        HostPersistence(path, timeout=float("inf"))

    path.touch()
    gateway = HostPersistence(path)
    with gateway.transaction() as tx:
        # Re-entrant transaction on scoped transaction gateway should raise
        with pytest.raises(
            PersistenceTransactionError, match="Nested transactions are not supported"
        ):
            with tx.transaction():
                pass
