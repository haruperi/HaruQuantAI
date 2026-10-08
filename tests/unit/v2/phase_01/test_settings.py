"""Unit tests for app.host.settings module.

Validates the SQLite persistence store (host_settings table), schema creation,
seeding, dot-access navigation, validation engine, revision conflict detection,
cached access, validated updates and persistence delegation.
"""

from __future__ import annotations

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
from app.host.settings import HostSettings, validate_configuration_values


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
    """Test IncompatibleSchemaError when host_settings has mismatched schema."""
    conn = sqlite3.connect(temp_db)
    # Create invalid table without required columns
    conn.execute("CREATE TABLE host_settings (wrong_col TEXT)")
    conn.close()

    store = SettingsStore(temp_db)
    with pytest.raises(IncompatibleSchemaError):
        store.initialize()


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
    assert updated.values["app.general"]["theme"] == "light"
    assert updated.values["app.general"]["zoom"] == 1.2
    assert updated.values["config.cpu"]["custom_cores"] == 4

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
    assert helper_updated.values["app.general"]["theme"] == "dark"


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
    store.update_batch({"app.general": {"theme": "dark"}}, expected_revision=1)

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
    store.update_batch({"user_access": {"username": "user"}})
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
        {"user_access": {"username": "external"}}, expected_revision=snapshot.revision
    )
    assert settings.user_access.username == "one"
    assert settings.get_snapshot().values["user_access"]["username"] == "external"
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
