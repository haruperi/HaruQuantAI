"""An empty Data Manager can read retained data without an acquisition provider."""

import asyncio
import base64
import json
from pathlib import Path

import pytest
from app.host.bootstrap import BootstrapCoordinator
from app.host.capabilities import HostCapabilities, ResourceAccess
from app.host.packages import (
    apply_removal,
    plan_removal,
    restore_removal,
    scan_packages,
)
from app.host.transport import create_app
from app.persistence.resources import ResourceStore
from app.workspace.DataManager.workspace import prepare
from starlette.testclient import TestClient
from tests.host.conftest import make_config


def test_empty_workspace_resource_read_and_unavailable_acquisition(tmp_path):
    store = ResourceStore(tmp_path)
    reference = store.publish(
        "removed.producer",
        "1.0.0",
        b"preserved",
        schema_id="test.bytes",
        schema_version="1.0.0",
        schema_json="{}",
        media_type="text/plain",
        readers=("*",),
    )

    async def run() -> None:
        context = HostCapabilities(
            ResourceAccess("workspace.data_manager", "1.0.0", store), None, None
        )
        owner = await prepare(context)
        assert await owner.invoke("capabilities", None) == {"providers": []}
        assert await owner.invoke("resources.list", None) == [
            reference.model_dump(mode="json")
        ]
        result = await owner.invoke("resources.read", reference.model_dump(mode="json"))
        assert isinstance(result, dict)
        assert result["content_base64"] == "cHJlc2VydmVk"
        with pytest.raises(ValueError, match="Missing acquisition"):
            await owner.invoke("download", None)
        await owner.close()
        assert store.read("consumer", reference)[0] == b"preserved"

    asyncio.run(run())


def test_missing_declared_service_fails_closed():
    with pytest.raises(ValueError, match=r"Missing host\.resources"):
        asyncio.run(prepare(HostCapabilities(None, None, None)))


def test_real_workspace_restart_removal_retains_resources(tmp_path):
    host_config = make_config(tmp_path)
    root = host_config.data_dir / "installation"
    directory = root / "app/workspace/DataManager"
    directory.mkdir(parents=True)
    source = (
        Path(__file__).resolve().parents[3] / "app/workspace/DataManager/workspace.py"
    )
    (directory / "workspace.py").write_bytes(source.read_bytes())
    (directory / "package.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "workspace.data_manager",
                "kind": "workspace",
                "version": "1.0.0",
                "host_contract": "1.0.0",
                "mode": "headless",
                "backend_entry": "app/workspace/DataManager/workspace.py",
                "owned_paths": {
                    "source": ["app/workspace/DataManager/workspace.py"],
                    "metadata": ["app/workspace/DataManager/package.json"],
                },
            }
        )
    )
    host = BootstrapCoordinator(host_config, installation_root=root)
    reference = host.resource_store.publish(
        "workspace.data_manager",
        "1.0.0",
        b"retained data",
        schema_id="test.data",
        schema_version="1.0.0",
        schema_json='{"type":"string"}',
        media_type="text/plain",
        readers=("*",),
    )
    resource_path = host_config.data_dir / "resources" / f"{reference.id}.1.json"
    saved = resource_path.read_bytes()
    route = "/api/v1/contributions/workspace.data_manager/capabilities"
    with TestClient(
        create_app(host), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    ) as browser:
        token = browser.post("/api/v1/auth/login", json={}).json()["data"]["token"]
        headers = {"Authorization": "Bearer " + token}
        assert browser.post(route, json={}, headers=headers).json()["data"] == {
            "providers": []
        }
        with pytest.raises(FileExistsError):
            apply_removal(
                root, plan_removal(root, scan_packages(root), "workspace.data_manager")
            )
    journal = apply_removal(
        root, plan_removal(root, scan_packages(root), "workspace.data_manager")
    )
    restarted = BootstrapCoordinator(host_config, installation_root=root)
    with TestClient(
        create_app(restarted), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    ) as browser:
        token = browser.post("/api/v1/auth/login", json={}).json()["data"]["token"]
        headers = {"Authorization": "Bearer " + token}
        assert browser.post(route, json={}, headers=headers).status_code == 503
        assert browser.get("/api/v1/status").status_code == 200
        assert browser.get("/api/v1/resources/", headers=headers).json()["data"] == [
            reference.model_dump(mode="json")
        ]
        result = browser.post(
            "/api/v1/resources/read",
            json=reference.model_dump(mode="json"),
            headers=headers,
        )
        assert (
            base64.b64decode(result.json()["data"]["content_base64"])
            == b"retained data"
        )
        assert (
            browser.post(
                "/api/v1/resources/read", json=reference.model_dump(mode="json")
            ).status_code
            == 401
        )
    assert resource_path.read_bytes() == saved
    restore_removal(root, journal)
    restored = BootstrapCoordinator(host_config, installation_root=root)
    with TestClient(
        create_app(restored), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    ) as browser:
        token = browser.post("/api/v1/auth/login", json={}).json()["data"]["token"]
        assert (
            browser.post(
                route, json={}, headers={"Authorization": "Bearer " + token}
            ).status_code
            == 200
        )


def test_workspace_logging(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Workspace operations emit expected structured log messages."""
    store = ResourceStore(tmp_path)

    async def run() -> None:
        context = HostCapabilities(
            ResourceAccess("workspace.data_manager", "1.0.0", store), None, None
        )
        with caplog.at_level("INFO", logger="app.workspace.DataManager.workspace"):
            owner = await prepare(context)
            await owner.invoke("capabilities", None)
            await owner.close()

        assert "Preparing Data Manager workspace" in caplog.text
        assert "Data Manager invoking: capabilities" in caplog.text
        assert "Data Manager workspace closed" in caplog.text

    asyncio.run(run())
