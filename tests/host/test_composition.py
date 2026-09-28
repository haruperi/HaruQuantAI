"""Real isolated modules prove validation precedes trusted activation."""

import asyncio
import json
from pathlib import Path

import pytest
from app.host.composition import Composition
from app.host.jobs import JobManager
from app.host.packages import scan_packages
from app.host.resource_store import ResourceStore


def package(
    root: Path,
    name: str,
    owner: str | None = None,
    *,
    slot: str = "test.slot",
    failure: bool = False,
) -> Path:
    folder = f"app/{'plugins' if owner else 'workspace'}/{name}"
    path = root / folder
    path.mkdir(parents=True)
    descriptor = {
        "id": "test." + name,
        "version": "1.0.0",
        "compatibility": "1",
        "kind": "plugin" if owner else "workspace",
        "owner_workspace_id": owner,
        "slot_id": slot if owner else None,
        "contract_version": "1.0.0" if owner else None,
        "slots": [] if owner else [{"id": "test.slot", "version": "1.0.0"}],
        "requires": [{"id": "host.resources", "version": "1.0.0"}],
    }
    source = f"""PLUGIN = {descriptor!r}
from app.host.composition import PreparedContribution
async def prepare(context):
    assert context.resources.owner == {descriptor["id"]!r}
    assert context.jobs is None
    if {failure!r}:
        raise RuntimeError('isolated failure')
    async def invoke(operation, payload):
        return payload
    async def close():
        return None
    return PreparedContribution(('echo',), invoke, close)
"""
    (path / "entry.py").write_text(source)
    metadata = {
        "schema_version": 1,
        "id": descriptor["id"],
        "kind": descriptor["kind"],
        "version": "1.0.0",
        "host_contract": "1.0.0",
        "mode": "headless",
        "owner_workspace_id": owner,
        "attachment": {"slot_id": slot, "contract_version": "1.0.0"} if owner else None,
        "backend_entry": folder + "/entry.py",
        "ui_entry": None,
        "owned_paths": {
            "source": [folder + "/entry.py"],
            "metadata": [folder + "/package.json"],
        },
    }
    (path / "package.json").write_text(json.dumps(metadata))
    return path


def test_healthy_and_failed_children_are_isolated(tmp_path):
    package(tmp_path, "owner")
    package(tmp_path, "good", "test.owner")
    package(tmp_path, "bad", "test.owner", failure=True)
    package(tmp_path, "wrong", "test.owner", slot="test.other")

    async def run() -> None:
        composition = Composition(
            tmp_path, ResourceStore(tmp_path / "data"), JobManager(2, 1024)
        )
        await composition.start(scan_packages(tmp_path))
        assert set(composition.active) == {"test.owner", "test.good"}
        assert await composition.invoke("test.good", "echo", {"value": 1}) == {
            "value": 1
        }
        assert {i.code for i in composition.issues} == {
            "activation_failed",
            "incompatible_slot",
        }
        with pytest.raises(ValueError, match="Missing"):
            await composition.invoke("test.bad", "echo", None)
        await composition.close()
        assert not composition.active

    asyncio.run(run())


def test_missing_owner_does_not_import_orphan(tmp_path):
    orphan = package(tmp_path, "orphan", "test.missing")
    (orphan / "entry.py").write_text("raise RuntimeError('must not import')")

    async def run() -> None:
        composition = Composition(
            tmp_path, ResourceStore(tmp_path / "data"), JobManager(1, 1024)
        )
        await composition.start(scan_packages(tmp_path))
        assert not composition.active
        assert composition.issues[0].code == "missing_owner"
        await composition.close()

    asyncio.run(run())


def test_empty_workspace_and_empty_installation(tmp_path):
    owner = package(tmp_path, "owner")

    async def run() -> None:
        composition = Composition(
            tmp_path, ResourceStore(tmp_path / "data"), JobManager(1, 1024)
        )
        await composition.start(scan_packages(tmp_path))
        assert list(composition.active) == ["test.owner"]
        await composition.close()
        for file in owner.iterdir():
            if file.is_file():
                file.unlink()
        await composition.start(scan_packages(tmp_path))
        assert not composition.active

    asyncio.run(run())
