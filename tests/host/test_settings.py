"""Host settings transactional updates preserve records and redact credentials."""

import json
import sqlite3
from contextlib import closing
from typing import Any

import pytest
from app.host.settings import (
    PUBLIC_FIELDS,
    SettingsConflictError,
    SettingsError,
    SettingsStore,
)
from app.persistence.host import (
    HostSettingRecord,
    HostStore,
    prepare_boot_database,
    utc_now_iso,
)


def test_settings_round_trip_conflict_and_secret_preservation(host_config):
    path = host_config.database_path
    prepare_boot_database(path)
    store = SettingsStore(path)
    HostStore(path).upsert_setting(
        HostSettingRecord(
            "application",
            "notify.email",
            json.dumps(
                {
                    "password": "never-expose",  # pragma: allowlist secret
                    "smtp_server": "old",
                }
            ),
            1,
            utc_now_iso(),
        )
    )
    assert store.snapshot() == {
        "revision": 0,
        "values": {"notify.email": {"smtp_server": "old"}},
    }
    saved = store.patch({"notify.email": {"smtp_server": "new"}}, 0)
    assert saved["revision"] == 1
    with pytest.raises(SettingsConflictError):
        store.patch({"notify.email": {"smtp_server": "stale"}}, 0)
    raw = HostStore(path).get_setting("application", "notify.email")
    assert raw is not None
    assert (
        json.loads(raw.value_json)["password"]
        == "never-expose"  # pragma: allowlist secret
    )
    assert SettingsStore(path).snapshot() == saved


@pytest.mark.parametrize(
    "change",
    [
        {},
        {"unknown": {"value": 1}},
        {"config.cpu": {"custom_cores": True}},
        {"config.cpu": {"core_usage": "unsupported"}},
        {"app.general": {"zoom": 4}},
        {
            "notify.email": {"password": "secret"}  # pragma: allowlist secret
        },
        {"config.global": {"header_custom_text": "x" * 31}},
        {"config.memory": {"memory_limit_gb": float("nan")}},
        {"config.databanks": {"databank_sync_interval_mins": -1}},
    ],
)
def test_invalid_changes_are_not_written(host_config, change):
    prepare_boot_database(host_config.database_path)
    store = SettingsStore(host_config.database_path)
    with pytest.raises(SettingsError):
        store.patch(change, 0)
    assert store.snapshot()["revision"] == 0


def test_all_public_field_types_and_ranges(host_config):
    from app.host.settings import ALLOWED_VALUES, FIELD_RANGES

    prepare_boot_database(host_config.database_path)
    values: dict[str, Any] = {}
    for key, fields in PUBLIC_FIELDS.items():
        values[key] = {}
        for field, kind in fields.items():
            values[key][field] = (
                ALLOWED_VALUES.get(field, (None,))[0]
                if field in ALLOWED_VALUES
                else FIELD_RANGES[field][0]
                if field in FIELD_RANGES
                else {
                    "str": "example",
                    "bool": False,
                    "int": 1,
                    "number": 2,
                    "interval": None,
                }[kind]
            )
    saved = SettingsStore(host_config.database_path).patch(values, 0)
    assert saved["values"] == values


def test_malformed_existing_record_and_revision_fail_closed(host_config):
    prepare_boot_database(host_config.database_path)
    store = SettingsStore(host_config.database_path)
    with closing(sqlite3.connect(host_config.database_path)) as conn:
        conn.execute(
            "INSERT INTO host_settings VALUES ('application','config.cpu','[]',1,'now')"
        )
        conn.commit()
    with pytest.raises(SettingsError):
        store.snapshot()


def test_endpoint_updates_publish_after_commit(client, auth_headers, services):
    subscriber = services.events.subscribe(["settings.changed"])
    changes = {"config.cpu": {"core_usage": "custom", "custom_cores": 4}}
    result = client.put(
        "/api/v1/settings",
        json={"expected_revision": 0, "changes": changes},
        headers=auth_headers,
    )
    assert result.status_code == 200
    assert subscriber.queue.get_nowait()["data"] == changes
    assert (
        client.get("/api/v1/settings", headers=auth_headers).json()["data"]
        == result.json()["data"]
    )
    assert (
        client.put(
            "/api/v1/settings",
            json={"expected_revision": 0, "changes": changes},
            headers=auth_headers,
        ).status_code
        == 409
    )
    assert subscriber.queue.empty()
    assert (
        client.put(
            "/api/v1/settings", json={"changes": changes}, headers=auth_headers
        ).status_code
        == 400
    )
    assert (
        client.put(
            "/api/v1/settings",
            json={"expected_revision": 1, "changes": {"bad": {"x": 1}}},
            headers=auth_headers,
        ).status_code
        == 400
    )
