"""Unit tests for app.host.settings module.

Validates the SQLite persistence store (host_settings table), schema creation,
seeding, dot-access navigation, validation engine, revision conflict detection,
workspace path validation, and FastAPI REST projection endpoints.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from app.host.settings import (
    MAX_BATCH_SIZE,
    CorruptDataError,
    HostSettings,
    IncompatibleSchemaError,
    RevisionConflictError,
    SettingsStore,
    ValidationError,
    canonical_json,
    create_settings_router,
    validate_configuration_values,
    validate_identifier,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Provide an isolated temporary SQLite database path."""
    return tmp_path / "test_haruquantai.db"


@pytest.fixture
def initialized_store(temp_db: Path) -> SettingsStore:
    """Provide an initialized SettingsStore on an isolated temporary database."""
    store = SettingsStore(temp_db)
    store.initialize()
    return store


@pytest.fixture
def host_settings(temp_db: Path) -> HostSettings:
    """Provide a HostSettings instance connected to an isolated temporary database."""
    return HostSettings(temp_db, auto_load=True)


def test_settings_store_initialize_and_seed(temp_db: Path) -> None:
    """Test table creation and default configuration seeding."""
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
    assert count > 10  # Seeded defaults present
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


def test_settings_store_update_batch_and_revision(
    initialized_store: SettingsStore,
) -> None:
    """Test atomic batch updates and monotonic revision increments."""
    initial_snapshot = initialized_store.get_snapshot()
    assert initial_snapshot.revision == 1

    # Update valid settings
    updated = initialized_store.update_batch(
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
        initialized_store.update_batch(
            {"app.general": {"theme": "dark"}},
            expected_revision=1,  # Outdated expected revision
        )

    # Empty changes should not increment revision
    no_change = initialized_store.update_batch({}, expected_revision=2)
    assert no_change.revision == 2

    # Single scope update helper
    helper_updated = initialized_store.update_settings(
        "app.general", {"theme": "dark"}, expected_revision=2
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


def test_host_settings_validate_workspace_paths(
    host_settings: HostSettings, tmp_path: Path
) -> None:
    """Test workspace path validation on existing and absent directories."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()

    # Update workspace paths
    host_settings.update(
        {
            "workspace_paths": {
                "configs_dir": str(configs_dir),
                "data_dir": str(tmp_path / "absent_data"),
                "projects_dir": str(tmp_path / "absent_projects"),
                "strategies_dir": str(tmp_path / "absent_strategies"),
            }
        },
        expected_revision=host_settings.revision,
    )

    results = host_settings.validate_workspace_paths()
    assert results["Configs"] is True
    assert results["Data"] is False
    assert results["Projects"] is False
    assert results["Strategies"] is False


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

    # 7. GET /settings/paths/validate
    paths_resp = client.get("/settings/paths/validate")
    assert paths_resp.status_code == 200
    paths_data = paths_resp.json()
    assert paths_data["status"] == "success"
    assert "paths" in paths_data["data"]
    assert "all_valid" in paths_data["data"]


def test_settings_store_edge_cases(tmp_path: Path) -> None:
    """Test absent database file handling, oversized batches, and missing tables."""
    absent_db = tmp_path / "does_not_exist.db"
    store = SettingsStore(absent_db)
    assert store.get_revision() == 1
    page = store.read_settings("test_scope")
    assert len(page.items) == 0

    rev, vals = store.read_all_scoped()
    assert rev == 1
    assert vals == {}

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
    hs = HostSettings(db_file, auto_load=False)
    assert not bool(hs._loaded)

    # Access triggers load and schema init
    assert hs.revision == 1
    assert bool(hs._loaded)
    assert hs.app_general.theme == "dark"


def test_host_settings_default_workspace_paths(tmp_path: Path) -> None:
    """Test validate_workspace_paths when workspace_paths is None/unconfigured."""
    db_file = tmp_path / "paths_default.db"
    hs = HostSettings(db_file)
    # Delete workspace_paths key from store
    conn = sqlite3.connect(db_file)
    conn.execute("DELETE FROM host_settings WHERE scope = 'workspace_paths'")
    conn.commit()
    conn.close()
    hs.reload()

    statuses = hs.validate_workspace_paths()
    assert isinstance(statuses, dict)
    assert "Configs" in statuses
