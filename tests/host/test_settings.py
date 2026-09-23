"""Tests for the file-backed settings store and its endpoints."""

import json
from pathlib import Path

import pytest
from app.host.events import SETTINGS_CHANNEL
from app.host.settings import SettingsError, SettingsStore
from app.host.webserver import HostServices
from starlette.testclient import TestClient


def test_missing_file_yields_empty_settings(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")

    assert store.get_all() == {}


def test_patch_persists_atomically_and_reloads(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)

    store.patch({"skin": "dark", "language": "English"})

    assert json.loads(path.read_text(encoding="utf-8"))["skin"] == "dark"
    reloaded = SettingsStore(path)
    assert reloaded.get_all() == {"skin": "dark", "language": "English"}
    leftovers = [item.name for item in tmp_path.iterdir() if item.suffix == ".tmp"]
    assert leftovers == []


def test_patch_merges_shallowly(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    store.patch({"a": 1, "nested": {"x": 1}})

    store.patch({"nested": {"y": 2}})

    assert store.get_all()["nested"] == {"y": 2}


def test_corrupt_settings_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(SettingsError):
        SettingsStore(path)


def test_non_object_settings_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("[1, 2]", encoding="utf-8")

    with pytest.raises(SettingsError):
        SettingsStore(path)


def test_settings_endpoints_round_trip(
    client: TestClient, auth_headers: dict[str, str], settings_path: Path
) -> None:
    put = client.put("/api/v1/settings", json={"skin": "light"}, headers=auth_headers)
    get = client.get("/api/v1/settings", headers=auth_headers)

    assert put.status_code == 200
    assert put.json()["data"] == {"skin": "light"}
    assert get.status_code == 200
    assert get.json()["data"] == {"skin": "light"}
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted == {"skin": "light"}


def test_settings_change_publishes_event(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    subscriber = services.events.subscribe([SETTINGS_CHANNEL])

    response = client.put("/api/v1/settings", json={"zoom": 100}, headers=auth_headers)

    assert response.status_code == 200
    event = subscriber.queue.get_nowait()
    assert event["channel"] == SETTINGS_CHANNEL
    assert event["data"] == {"zoom": 100}


def test_settings_requires_auth(client: TestClient) -> None:
    response = client.put("/api/v1/settings", json={"skin": "dark"})

    assert response.status_code == 401
