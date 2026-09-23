"""Tests for status probe and graceful shutdown."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.host.webserver import HOST_VERSION, HostServices
from starlette.applications import Starlette
from starlette.testclient import TestClient


def test_status_is_public_and_shaped(client: TestClient) -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "running"
    assert data["version"] == HOST_VERSION
    assert data["ui_ready"] is False
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["pid"], int)
    assert data["cpu_count"] >= 1
    assert isinstance(data["platform"], str) and data["platform"]
    assert isinstance(data["system"], str) and data["system"]
    assert isinstance(data["python_version"], str) and data["python_version"]
    assert data["memory_total_bytes"] is None or data["memory_total_bytes"] > 0
    assert data["memory_available_bytes"] is None or data["memory_available_bytes"] > 0


def test_ui_readiness_lifecycle_progression(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    # Initial state before app-loaded
    assert not services.lifecycle.ui_ready
    res_status_before = client.get("/api/v1/status")
    assert res_status_before.status_code == 200
    assert res_status_before.json()["data"]["ui_ready"] is False

    res_health_before = client.get("/api/v1/health")
    assert res_health_before.status_code == 200
    assert res_health_before.json()["data"]["services"] == {
        "host": "ready",
        "ui": "pending",
    }

    # app-loaded requires auth, records readiness
    res_loaded = client.post(
        "/api/v1/app-loaded", json={"product": "web"}, headers=auth_headers
    )
    assert res_loaded.status_code == 200
    assert res_loaded.json()["data"] == {"acknowledged": True}
    assert bool(services.lifecycle.ui_ready)

    # After app-loaded, status and health reflect ui_ready: True
    res_status_after = client.get("/api/v1/status")
    assert res_status_after.status_code == 200
    assert res_status_after.json()["data"]["ui_ready"] is True

    res_health_after = client.get("/api/v1/health")
    assert res_health_after.status_code == 200
    assert res_health_after.json()["data"]["services"] == {
        "host": "ready",
        "ui": "ready",
    }


def test_shutdown_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/shutdown")

    assert response.status_code == 401


def test_shutdown_sets_the_graceful_flag(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    response = client.post("/api/v1/shutdown", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["data"] == {"shutdown": "requested"}
    assert services.lifecycle.shutdown_requested is True


def test_linux_memory_parsing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.host.lifecycle import _linux_memory

    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal:        16384 kB\nMemAvailable:     8192 kB\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "app.host.lifecycle.Path",
        lambda p: meminfo if str(p) == "/proc/meminfo" else Path(p),
    )
    total, avail = _linux_memory()
    assert total == 16384 * 1024
    assert avail == 8192 * 1024


def test_system_memory_unknown_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.host.lifecycle import _system_memory

    monkeypatch.setattr("platform.system", lambda: "UnknownOS")
    assert _system_memory() == (None, None)


def test_shutdown_with_attached_uvicorn_server(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert isinstance(client.app, Starlette)
    fake_server = MagicMock()
    fake_server.should_exit = False
    client.app.state.uvicorn_server = fake_server
    try:
        response = client.post("/api/v1/shutdown", headers=auth_headers)
        assert response.status_code == 200
        assert fake_server.should_exit is True
    finally:
        del client.app.state.uvicorn_server
