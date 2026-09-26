"""Isolated host fixtures; no test opens the shared application database."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from app.host.bootstrap import BootstrapCoordinator
from app.host.config import HostSettings
from app.host.http_server import create_app
from starlette.testclient import TestClient


def make_config(tmp_path: Path) -> HostSettings:
    return HostSettings(
        data_dir=tmp_path,
        roots=(tmp_path / "contributions",),
        ui_dist=tmp_path / "dist",
    )


@pytest.fixture
def host_config(tmp_path: Path) -> HostSettings:
    return make_config(tmp_path)


@pytest.fixture
def services(host_config: HostSettings) -> BootstrapCoordinator:
    return BootstrapCoordinator(host_config)


@pytest.fixture
def settings_path(host_config: HostSettings) -> Path:
    return host_config.database_path


@pytest.fixture
def client(services: BootstrapCoordinator) -> Iterator[TestClient]:
    with TestClient(
        create_app(services), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    ) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    result = client.post("/api/v1/auth/login", json={"username": "operator"})
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["data"]["token"]}
