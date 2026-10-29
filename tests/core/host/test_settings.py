import importlib
import json
import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from app.core.host.settings import (
    RevisionConflictError,
    SettingsDataError,
    SettingsManager,
    SettingsPersistenceError,
)
from app.host.persistence import HostPersistence


@pytest.fixture
def gateway(tmp_path):
    path = tmp_path / "settings.db"
    connection = sqlite3.connect(path)
    connection.execute("""
        CREATE TABLE host_settings (
            scope TEXT NOT NULL, key TEXT NOT NULL, value_json TEXT NOT NULL,
            schema_version INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT NOT NULL,
            PRIMARY KEY(scope, key),
            CHECK(NOT(key = 'port' AND value_json = '-1'))
        )
    """)
    connection.close()
    gateway = HostPersistence(path)
    rows = [
        ("application", "app_general", {"theme": "dark", "extras": [1]}),
        (
            "application",
            "user_access",
            {"username": "tester", "password_hash": "secret"},
        ),
        ("host", "port", 8000),
        ("ui", "theme", "dark"),
        ("_system", "revision", 10),
        ("host", "__revision__", 7),
    ]
    result = gateway.create_records(
        "host_settings",
        [
            {
                "scope": scope,
                "key": key,
                "value_json": json.dumps(value),
                "schema_version": 3,
                "updated_at_utc": "unchanged",
            }
            for scope, key, value in rows
        ],
    )
    assert result["success"], result
    return gateway


def row(gateway, scope, key):
    result = gateway.read_records("host_settings", filters={"scope": scope, "key": key})
    assert result["success"], result
    return result["data"]["records"][0]


def test_singleton_and_manager_are_lazy():
    module = importlib.import_module("app.core.host.settings")
    with patch.object(
        module, "HostPersistence", side_effect=AssertionError("eager access")
    ):
        manager = SettingsManager()
        assert manager._loaded is False
        assert manager._persistence is None
        assert (
            importlib.import_module("app.core.host.settings").settings
            is module.settings
        )


def test_scoped_attribute_access_stored_only_projection_and_detachment(gateway):
    manager = SettingsManager(gateway)
    assert manager.application.app_general.theme == "dark"
    assert manager.app_general.theme == "dark"
    assert manager.host.port == 8000
    assert manager["user_access"]["username"] == "tester"
    assert manager.revision == 10
    snapshot = manager.get_snapshot(scopes=["application", "missing"])
    assert list(snapshot["values"]) == ["application"]
    assert "_system" not in manager.as_dict()
    assert "__revision__" not in manager.get_scope("host")
    assert manager.get("missing", default={"fallback": True}) == {"fallback": True}
    assert "missing" not in manager.as_dict()
    snapshot["values"]["application"]["app_general"]["theme"] = "tampered"
    manager.get_scope("app_general")["extras"].append(2)
    manager.app_general.extras.append(3)
    assert manager.app_general.theme == "dark"
    assert manager.app_general.extras == [1]
    with pytest.raises(AttributeError):
        _ = manager.missing
    with pytest.raises(KeyError):
        manager.get_scope("missing")
    with pytest.raises(AttributeError):
        manager.app_general.theme = "changed"


def test_batch_updates_multiple_scopes_and_revision_markers(gateway):
    manager = SettingsManager(gateway)
    new_revision = manager.save_settings(
        {"application": {"app_general": {"theme": "light"}}, "host": {"port": 9000}},
        expected_revision=10,
    )
    assert new_revision == 11
    assert manager.revision == 11
    assert manager.app_general.theme == "light"
    assert manager.host.port == 9000
    assert manager.user_access.username == "tester"
    for scope, key in [
        ("application", "app_general"),
        ("host", "port"),
        ("_system", "revision"),
        ("host", "__revision__"),
    ]:
        result = row(gateway, scope, key)
        assert result["schema_version"] == 11
        assert result["updated_at_utc"] != "unchanged"
    assert json.loads(row(gateway, "_system", "revision")["value_json"]) == 11
    assert row(gateway, "application", "user_access")["schema_version"] == 3


def test_noop_keeps_revision_and_timestamps_and_distinguishes_bool(gateway):
    manager = SettingsManager(gateway)
    assert manager.save_settings({"host": {"port": 8000}}, expected_revision=10) == 10
    assert row(gateway, "host", "port")["updated_at_utc"] == "unchanged"
    assert manager.save_settings({"ui": {"theme": True}}, expected_revision=10) == 11
    assert manager.save_settings({"ui": {"theme": 1}}, expected_revision=11) == 12


def test_stale_revision_rejects_even_noop_and_reload_is_explicit(gateway):
    first, second = SettingsManager(gateway), SettingsManager(gateway)
    assert first.revision == second.revision == 10
    first.save_settings({"host": {"port": 9000}}, expected_revision=10)
    with pytest.raises(RevisionConflictError) as caught:
        second.save_settings({"host": {"port": 9000}}, expected_revision=10)
    assert caught.value.expected_revision == 10
    assert caught.value.current_revision == 11
    assert second.host.port == 8000
    second.reload()
    assert second.host.port == 9000


