"""Host scoped SQLite settings, redaction, and conditional writes."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.host.events import SETTINGS_CHANNEL
from app.host.settings import SettingsConflictError, SettingsError, SettingsStore
from app.host.webserver import HostServices
from starlette.testclient import TestClient


def test_new_database_starts_empty(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    store = SettingsStore(path)
    assert store.snapshot() == {"revision": 0, "values": {}}
    with closing(sqlite3.connect(path)) as connection:
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(host_settings)")
        ]
        assert columns == [
            "scope",
            "key",
            "value_json",
            "schema_version",
            "updated_at_utc",
        ]


def test_patch_preserves_unrelated_fields_and_rejects_stale_revision(
    tmp_path: Path,
) -> None:
    path = tmp_path / "app.db"
    store = SettingsStore(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "INSERT INTO host_settings VALUES (?, ?, ?, ?, ?)",
            (
                "application",
                "notify.email",
                json.dumps(
                    {
                        "password": "never-expose",  # pragma: allowlist secret
                        "smtp_server": "old",
                    }
                ),
                1,
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.commit()
    assert store.snapshot()["values"] == {"notify.email": {"smtp_server": "old"}}
    saved = store.patch({"notify.email": {"smtp_server": "new"}}, 0)
    assert saved == {"revision": 1, "values": {"notify.email": {"smtp_server": "new"}}}
    with closing(sqlite3.connect(path)) as connection:
        row = connection.execute(
            "SELECT value_json FROM host_settings WHERE scope=? AND key=?",
            ("application", "notify.email"),
        ).fetchone()
        assert row is not None
        assert json.loads(row[0]) == {
            "password": "never-expose",  # pragma: allowlist secret
            "smtp_server": "new",
        }
    with pytest.raises(SettingsConflictError):
        store.patch({"notify.email": {"smtp_server": "stale"}}, 0)
    assert SettingsStore(path).snapshot() == saved


def test_patch_rejects_unknown_and_secret_fields(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "app.db")
    for change in (
        {"ui": {"theme": "dark"}},
        {"notify.email": {"password": "secret"}},  # pragma: allowlist secret
        {"config.cpu": {"custom_cores": True}},
        {"config.cpu": {"core_usage": "unsupported"}},
        {"app.general": {"zoom": 4.0}},
        {"config.databanks": {"databank_sync_interval_mins": -1}},
        {},
    ):
        with pytest.raises(SettingsError):
            store.patch(change, 0)
    assert store.snapshot()["revision"] == 0


def test_existing_database_preserves_unrelated_table(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE workspace_settings (key TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO workspace_settings VALUES ('retained')")
        connection.commit()
    SettingsStore(path)
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT key FROM workspace_settings").fetchone() == (
            "retained",
        )


def test_incompatible_host_schema_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE host_settings (key TEXT PRIMARY KEY)")
        connection.commit()
    with pytest.raises(SettingsError, match="Incompatible"):
        SettingsStore(path)


def test_corrupt_settings_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "app.db"
    SettingsStore(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "INSERT INTO host_settings VALUES (?, ?, ?, ?, ?)",
            ("application", "config.cpu", "{broken", 1, "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()
    with pytest.raises(SettingsError, match="Malformed"):
        SettingsStore(path).snapshot()


def test_settings_endpoints_round_trip(
    client: TestClient, auth_headers: dict[str, str], settings_path: Path
) -> None:
    changes = {"config.cpu": {"core_usage": "custom", "custom_cores": 4}}
    put = client.put(
        "/api/v1/settings",
        json={"expected_revision": 0, "changes": changes},
        headers=auth_headers,
    )
    get = client.get("/api/v1/settings", headers=auth_headers)
    assert put.status_code == 200
    assert put.json()["data"] == {"revision": 1, "values": changes}
    assert get.json()["data"] == put.json()["data"]
    with closing(sqlite3.connect(settings_path)) as connection:
        value = connection.execute(
            "SELECT value_json FROM host_settings WHERE scope=? AND key=?",
            ("application", "config.cpu"),
        ).fetchone()
        assert value is not None
        assert json.loads(value[0]) == changes["config.cpu"]
    stale = client.put(
        "/api/v1/settings",
        json={"expected_revision": 0, "changes": changes},
        headers=auth_headers,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "SETTINGS_CONFLICT"


def test_settings_change_publishes_only_safe_fields_after_commit(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    subscriber = services.events.subscribe([SETTINGS_CHANNEL])
    response = client.put(
        "/api/v1/settings",
        json={
            "expected_revision": 0,
            "changes": {"app.general": {"zoom": 1.1}},
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    event = subscriber.queue.get_nowait()
    assert event["channel"] == SETTINGS_CHANNEL
    assert event["data"] == {"app.general": {"zoom": 1.1}}
    rejected = client.put(
        "/api/v1/settings",
        json={
            "expected_revision": 0,
            "changes": {"app.general": {"zoom": 1.2}},
        },
        headers=auth_headers,
    )
    assert rejected.status_code == 409
    assert subscriber.queue.empty()


def test_settings_requires_auth(client: TestClient) -> None:
    response = client.put(
        "/api/v1/settings",
        json={
            "expected_revision": 0,
            "changes": {"app.general": {"zoom": 1.1}},
        },
    )
    assert response.status_code == 401
