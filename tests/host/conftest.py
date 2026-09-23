"""Shared fixtures for the host test suite."""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.host.bootstrapper import HostConfig, build_services
from app.host.webserver import HostServices, create_app
from starlette.testclient import TestClient


def make_config(tmp_path: Path) -> HostConfig:
    """Build an isolated host configuration rooted in ``tmp_path``."""
    return HostConfig(
        address="127.0.0.1",
        port=8000,
        log_dir=tmp_path / "logs",
        password=None,
        settings_path=tmp_path / "user" / "settings.json",
        exchange_root=tmp_path / "exchange",
        domain_roots=(tmp_path / "domains",),
        ui_dist=None,
    )


@pytest.fixture
def host_config(tmp_path: Path) -> HostConfig:
    return make_config(tmp_path)


@pytest.fixture
def settings_path(tmp_path: Path) -> Path:
    return tmp_path / "user" / "settings.json"


@pytest.fixture
def services(host_config: HostConfig) -> HostServices:
    return build_services(host_config)


@pytest.fixture
def client(services: HostServices) -> Iterator[TestClient]:
    app = create_app(services, logging.getLogger("tests.host"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "tester"})
    assert response.status_code == 200
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