def test_later_database_failure_rolls_back_everything_and_preserves_cache(gateway):
    manager = SettingsManager(gateway)
    before = manager.get_snapshot()
    with pytest.raises(SettingsPersistenceError):
        manager.save_settings(
            {"ui": {"theme": "light"}, "host": {"port": -1}}, expected_revision=10
        )
    assert manager.get_snapshot() == before
    assert SettingsManager(gateway).get_snapshot() == before
    assert row(gateway, "ui", "theme")["updated_at_utc"] == "unchanged"


def test_missing_records_do_not_create_or_partially_update(gateway):
    manager = SettingsManager(gateway)
    with pytest.raises(KeyError):
        manager.save_settings(
            {"host": {"port": 9000, "new_key": True}}, expected_revision=10
        )
    assert manager.host.port == 8000
    assert manager.revision == 10


@pytest.mark.parametrize(
    "updates",
    [
        {},
        {"host": {}},
        {"_system": {"revision": 9}},
        {"host": {"__revision__": 9}},
        {"host": {"port": float("inf")}},
        {"host": {"port": {1: "bad"}}},
        {"host": {"port": object()}},
    ],
)
def test_invalid_updates_rejected_before_writes(gateway, updates):
    manager = SettingsManager(gateway)
    with pytest.raises((TypeError, ValueError)):
        manager.save_settings(updates, expected_revision=10)
    assert manager.host.port == 8000


def test_corrupt_stored_json_does_not_replace_cache(gateway):
    manager = SettingsManager(gateway)
    before = manager.get_snapshot()
    result = gateway.update_record(
        "host_settings", {"value_json": "NaN"}, filters={"scope": "host", "key": "port"}
    )
    assert result["success"]
    with pytest.raises(SettingsDataError):
        manager.reload()
    assert manager.get_snapshot() == before


def test_concurrent_managers_only_one_revision_wins(gateway):
    barrier = threading.Barrier(2)

    def save(port):
        manager = SettingsManager(gateway)
        revision = manager.revision
        barrier.wait(timeout=5)
        try:
            return manager.save_settings(
                {"host": {"port": port}}, expected_revision=revision
            )
        except RevisionConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, [9001, 9002]))
    assert results.count(11) == 1
    assert results.count("conflict") == 1


def test_loading_pages_beyond_persistence_limit(gateway):
    for start, end in [(0, 1000), (1000, 1005)]:
        result = gateway.create_records(
            "host_settings",
            [
                {
                    "scope": "extra",
                    "key": f"key-{i:04}",
                    "value_json": str(i),
                    "schema_version": 3,
                    "updated_at_utc": "unchanged",
                }
                for i in range(start, end)
            ],
        )
        assert result["success"], result
    manager = SettingsManager(gateway)
    assert len(manager.get_scope("extra")) == 1005
    assert manager.extra["key-1004"] == 1004


def test_logs_do_not_include_setting_values(gateway, caplog):
    manager = SettingsManager(gateway)
    secret = "private-credential-value"
    with caplog.at_level(logging.INFO):
        manager.save_settings(
            {"application": {"user_access": {"password_hash": secret}}},
            expected_revision=10,
        )
    assert "Settings batch committed" in caplog.text
    assert secret not in caplog.text


def test_legacy_rows_without_revision_markers_use_maximum_row_version(gateway):
    result = gateway.delete_record("host_settings", filters={"scope": "_system"})
    assert result["success"], result
    result = gateway.delete_record(
        "host_settings", filters={"scope": "host", "key": "__revision__"}
    )
    assert result["success"], result
    manager = SettingsManager(gateway)
    assert manager.revision == 3
    assert manager.save_settings({"host": {"port": 9000}}, expected_revision=3) == 4
    assert SettingsManager(gateway).revision == 4


def test_legacy_plain_text_loads_without_rewriting_and_saves_as_json(gateway):
    result = gateway.update_record(
        "host_settings", {"value_json": "dark"}, filters={"scope": "ui", "key": "theme"}
    )
    assert result["success"], result
    manager = SettingsManager(gateway)
    assert manager.ui.theme == "dark"
    assert manager.user_access.username == "tester"
    assert manager.save_settings({"ui": {"theme": "dark"}}, expected_revision=10) == 10
    assert row(gateway, "ui", "theme")["value_json"] == "dark"
    assert manager.save_settings({"ui": {"theme": "light"}}, expected_revision=10) == 11
    assert row(gateway, "ui", "theme")["value_json"] == '"light"'


@pytest.mark.parametrize(
    "raw", ['{"broken":', "[1,", '"unclosed', "Infinity", "-Infinity", "1e999"]
)
def test_legacy_text_compatibility_does_not_hide_invalid_json(gateway, raw):
    result = gateway.update_record(
        "host_settings", {"value_json": raw}, filters={"scope": "ui", "key": "theme"}
    )
    assert result["success"], result
    with pytest.raises(SettingsDataError):
        SettingsManager(gateway).reload()
