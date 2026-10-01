"""Unit tests for host capabilities and scoped settings access."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from app.host.capabilities import HostCapabilities, SettingsAccess
from app.host.jobs import JobManager
from app.host.packages import Composition, scan_packages
from app.host.settings import SettingsStore
from app.persistence.host import prepare_boot_database
from app.persistence.resources import ResourceStore


class DummyStore:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, Any]] = {}

    def get_private(self, owner: str, key: str) -> dict[str, Any] | None:
        return self.data.get(f"{owner}:{key}")

    def set_private(self, owner: str, key: str, value: dict[str, Any]) -> None:
        self.data[f"{owner}:{key}"] = dict(value)


def test_settings_access_scoping() -> None:
    store = DummyStore()
    access_a = SettingsAccess("owner.a", store)
    access_b = SettingsAccess("owner.b", store)

    assert access_a.get("config") is None
    access_a.set("config", {"timeout": 30})

    assert access_a.get("config") == {"timeout": 30}
    assert access_b.get("config") is None


def test_settings_access_with_settings_store(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    prepare_boot_database(db_path)
    store = SettingsStore(db_path)

    access_a = SettingsAccess("plugin.alpha", store)
    access_b = SettingsAccess("plugin.beta", store)

    access_a.set("prefs", {"active": True, "count": 5})
    assert access_a.get("prefs") == {"active": True, "count": 5}
    assert access_b.get("prefs") is None

    # Update
    access_a.set("prefs", {"active": False, "count": 10})
    assert access_a.get("prefs") == {"active": False, "count": 10}


def test_host_capabilities_defaults() -> None:
    caps = HostCapabilities(resources=None, jobs=None, log=None)
    assert caps.resources is None
    assert caps.jobs is None
    assert caps.log is None
    assert caps.settings is None


@pytest.mark.anyio
async def test_composition_supplies_settings_capability(tmp_path: Path) -> None:
    root = tmp_path / "install"
    db_path = tmp_path / "host.db"
    prepare_boot_database(db_path)
    settings_store = SettingsStore(db_path)
    resource_store = ResourceStore(tmp_path / "resources")
    job_manager = JobManager(1, 1024)

    pkg_dir = root / "app" / "workspace" / "test_workspace"
    pkg_dir.mkdir(parents=True)

    source = """PLUGIN = {
    "id": "test.workspace",
    "version": "1.0.0",
    "compatibility": "1",
    "kind": "workspace",
    "slots": [],
    "requires": [{"id": "host.settings", "version": "1.0.0"}],
}
from app.host.packages import PreparedContribution

async def prepare(context):
    assert context.settings is not None
    assert context.settings.owner == "test.workspace"
    context.settings.set("initial", {"ok": True})
    async def invoke(op, payload):
        return payload
    async def close():
        return None
    return PreparedContribution(("echo",), invoke, close)
"""
    folder = "app/workspace/test_workspace"
    (pkg_dir / "entry.py").write_text(source)

    metadata = {
        "schema_version": 1,
        "id": "test.workspace",
        "kind": "workspace",
        "version": "1.0.0",
        "host_contract": "1.0.0",
        "mode": "headless",
        "owner_workspace_id": None,
        "attachment": None,
        "backend_entry": folder + "/entry.py",
        "ui_entry": None,
        "owned_paths": {
            "source": [folder + "/entry.py"],
            "metadata": [folder + "/package.json"],
        },
    }
    import json

    (pkg_dir / "package.json").write_text(json.dumps(metadata))

    comp = Composition(root, resource_store, job_manager, settings=settings_store)
    inventory = scan_packages(root)
    assert len(inventory.packages) == 1

    await comp.start(inventory)
    assert "test.workspace" in comp.active

    # Check that settings were persisted under test.workspace
    access = SettingsAccess("test.workspace", settings_store)
    assert access.get("initial") == {"ok": True}


def test_terminal_worker_is_historical_only_and_reaped_on_cancellation(
    monkeypatch: Any,
) -> None:
    import asyncio

    from app.host.capabilities import TerminalAccess

    worker = "import sys,time\nfor line in sys.stdin:\n time.sleep(120)\n"
    monkeypatch.setattr("app.host.capabilities._TERMINAL_WORKER", worker)

    async def scenario() -> None:
        terminal = TerminalAccess("plugin.test")
        with pytest.raises(ValueError, match="Unsupported"):
            await terminal.call("order_send", {})
        task = asyncio.create_task(terminal.call("connect", {}))
        for _ in range(100):
            if terminal._process is not None:
                break
            await asyncio.sleep(0.01)
        process = terminal._process
        assert process is not None
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert process.returncode is not None
        assert terminal._process is None

    asyncio.run(scenario())


def test_terminal_worker_failure_does_not_return_synthetic_history(
    monkeypatch: Any,
) -> None:
    import asyncio

    from app.host.capabilities import TerminalAccess

    monkeypatch.setattr(
        "app.host.capabilities._TERMINAL_WORKER",
        'import sys\nsys.stdin.readline()\nsys.stdout.write(\'{"error":"failure"}\\n\')\nsys.stdout.flush()\n',
    )

    async def scenario() -> None:
        terminal = TerminalAccess("plugin.test")
        with pytest.raises(ValueError, match="Terminal operation failed"):
            await terminal.call("history", {})
        assert terminal._process is None

    asyncio.run(scenario())
