"""Unit tests for app.host.settings module.

Validates the SQLite persistence store (host_settings table), schema creation,
seeding, dot-access navigation, validation engine, revision conflict detection,
cached access, validated updates and persistence delegation.
"""

from __future__ import annotations

import logging
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from app.host.bootstrap import HostRuntime
from app.host.persistence import (
    MAX_BATCH_SIZE,
    CorruptDataError,
    IncompatibleSchemaError,
    PersistenceError,
    RevisionConflictError,
    SettingsStore,
    ValidationError,
    canonical_json,
    validate_identifier,
)
from app.host.settings import (
    SETTINGS_GROUPS,
    HostSettings,
    _field_value,
    consolidate_settings,
    create_settings_router,
    effective_settings_values,
    settings_catalogue,
    validate_configuration_values,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_catalogue_uses_canonical_backend_port(temp_db: Path) -> None:
    """The port control has one JSON source even before explicit legacy cleanup."""
    store = SettingsStore(temp_db)
    store.initialize()
    store.update_batch(
        {
            "application": {"app_general": {"backend_port": 8123}},
            "host": {"bound_port": {"port": 8000}},
        }
    )
    target = HostSettings(temp_db)
    fields = settings_catalogue(target.get_snapshot())["fields"]
    assert not any(field["key"] == "bound_port" for field in fields)
    port = [field for field in fields if field["key"] == "backend_port"]
    assert len(port) == 1
    assert port[0]["value"] == 8123
    assert not port[0]["readonly"]
    revision, _ = store.read_all()
    store.update_batch(
        {}, expected_revision=revision, deletions=(("host", "bound_port"),)
    )
    target.reload()
    target.update({"app.general": {"backend_port": 8124}})
    assert target.app_general.backend_port == 8124
    assert ("host", "bound_port") not in {(r.scope, r.key) for r in store.read_all()[1]}


@pytest.mark.parametrize(
    ("scope", "key", "value"),
    [
        ("config.global", "data_frame_guard", "guess"),
        ("config.memory", "cleanup_interval_mins", True),
        ("config.memory", "cleanup_interval_mins", 7),
        ("config.databanks", "databank_sync_interval_mins", False),
        ("config.memory", "gc_type", "unknown"),
        ("config.global", "default_result_to_display", "unknown"),
        ("config.performance", "compute_separate_metrics", "yes"),
    ],
)
def test_configuration_contract_rejection_logs(
    scope: str, key: str, value: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """Reject unsupported preference values without silently accepting bad storage."""
    caplog.set_level(logging.WARNING)
    with pytest.raises(ValidationError, match="Unsupported value"):
        validate_configuration_values(scope, key, value)
    assert any(
        "FR-HOST-SETTINGS-VALIDATION" in record.message for record in caplog.records
    )


def test_configuration_preferences_database_round_trip(temp_db: Path) -> None:
    """Round-trip every displayed preference through a real isolated database."""
    values: dict[str, dict[str, Any]] = {
        "app.general": {"header_custom_text": "Header"},
        "config.global": {
            "sounds_off": True,
            "advanced_file_chooser": False,
            "show_control_orders": True,
            "footer_custom_text": "Footer",
            "default_result_to_display": "Main",
            "data_frame_guard": "stop",
        },
        "config.cpu": {
            "core_usage": "custom",
            "custom_cores": 3,
            "high_priority": True,
        },
        "config.performance": {
            "compute_pips_metrics": True,
            "compute_pcts_metrics": True,
            "compute_separate_metrics": False,
        },
        "config.memory": {
            "gc_type": "G1GC",
            "automatic_memory": True,
            "memory_limit_gb": 6,
            "dont_store_pending_orders": False,
            "memory_cleanup": True,
            "cleanup_interval_mins": 0,
        },
        "config.databanks": {
            "databank_sync_interval_mins": 60,
            "sync_databanks_after_task_done": False,
            "store_chart_data": True,
        },
        "config.optimizations": {"dont_store_op_3d_charts_data": False},
        "config.troubleshooting": {
            "gpu_accelerated": False,
            "memory_protection": False,
            "debug_level_active": True,
        },
    }
    settings = HostSettings(temp_db)
    settings.update(values, expected_revision=settings.revision)
    fresh = HostSettings(temp_db)
    snapshot = fresh.get_snapshot()
    for scope, fields in values.items():
        for key, value in fields.items():
            assert effective_settings_values(snapshot.values)[scope][key] == value
    for guard in ("warn", "stop", "off"):
        fresh.update({"config.global": {"data_frame_guard": guard}})
        assert (
            HostSettings(temp_db)
            .get_snapshot()
            .values["application"]["config_global"]["data_frame_guard"]
            == guard
        )
    for minutes in (0, 5, 15, 30, 60):
        fresh.update({"config.memory": {"cleanup_interval_mins": minutes}})
        assert (
            HostSettings(temp_db)
            .get_snapshot()
            .values["application"]["config_memory"]["cleanup_interval_mins"]
            == minutes
        )
    for sync_minutes in (None, 0, 5, 10, 15, 60):
        fresh.update(
            {"config.databanks": {"databank_sync_interval_mins": sync_minutes}}
        )
        assert (
            HostSettings(temp_db)
            .get_snapshot()
            .values["application"]["config_databanks"]["databank_sync_interval_mins"]
            == sync_minutes
        )


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Provide an isolated temporary SQLite database path."""
    return tmp_path / "test_haruquantai.db"


@pytest.fixture
def initialized_store(temp_db: Path) -> SettingsStore:
    """Provide an initialized SettingsStore on an isolated temporary database with test records."""
    store = SettingsStore(temp_db)
    store.initialize()
    conn = sqlite3.connect(temp_db)
    conn.execute(
        """
        INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
        VALUES
            ('app.general', 'theme', '"dark"', 1, '2026-10-07T00:00:00Z'),
            ('app.general', 'language', '"en"', 1, '2026-10-07T00:00:00Z'),
            ('app.general', 'zoom', '1.0', 1, '2026-10-07T00:00:00Z'),
            ('config.global', 'advanced_file_chooser', 'true', 1, '2026-10-07T00:00:00Z'),
            ('config.global', 'default_result_to_display', '"Portfolio"', 1, '2026-10-07T00:00:00Z'),
            ('config.global', 'sounds_off', 'false', 1, '2026-10-07T00:00:00Z'),
            ('config.cpu', 'core_usage', '"all_except_one"', 1, '2026-10-07T00:00:00Z'),
            ('config.cpu', 'custom_cores', '7', 1, '2026-10-07T00:00:00Z'),
            ('config.memory', 'memory_limit_gb', '10', 1, '2026-10-07T00:00:00Z'),
            ('workspace_paths', 'configs_dir', '"data/configs"', 1, '2026-10-07T00:00:00Z'),
            ('workspace_paths', 'data_dir', '"data"', 1, '2026-10-07T00:00:00Z'),
            ('workspace_paths', 'projects_dir', '"data/projects"', 1, '2026-10-07T00:00:00Z'),
            ('workspace_paths', 'strategies_dir', '"data/strategies"', 1, '2026-10-07T00:00:00Z')
        """
    )
    conn.commit()
    conn.close()
    return store


@pytest.fixture
def host_settings(initialized_store: SettingsStore, temp_db: Path) -> HostSettings:
    """Provide a HostSettings instance connected to an isolated temporary database."""
    _, rows = initialized_store.read_all()
    application: dict[str, dict[str, Any]] = {}
    for row in rows:
        group = SETTINGS_GROUPS.get(row.scope, row.scope)
        application.setdefault(group, {})[row.key] = row.value
    with sqlite3.connect(temp_db) as conn:
        conn.execute("DELETE FROM host_settings WHERE scope != '_system'")
        conn.executemany(
            "INSERT INTO host_settings(scope,key,value_json,schema_version,updated_at_utc) VALUES ('application',?,?,1,'2026-10-07T00:00:00Z')",
            [(group, canonical_json(fields)) for group, fields in application.items()],
        )
    conn.close()
    return HostSettings(temp_db, auto_load=True)


def test_settings_store_initialize_and_seed(temp_db: Path) -> None:
    """Test table creation and schema initialization."""
    store = SettingsStore(temp_db)
    assert not temp_db.exists()

    store.initialize()
    assert temp_db.exists()
    assert store.get_revision() == 1

    # Verify table structure directly
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='host_settings'"
    )
    assert cur.fetchone() is not None

    cur.execute("SELECT COUNT(*) FROM host_settings")
    count = cur.fetchone()[0]
    assert count >= 1  # Revision key present
    conn.close()

    # Re-initialization should be idempotent
    store.initialize()
    assert store.get_revision() == 1


def test_settings_store_schema_validation_failure(temp_db: Path) -> None:
    """Test IncompatibleSchemaError when host_settings has mismatched schema,
    and verify existing unrelated tables are not mutated or dropped."""
    conn = sqlite3.connect(temp_db)
    # Create invalid table without required columns
    conn.execute("CREATE TABLE host_settings (wrong_col TEXT)")
    # Create unrelated legacy table with data
    conn.execute("CREATE TABLE source_datasets (id TEXT PRIMARY KEY, val TEXT)")
    conn.execute("INSERT INTO source_datasets VALUES ('d1', 'v1')")
    conn.commit()
    conn.close()

    store = SettingsStore(temp_db)
    with pytest.raises(IncompatibleSchemaError):
        store.initialize()

    # Unrelated legacy table must still exist with data intact
    check_conn = sqlite3.connect(temp_db)
    try:
        row = check_conn.execute(
            "SELECT val FROM source_datasets WHERE id = 'd1'"
        ).fetchone()
        assert row is not None
        assert row[0] == "v1"
        # And full core schema was not generated
        tables = {
            r[0]
            for r in check_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "host_jobs" not in tables
        assert "datamgr_datasets" not in tables
    finally:
        check_conn.close()


def test_settings_store_corrupt_data(temp_db: Path) -> None:
    """Test CorruptDataError on invalid JSON or bad schema version."""
    store = SettingsStore(temp_db)
    store.initialize()

    conn = sqlite3.connect(temp_db)
    # Insert invalid JSON
    conn.execute(
        """
        INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
        VALUES ('test', 'corrupt', '{invalid json', 1, '2026-10-07T00:00:00Z')
        """
    )
    conn.commit()
    conn.close()

    with pytest.raises(CorruptDataError):
        store.read_settings("test", key="corrupt")

    # Insert unsupported schema version
    conn = sqlite3.connect(temp_db)
    conn.execute(
        """
        INSERT INTO host_settings (scope, key, value_json, schema_version, updated_at_utc)
        VALUES ('test', 'bad_ver', '\"ok\"', 99, '2026-10-07T00:00:00Z')
        """
    )
    conn.commit()
    conn.close()

    with pytest.raises(CorruptDataError):
        store.read_settings("test", key="bad_ver")


def test_settings_store_read_and_pagination(initialized_store: SettingsStore) -> None:
    """Test single-key lookup, missing keys, and keyset pagination."""
    # Single key read
    page = initialized_store.read_settings("app.general", key="theme")
    assert len(page.items) == 1
    assert page.items[0].value == "dark"
    assert page.next_key is None

    # Missing key
    missing = initialized_store.read_settings("app.general", key="non_existent")
    assert len(missing.items) == 0

    # Paginated read
    page1 = initialized_store.read_settings("config.global", limit=2)
    assert len(page1.items) == 2
    assert page1.next_key is not None

    page2 = initialized_store.read_settings(
        "config.global", after_key=page1.next_key, limit=2
    )
    assert len(page2.items) >= 1
    assert page2.items[0].key != page1.items[0].key


def test_settings_store_read_invalid_arguments(
    initialized_store: SettingsStore,
) -> None:
    """Test argument validation for read_settings."""
    with pytest.raises(ValidationError):
        initialized_store.read_settings("app.general", limit=0)
    with pytest.raises(ValidationError):
        initialized_store.read_settings("app.general", limit=1001)
    with pytest.raises(ValidationError):
        initialized_store.read_settings("")
    with pytest.raises(ValidationError):
        initialized_store.read_settings("invalid space")


def test_host_settings_update_batch_and_revision(
    host_settings: HostSettings,
) -> None:
    """Test atomic batch updates and monotonic revision increments."""
    initial_snapshot = host_settings.get_snapshot()
    assert initial_snapshot.revision == 1

    # Update valid settings
    updated = host_settings.update(
        {
            "app.general": {"theme": "light", "zoom": 1.2},
            "config.cpu": {"custom_cores": 4},
        },
        expected_revision=1,
    )
    assert updated.revision == 2
    assert updated.values["application"]["app_general"]["theme"] == "light"
    assert updated.values["application"]["app_general"]["zoom"] == 1.2
    assert updated.values["application"]["config_cpu"]["custom_cores"] == 4

    # Revision conflict check
    with pytest.raises(RevisionConflictError):
        host_settings.update(
            {"app.general": {"theme": "dark"}},
            expected_revision=1,  # Outdated expected revision
        )

    # Empty changes should not increment revision
    no_change = host_settings.update({}, expected_revision=2)
    assert no_change.revision == 2

    # Single scope update helper
    helper_updated = host_settings.update(
        {"app.general": {"theme": "dark"}}, expected_revision=2
    )
    assert helper_updated.revision == 3
    assert helper_updated.values["application"]["app_general"]["theme"] == "dark"


def test_validation_engine_constraints() -> None:
    """Test validation rules for zoom, cores, memory, ports, and text limits."""
    # Valid calls should not raise
    validate_configuration_values("app.general", "zoom", 1.0)
    validate_configuration_values("app.general", "zoom", 0.7)
    validate_configuration_values("app.general", "zoom", 1.8)
    validate_configuration_values("config.cpu", "custom_cores", 8)
    validate_configuration_values("config.memory", "memory_limit_gb", 16)
    validate_configuration_values(
        "config.global", "header_custom_text", "My Custom Header"
    )
    validate_configuration_values("notify.email", "smtp_port", 587)
    validate_configuration_values("app.general", "theme", "dark")
    validate_configuration_values("config.cpu", "core_usage", "all_except_one")

    # Non-finite float
    with pytest.raises(ValidationError, match="NaN or Infinity"):
        validate_configuration_values("test", "metric", float("nan"))
    with pytest.raises(ValidationError, match="NaN or Infinity"):
        validate_configuration_values("test", "metric", float("inf"))

    # Zoom out of range
    with pytest.raises(ValidationError, match="Zoom level"):
        validate_configuration_values("app.general", "zoom", 0.6)
    with pytest.raises(ValidationError, match="Zoom level"):
        validate_configuration_values("app.general", "zoom", 1.9)

    # Custom cores invalid
    with pytest.raises(ValidationError, match="Custom cores"):
        validate_configuration_values("config.cpu", "custom_cores", 0)
    with pytest.raises(ValidationError, match="Custom cores"):
        validate_configuration_values("config.cpu", "custom_cores", True)

    # Memory limit out of bounds
    with pytest.raises(ValidationError, match="Memory limit"):
        validate_configuration_values("config.memory", "memory_limit_gb", 1.5)
    with pytest.raises(ValidationError, match="Memory limit"):
        validate_configuration_values("config.memory", "memory_limit_gb", 2048)

    # Header text length > 30
    with pytest.raises(ValidationError, match="header_custom_text"):
        validate_configuration_values("config.global", "header_custom_text", "x" * 31)

    # SMTP port out of bounds
    with pytest.raises(ValidationError, match="SMTP port"):
        validate_configuration_values("notify.email", "smtp_port", 0)
    with pytest.raises(ValidationError, match="SMTP port"):
        validate_configuration_values("notify.email", "smtp_port", 70000)

    # Theme invalid
    with pytest.raises(ValidationError, match="Theme"):
        validate_configuration_values("app.general", "theme", "blue")

    # Core usage mode invalid
    with pytest.raises(ValidationError, match="core_usage"):
        validate_configuration_values("config.cpu", "core_usage", "invalid_mode")


def test_canonical_json_and_depth() -> None:
    """Test canonical JSON serialization and nesting depth limits."""
    data = {"b": 2, "a": 1}
    assert canonical_json(data) == '{"a":1,"b":2}'

    # Recursive nesting exceeding limit
    nested: dict[str, Any] = {}
    curr = nested
    for _ in range(20):
        curr["child"] = {}
        curr = curr["child"]

    with pytest.raises(ValidationError, match="nesting depth"):
        canonical_json(nested)


def test_validate_identifier() -> None:
    """Test identifier format and length limits."""
    validate_identifier("valid_key-1.2:test", "test_field")

    with pytest.raises(ValidationError, match="must not be empty"):
        validate_identifier("", "empty_field")

    with pytest.raises(ValidationError, match="exceeds maximum"):
        validate_identifier("a" * 129, "oversized_field")

    with pytest.raises(ValidationError, match="invalid characters"):
        validate_identifier("bad char*", "invalid_field")


def test_host_settings_dot_access(host_settings: HostSettings) -> None:
    """Test dot-attribute navigation, dictionary indexing, and fallbacks."""
    # Dot-access
    assert host_settings.app_general.theme == "dark"
    assert host_settings.config_cpu.core_usage == "all_except_one"
    assert host_settings.config_memory.memory_limit_gb == 10

    # Dict indexing
    assert host_settings["app_general"]["theme"] == "dark"
    assert host_settings["app.general"]["theme"] == "dark"

    # get fallback
    assert host_settings.get("missing_key", "default_val") == "default_val"
    assert host_settings.app_general.get("theme") == "dark"

    # In operator
    assert "app_general" in host_settings
    assert "app.general" in host_settings
    assert "non_existent" not in host_settings

    # Attributes missing
    with pytest.raises(AttributeError):
        _ = host_settings.non_existent_attr

    with pytest.raises(KeyError):
        _ = host_settings["non_existent_key"]

    # as_dict
    d = host_settings.as_dict()
    assert isinstance(d, dict)
    assert "app_general" in d or "app.general" in d

    # items and len
    assert len(host_settings) > 0
    assert len(host_settings.items()) > 0
    assert repr(host_settings).startswith("HostSettings(")


def test_host_settings_update_and_reload(host_settings: HostSettings) -> None:
    """Test updating HostSettings through manager interface."""
    assert host_settings.revision == 1
    snapshot = host_settings.update(
        {"app.general": {"theme": "light"}},
        expected_revision=1,
    )
    assert snapshot.revision == 2
    assert host_settings.revision == 2
    assert host_settings.app_general.theme == "light"


def test_settings_store_edge_cases(tmp_path: Path) -> None:
    """Test absent database file handling, oversized batches, and missing tables."""
    absent_db = tmp_path / "does_not_exist.db"
    store = SettingsStore(absent_db)
    assert store.get_revision() == 1
    page = store.read_settings("test_scope")
    assert len(page.items) == 0

    rev, vals = store.read_all()
    assert rev == 1
    assert vals == []

    # Oversized batch
    oversized = {"test_scope": {f"k{i}": i for i in range(MAX_BATCH_SIZE + 5)}}
    with pytest.raises(ValidationError, match="exceeds limit"):
        store.update_batch(oversized)

    # Invalid scope changes (not a dict)
    bad_batch: Any = {"test_scope": "not a dict"}
    with pytest.raises(ValidationError, match="must be a dictionary"):
        store.update_batch(bad_batch)


def test_host_settings_lazy_loading(tmp_path: Path) -> None:
    """Test HostSettings auto_load=False deferred loading."""
    db_file = tmp_path / "lazy.db"
    store = SettingsStore(db_file)
    store.initialize()
    store.update_batch(
        {"application": {"app_general": {"theme": "dark"}}}, expected_revision=1
    )

    hs = HostSettings(db_file, auto_load=False)
    assert not bool(hs._loaded)

    # Access triggers load and schema init
    assert hs.revision == 2
    assert bool(hs._loaded)
    assert hs.app_general.theme == "dark"


@pytest.mark.parametrize(
    "access",
    ["attribute", "index", "get", "contains", "items", "dict", "iterate", "length"],
)
def test_cold_access_loads_direct_storage(temp_db: Path, access: str) -> None:
    """Every public collection access loads values through the raw store."""
    store = SettingsStore(temp_db)
    store.initialize()
    store.update_batch({"application": {"user_access": {"username": "user"}}})
    settings = HostSettings(temp_db)
    assert isinstance(settings._store, SettingsStore)
    assert not settings._loaded
    if access == "attribute":
        assert settings.user_access.username == "user"
    elif access == "index":
        assert settings["user_access"]["username"] == "user"
    elif access == "get":
        assert settings.get("user_access").username == "user"
    elif access == "contains":
        assert "user_access" in settings
    elif access == "items":
        assert dict(settings.items())["user_access"].username == "user"
    elif access == "dict":
        assert settings.as_dict()["user_access"]["username"] == "user"
    elif access == "iterate":
        assert "user_access" in list(iter(settings))
    else:
        assert len(settings) > 0
    assert settings._loaded


def test_construction_and_singleton_import_do_not_connect(temp_db: Path) -> None:
    """Default construction and a fresh singleton import perform no database I/O."""
    settings = HostSettings(temp_db)
    assert not temp_db.exists()
    assert not settings._loaded
    assert bool(settings)
    assert HostRuntime(settings).settings is settings
    assert not temp_db.exists()
    assert not settings._loaded
    code = (
        "from unittest.mock import patch\n"
        "with patch('sqlite3.connect', side_effect=AssertionError('unexpected connection')):\n"
        "    from app.host.settings import HostSettings, settings\n"
        "    assert not settings._loaded\n"
        "    assert not HostSettings()._loaded\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_updates_refresh_cache_and_reload_observes_other_writers(temp_db: Path) -> None:
    """Scoped access is independent; external writes require explicit reload."""
    settings = HostSettings(temp_db)
    snapshot = settings.update(
        {"user_access": {"username": "one"}, "other": {"username": "two"}}
    )
    assert settings.user_access.username == "one"
    assert settings.other.username == "two"
    assert settings.revision == snapshot.revision
    writer = SettingsStore(temp_db)
    writer.update_batch(
        {"application": {"user_access": {"username": "external"}}},
        expected_revision=snapshot.revision,
    )
    assert settings.user_access.username == "one"
    assert (
        settings.get_snapshot().values["application"]["user_access"]["username"]
        == "external"
    )
    settings.reload()
    assert settings.user_access.username == "external"
    assert settings.other.username == "two"


def test_validation_rejection_is_atomic(host_settings: HostSettings) -> None:
    """One invalid value prevents valid siblings and revision updates."""
    before = host_settings.get_snapshot()
    with pytest.raises(ValidationError):
        host_settings.update(
            {"app.general": {"theme": "light", "zoom": 9.0}},
            expected_revision=before.revision,
        )
    assert host_settings.get_snapshot() == before
    assert host_settings.app_general.theme == "dark"


def test_runtime_overrides_do_not_leak_into_persisted_snapshots(temp_db: Path) -> None:
    """In-memory overrides win without being written or projected as stored data."""
    raw = SettingsStore(temp_db)
    raw.initialize()
    raw.update_batch(
        {
            "app_general": {"host": "stored", "backend_port": 8001},
            "host_runtime": {"title": "Stored"},
        }
    )
    settings = HostSettings(temp_db, host="override", port=9000, title="Override")
    assert settings.host == "override"
    assert settings.port == 9000
    assert settings.app_general.host == "override"
    snapshot = settings.update({"host_runtime": {"title": "Updated"}})
    assert snapshot.values["app_general"]["host"] == "stored"
    assert snapshot.values["app_general"]["backend_port"] == 8001
    assert snapshot.values["host_runtime"]["title"] == "Updated"
    assert settings.title == "Override"


@pytest.mark.parametrize(
    "failure", [PersistenceError, IncompatibleSchemaError, CorruptDataError]
)
def test_initialization_failure_logging_excludes_values(
    temp_db: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure: type[PersistenceError],
) -> None:
    """Tolerated failures are visible; incompatible/corrupt stores fail closed."""
    settings = HostSettings(temp_db)

    def fail() -> None:
        raise failure("secret-test-value")

    monkeypatch.setattr(settings._store, "initialize", fail)
    if failure is PersistenceError:
        settings.reload()
        assert settings.get_snapshot().values == {}
    else:
        with pytest.raises(failure):
            settings.reload()
        assert not settings._loaded
    assert any(
        record.fr_id == "FR-HOST-SETTINGS-LOAD"
        for record in caplog.records
        if hasattr(record, "fr_id")
    )
    assert "secret-test-value" not in caplog.text


def test_fastapi_settings_router(host_settings: HostSettings) -> None:
    """Test FastAPI settings REST projection endpoints."""
    app = FastAPI()
    router = create_settings_router(host_settings)
    app.include_router(router)
    client = TestClient(app)

    # 1. GET /settings
    resp = client.get("/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["revision"] == 1
    assert "app.general" in data["data"]["values"]
    assert data["data"]["values"]["app.general"]["theme"] == "dark"

    # 2. PUT /settings success
    put_resp = client.put(
        "/settings",
        json={
            "expected_revision": 1,
            "changes": {"app.general": {"theme": "light", "zoom": 1.2}},
        },
    )
    assert put_resp.status_code == 200
    put_data = put_resp.json()
    assert put_data["status"] == "success"
    assert put_data["data"]["revision"] == 2
    assert put_data["data"]["values"]["app.general"]["theme"] == "light"
    assert put_data["data"]["values"]["app.general"]["zoom"] == 1.2

    # 3. PUT /settings revision conflict (409)
    conflict_resp = client.put(
        "/settings",
        json={
            "expected_revision": 1,  # Current is 2
            "changes": {"app.general": {"theme": "dark"}},
        },
    )
    assert conflict_resp.status_code == 409
    conflict_data = conflict_resp.json()
    assert conflict_data["status"] == "error"
    assert conflict_data["error"]["code"] == "REVISION_CONFLICT"

    # 4. PUT /settings validation error (422)
    val_resp = client.put(
        "/settings",
        json={
            "expected_revision": 2,
            "changes": {"app.general": {"zoom": 3.5}},  # Out of range
        },
    )
    assert val_resp.status_code == 422
    val_data = val_resp.json()
    assert val_data["status"] == "error"
    assert val_data["error"]["code"] == "VALIDATION_ERROR"

    # 5. PUT /settings invalid payload types
    bad_type_resp = client.put("/settings", json="invalid string payload")
    assert bad_type_resp.status_code == 422

    bad_rev_resp = client.put(
        "/settings", json={"expected_revision": -1, "changes": {}}
    )
    assert bad_rev_resp.status_code == 422

    bad_changes_resp = client.put(
        "/settings", json={"expected_revision": 2, "changes": "not a dict"}
    )
    assert bad_changes_resp.status_code == 422

    # 6. PUT /settings malformed raw body (400)
    malformed_resp = client.put(
        "/settings",
        content=b"not valid json at all",
        headers={"content-type": "application/json"},
    )
    assert malformed_resp.status_code == 400
    assert malformed_resp.json()["error"]["code"] == "INVALID_JSON"


def test_settings_http_hides_and_protects_credentials(
    host_settings: HostSettings,
) -> None:
    """Credential configuration is internal and never writable through settings UI."""
    host_settings.update(
        {"user_access": {"username": "configured", "password_hash": "private-verifier"}}
    )
    app = FastAPI()
    app.include_router(create_settings_router(host_settings))
    with TestClient(app) as client:
        assert "user_access" not in client.get("/settings").json()["data"]["values"]
        response = client.put(
            "/settings",
            json={
                "expected_revision": host_settings.revision,
                "changes": {"app.general": {"theme": "light"}},
            },
        )
        assert response.status_code == 200
        assert "private-verifier" not in response.text
        assert "user_access" not in response.json()["data"]["values"]
        before = host_settings.revision
        rejected = client.put(
            "/settings",
            json={
                "expected_revision": before,
                "changes": {"user_access": {"password_hash": "replace"}},
            },
        )
        assert rejected.status_code == 422
        assert host_settings.revision == before


def test_settings_notifications_follow_committed_writes(
    host_settings: HostSettings,
) -> None:
    """Only successful non-empty writes notify readers with their revision."""
    revisions: list[int] = []
    app = FastAPI()
    app.include_router(
        create_settings_router(host_settings, on_updated=revisions.append)
    )
    with TestClient(app) as client:
        before = host_settings.get_snapshot().revision
        saved = client.put(
            "/settings",
            json={
                "expected_revision": before,
                "changes": {"app.general": {"theme": "light"}},
            },
        )
        assert saved.status_code == 200
        assert revisions == [saved.json()["data"]["revision"]]
        persisted = HostSettings(host_settings.db_path).get_snapshot()
        assert persisted.values["application"]["app_general"]["theme"] == "light"
        for body in [
            {
                "expected_revision": before,
                "changes": {"app.general": {"theme": "dark"}},
            },
            {
                "expected_revision": persisted.revision,
                "changes": {"app.general": {"zoom": 8}},
            },
            {
                "expected_revision": persisted.revision,
                "changes": {"user_access": {"username": "changed"}},
            },
        ]:
            assert client.put("/settings", json=body).status_code in (409, 422)
        assert (
            client.put(
                "/settings",
                json={"expected_revision": persisted.revision, "changes": {}},
            ).status_code
            == 200
        )
        assert revisions == [persisted.revision]
        assert host_settings.get_snapshot() == persisted


def test_notification_failure_does_not_reject_committed_save(
    host_settings: HostSettings, caplog: pytest.LogCaptureFixture
) -> None:
    """A broken refresh hint cannot turn a committed write into a failed save."""

    def fail_notification(revision: int) -> None:
        raise RuntimeError("private notification internals")

    app = FastAPI()
    app.include_router(
        create_settings_router(host_settings, on_updated=fail_notification)
    )
    with TestClient(app) as client:
        response = client.put(
            "/settings",
            json={
                "expected_revision": host_settings.revision,
                "changes": {"app.general": {"theme": "light"}},
            },
        )
    assert response.status_code == 200
    assert (
        HostSettings(host_settings.db_path)
        .get_snapshot()
        .values["application"]["app_general"]["theme"]
        == "light"
    )
    assert "Settings committed but revision notification failed" in caplog.text
    assert "private notification internals" not in caplog.text


def test_catalogue_masks_nested_secrets_and_unknown_payloads(temp_db: Path) -> None:
    """Neither legacy nested credentials nor unknown payloads reach HTTP reads."""
    target = HostSettings(temp_db)
    target.update(
        {
            "application": {
                "config_ctrader": {
                    "client_secret": "synthetic-client-secret",
                    "account_id": "42",
                },
                "config_agents": {
                    "openai": {"api_key": "synthetic-api-key", "model": "local-test"}
                },
                "user_access": {
                    "password_hash": "synthetic-legacy-hash",
                    "password_salt": "synthetic-salt",
                },
                "unknown_extension": {"private_token": "synthetic-unknown-secret"},
            }
        }
    )
    app = FastAPI()
    app.include_router(create_settings_router(target))
    with TestClient(app) as client:
        for path in ("/settings", "/settings/catalogue"):
            response = client.get(path)
            assert response.status_code == 200
            for secret in (
                "synthetic-client-secret",
                "synthetic-api-key",
                "synthetic-legacy-hash",
                "synthetic-salt",
                "synthetic-unknown-secret",
            ):
                assert secret not in response.text
        catalogue = client.get("/settings/catalogue").json()["data"]
        secret = next(
            field for field in catalogue["fields"] if field["key"] == "openai.api_key"
        )
        assert secret["configured"] is True
        assert "value" not in secret
        assert catalogue["unknown"][0]["reason"].startswith("Unsupported")


def test_catalogue_atomic_group_update_and_secret_preservation(temp_db: Path) -> None:
    """A mixed secret/preferences save updates consumer records atomically."""
    target = HostSettings(temp_db)
    target.update(
        {
            "application": {
                "config_agents": {
                    "openai": {"api_key": "old-key", "model": "old-model"},
                    "ollama": {"model": "untouched"},
                },
                "notify_email": {
                    "password": "old-password",
                    "use_ssl": False,
                    "use_tls": True,
                },
            }
        }
    )
    app = FastAPI()
    app.include_router(create_settings_router(target))
    with TestClient(app) as client:
        revision = target.revision
        response = client.put(
            "/settings/secrets",
            json={
                "expected_revision": revision,
                "changes": {
                    "config.agents": {
                        "openai.api_key": "new-synthetic-key",
                        "openai.model": "new-model",
                    },
                    "notify.email": {"recipient_addresses": ["test@example.test"]},
                },
            },
        )
        assert response.status_code == 200
        assert "new-synthetic-key" not in response.text
        assert response.json()["data"]["revision"] == revision + 1
        independent = HostSettings(temp_db)
        snapshot = independent.get_snapshot()
        assert independent.config_agents.openai.model == "new-model"
        assert independent.config_agents.openai.api_key == "new-synthetic-key"
        assert independent.config_agents.ollama.model == "untouched"
        assert independent.notify_email.password == "old-password"
        assert (
            snapshot.values["application"]["config_agents"]["openai"]["model"]
            == "new-model"
        )
        stale = client.put(
            "/settings/secrets",
            json={
                "expected_revision": revision,
                "changes": {"config.agents": {"openai.api_key": "stale"}},
            },
        )
        assert stale.status_code == 409
        assert HostSettings(temp_db).config_agents.openai.api_key == "new-synthetic-key"
        clear = client.put(
            "/settings/secrets",
            json={
                "expected_revision": revision + 1,
                "changes": {"config.agents": {"openai.api_key": ""}},
            },
        )
        assert clear.status_code == 200
        assert HostSettings(temp_db).config_agents.openai.api_key == ""


@pytest.mark.parametrize(
    ("scope", "changes"),
    [
        ("notify.desktop", {"enabled": True, "duration_seconds": 6}),
        ("notify.desktop", {"min_priority": "normal"}),
        (
            "notify.email",
            {"enabled": True, "smtp_port": 465, "use_ssl": True, "use_tls": False},
        ),
        ("notify.telegram", {"chat_id": "synthetic-chat", "parse_mode": "HTML"}),
        (
            "config.metatrader5",
            {"account_id": 123, "timeout_ms": 60000, "portable": True},
        ),
        (
            "config.ctrader",
            {"account_id": "123", "environment": "demo", "gateway_port": 5035},
        ),
        (
            "config.agents",
            {"openai.model": "synthetic-model", "openai.temperature": 0.5},
        ),
        ("workspace.paths", {"projects_dir": "temporary/projects"}),
        ("engine.backtest", {"max_threads": 2, "precision_mode": "normal"}),
        ("calibration.indicators", {"QQE.RSIPeriod": [7, 14, 21]}),
        ("connect.mcp", {"allowed_tools": ["settings.read"], "max_context_items": 10}),
    ],
)
def test_remaining_settings_http_round_trip(
    temp_db: Path, scope: str, changes: dict[str, Any]
) -> None:
    """Every newly exposed business group round-trips through the real store."""
    target = HostSettings(temp_db)
    app = FastAPI()
    app.include_router(create_settings_router(target))
    with TestClient(app) as client:
        revision = target.get_snapshot().revision
        response = client.put(
            "/settings",
            json={"expected_revision": revision, "changes": {scope: changes}},
        )
        assert response.status_code == 200
        _, records = SettingsStore(temp_db).read_all()
        assert all(record.scope == "application" for record in records)
        persisted = next(
            record.value for record in records if record.key == SETTINGS_GROUPS[scope]
        )
        for key, value in changes.items():
            assert _field_value(persisted, key, None) == value
        assert HostSettings(temp_db).get_snapshot().revision == revision + 1


@pytest.mark.parametrize(
    ("scope", "fields"),
    [
        ("application", {"config_agents": {"openai": {"api_key": "bypass"}}}),
        ("config.agents", {"openai.api_key": "bypass"}),
        ("notify.desktop", {"duration_seconds": -1}),
        ("notify.email", {"smtp_port": True}),
        ("config.agents", {"openai.temperature": 8}),
        ("app.general", {"language": "de"}),
        ("notify.telegram", {"unknown_field": "value"}),
    ],
)
def test_catalogue_rejects_unsafe_or_untyped_http_updates(
    temp_db: Path, scope: str, fields: dict[str, Any]
) -> None:
    """No generic settings request can bypass secret/read-only/type contracts."""
    target = HostSettings(temp_db)
    app = FastAPI()
    app.include_router(create_settings_router(target))
    with TestClient(app) as client:
        before = target.get_snapshot()
        response = client.put(
            "/settings",
            json={"expected_revision": before.revision, "changes": {scope: fields}},
        )
        assert response.status_code == 422
        assert target.get_snapshot() == before


def test_consolidation_preserves_current_credentials_and_values(temp_db: Path) -> None:
    """Cleanup preserves working login, unknown siblings and stable future row sets."""
    from app.host.session import hash_password, verify_password

    store = SettingsStore(temp_db)
    store.initialize()
    working = hash_password("synthetic-current-password")
    store.update_batch(
        {
            "application": {
                "app_general": {"zoom": 1.0, "unknown": "retain"},
                "config_global": {
                    "advanced_file_chooser": False,
                    "header_custom_text": "old",
                    "footer_custom_text": "footer",
                },
                "config_memory": {"gc_type": "ParallelGC", "memory_limit_gb": 10},
                "config_troubleshooting": {"debug_level_active": False},
                "notify_desktop": {"duration_seconds": 5, "enabled": True},
                "user_access": {
                    "username": "obsolete",
                    "password_hash": "obsolete",
                    "session_timeout_mins": 1440,
                    "require_auth": True,
                },
            },
            "app.general": {"zoom": 1.1},
            "config.global": {
                "advanced_file_chooser": True,
                "header_custom_text": "current",
            },
            "config.memory": {"gc_type": "G1GC"},
            "config.troubleshooting": {"debug_level_active": True},
            "notify.desktop": {"duration_seconds": 6},
            "user_access": {"username": "current", "password_hash": working},
            "unknown": {"untouched": {"data": "retain"}},
        }
    )
    target = HostSettings(temp_db)
    before = target.get_snapshot()
    dry = consolidate_settings(target)
    assert not dry["applied"]
    assert target.get_snapshot() == before
    assert working not in str(dry)
    result = consolidate_settings(target, apply=True)
    assert result["revision"] == before.revision + 1
    _, rows = store.read_all()
    assert len(result["deleted_rows"]) == 8
    assert all(row.scope in ("application", "unknown") for row in rows)
    groups = target.get_snapshot().values["application"]
    assert groups["app_general"] == {
        "zoom": 1.1,
        "unknown": "retain",
        "header_custom_text": "current",
    }
    assert groups["config_global"] == {
        "advanced_file_chooser": True,
        "footer_custom_text": "footer",
    }
    assert groups["user_access"]["password_hash"] == working
    assert verify_password(
        "synthetic-current-password", target.user_access.password_hash
    )
    assert groups["user_access"]["session_timeout_mins"] == 1440
    stable = target.get_snapshot()
    assert not consolidate_settings(target, apply=True)["applied"]
    assert target.get_snapshot() == stable
    row_set = {(row.scope, row.key) for row in rows}
    target.update({"notify.desktop": {"duration_seconds": 7}})
    target.update({"app.general": {"header_custom_text": "new"}})
    target.update({"connect.remote": {"allow": False, "require_password": True}})
    assert {(r.scope, r.key) for r in store.read_all()[1]} == row_set
    assert target.app_general.remote_access.require_password is True
    assert target.notify_desktop.enabled is True


def test_consolidation_rejects_unapproved_or_invalid_account(temp_db: Path) -> None:
    """No partial writes occur for malformed credentials or different row targets."""
    store = SettingsStore(temp_db)
    store.initialize()
    store.update_batch(
        {
            "application": {"user_access": {"username": "old"}},
            "user_access": {"username": "new"},
        }
    )
    target = HostSettings(temp_db)
    before = target.get_snapshot()
    with pytest.raises(ValidationError):
        consolidate_settings(target, apply=True)
    assert target.get_snapshot() == before
    store.update_batch(
        {"application": {"app_general": {"zoom": 1.0}}, "app.general": {"zoom": 1.1}},
        deletions=(("user_access", "username"),),
    )
    before = target.get_snapshot()
    with pytest.raises(ValidationError):
        consolidate_settings(target, apply=True, allowed_deletions=())
    assert target.get_snapshot() == before


def test_settings_record_schema_version_applied(temp_db: Path) -> None:
    """Verify that host_settings rows are written with SETTINGS_RECORD_SCHEMA_VERSION."""
    from app.host.persistence import SETTINGS_RECORD_SCHEMA_VERSION

    store = SettingsStore(temp_db)
    store.initialize()
    store.update_batch({"app_general": {"theme": "dark"}})

    conn = sqlite3.connect(temp_db)
    try:
        row = conn.execute(
            "SELECT schema_version FROM host_settings WHERE scope='app_general' AND key='theme'"
        ).fetchone()
        assert row is not None
        assert row[0] == SETTINGS_RECORD_SCHEMA_VERSION
    finally:
        conn.close()
