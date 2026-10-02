"""Unit tests for host capabilities and scoped settings access."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from app.host.capabilities import HostCapabilities, SettingsAccess, TerminalAccess
from app.host.jobs import JobManager
from app.host.packages import Composition, scan_packages
from app.host.settings import MT5TerminalConfiguration, SettingsStore
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
    tmp_path: Path,
) -> None:
    import asyncio

    from app.host.capabilities import TerminalAccess

    worker = "import sys,time\nfor line in sys.stdin:\n time.sleep(120)\n"
    monkeypatch.setattr("app.host.capabilities._TERMINAL_WORKER", worker)

    async def scenario() -> None:
        terminal = TerminalAccess("plugin.test")
        with pytest.raises(ValueError, match="Unsupported"):
            await terminal.call("order_send", {})
        executable = tmp_path / "terminal64.exe"
        executable.touch()
        task = asyncio.create_task(terminal.call("connect", {"path": str(executable)}))
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


@pytest.mark.parametrize(
    "case",
    ["missing", "disabled", "blank", "gone", "directory", "wrong_name", "bad_manual"],
)
def test_terminal_invalid_selection_cannot_spawn(
    tmp_path: Path, monkeypatch: Any, case: str
) -> None:
    import asyncio

    executable = tmp_path / "terminal64.exe"
    executable.touch()
    config = MT5TerminalConfiguration(True, str(executable))
    arguments: dict[str, Any] = {}
    if case == "disabled":
        config = MT5TerminalConfiguration(False, str(executable))
    elif case == "blank":
        config = MT5TerminalConfiguration(True, " ")
    elif case == "gone":
        executable.unlink()
    elif case == "directory":
        executable.unlink()
        executable.mkdir()
    elif case == "wrong_name":
        config = MT5TerminalConfiguration(True, str(tmp_path / "other.exe"))
    elif case == "bad_manual":
        arguments = {"path": str(tmp_path / "missing" / "terminal64.exe")}

    async def forbidden_spawn(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Invalid terminal selection started a worker")

    monkeypatch.setattr("asyncio.create_subprocess_exec", forbidden_spawn)
    terminal = TerminalAccess(
        "plugin.test", None if case == "missing" else lambda: config
    )
    with pytest.raises(ValueError):
        asyncio.run(terminal.call("connect", arguments))
    assert terminal._process is None


def test_terminal_uses_latest_saved_path_and_portable_without_credentials(
    tmp_path: Path, monkeypatch: Any, caplog: Any
) -> None:
    import asyncio
    import json

    from app.persistence.host import HostSettingRecord, HostStore, utc_now_iso

    prepare_boot_database(tmp_path / "settings.db")
    store = SettingsStore(tmp_path / "settings.db")
    persistence = HostStore(tmp_path / "settings.db")
    worker = (
        "import sys,json\nfor line in sys.stdin:\n"
        " request=json.loads(line)\n"
        " sys.stdout.write(json.dumps({'value':request['arguments']})+'\\n')\n"
        " sys.stdout.flush()\n"
    )
    monkeypatch.setattr("app.host.capabilities._TERMINAL_WORKER", worker)
    terminal = TerminalAccess("plugin.test", store.mt5_terminal_configuration)
    caplog.set_level("INFO")

    async def scenario() -> None:
        for name, portable in (("first", False), ("second", True)):
            directory = tmp_path / name
            directory.mkdir()
            executable = directory / "terminal64.exe"
            executable.touch()
            persistence.upsert_setting(
                HostSettingRecord(
                    "application",
                    "config.metatrader5",
                    json.dumps(
                        {
                            "enabled": True,
                            "terminal_path": str(executable),
                            "portable": portable,
                            "password": "private-test-value",  # pragma: allowlist secret
                            "account_id": "private-account",
                            "server": "private-server",
                        }
                    ),
                    1,
                    utc_now_iso(),
                )
            )
            assert await terminal.call("connect", {}) == {
                "path": str(executable),
                "portable": portable,
            }
            await terminal.close()
        override = tmp_path / "terminal64.exe"
        override.touch()
        persistence.upsert_setting(
            HostSettingRecord(
                "application",
                "config.metatrader5",
                '{"enabled":false,"terminal_path":""}',
                1,
                utc_now_iso(),
            )
        )
        assert await terminal.call(
            "connect", {"path": str(override), "password": "ignored"}
        ) == {"path": str(override), "portable": False}
        await terminal.close()

    asyncio.run(scenario())
    assert "source=global" in caplog.text
    assert "source=manual" in caplog.text
    for private in (
        str(tmp_path),
        "private-test-value",
        "private-account",
        "private-server",
    ):
        assert private not in caplog.text


@pytest.mark.parametrize("success", [True, False])
def test_native_worker_initializes_one_explicit_path_without_fallback(
    tmp_path: Path, monkeypatch: Any, success: bool
) -> None:
    import asyncio
    import json

    from app.host.capabilities import _TERMINAL_WORKER

    executable = tmp_path / "terminal64.exe"
    executable.touch()
    capture = tmp_path / "calls.jsonl"
    stub = (
        "import sys,types,json\n"
        "def initialize(**options):\n"
        f" with open({str(capture)!r},'a') as stream:\n"
        "  stream.write(json.dumps(options)+'\\n')\n"
        f" return {success!r}\n"
        "sys.modules['MetaTrader5']=types.SimpleNamespace(\n"
        " initialize=initialize,shutdown=lambda:None)\n"
    )
    monkeypatch.setattr(
        "app.host.capabilities._TERMINAL_WORKER", stub + _TERMINAL_WORKER
    )
    terminal = TerminalAccess(
        "plugin.test", lambda: MT5TerminalConfiguration(True, str(executable), True)
    )

    async def scenario() -> None:
        if success:
            assert await terminal.call("connect", {}) is True
            await terminal.close()
        else:
            with pytest.raises(ValueError, match="Terminal operation failed"):
                await terminal.call("connect", {})
            assert terminal._process is None

    asyncio.run(scenario())
    assert [json.loads(line) for line in capture.read_text().splitlines()] == [
        {"path": str(executable), "portable": True, "timeout": 30000}
    ]


def test_native_worker_tick_protocol_excludes_prices_and_account_data(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import asyncio

    from app.host.capabilities import _TERMINAL_WORKER

    executable = tmp_path / "terminal64.exe"
    executable.touch()
    stub = "import sys,types\nsys.modules['MetaTrader5']=types.SimpleNamespace(initialize=lambda **kw:True,shutdown=lambda:None,symbol_info_tick=lambda symbol:types.SimpleNamespace(time_msc=123000,time=123,bid='private-price'))\n"
    monkeypatch.setattr(
        "app.host.capabilities._TERMINAL_WORKER", stub + _TERMINAL_WORKER
    )
    terminal = TerminalAccess(
        "plugin.test", lambda: MT5TerminalConfiguration(True, str(executable))
    )

    async def scenario() -> None:
        await terminal.call("connect", {})
        sample = await terminal.call("tick", {"symbol": "TEST"})
        assert set(sample) == {
            "time_msc",
            "utc_before",
            "utc_after",
            "monotonic_before",
            "monotonic_after",
        }
        assert sample["time_msc"] == 123000
        with pytest.raises(
            ValueError, match="Unsupported historical terminal operation"
        ):
            await terminal.call("order_send", {})
        await terminal.close()

    asyncio.run(scenario())


def test_mt5_authorized_market_access(tmp_path: Path) -> None:
    from app.host.capabilities import MarketAccess
    from app.persistence.market import MarketDataStore, create_isolated_schema

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    mt5_access = MarketAccess("plugin.data_manager.meta_trader", store)
    assert mt5_access._authorized_source() == "mt5"

    ds = mt5_access.register_dataset("eurusd", "m1", "EURUSD", broker="-1")
    assert ds.source == "mt5"
    assert ds.symbol == "eurusd"
    assert ds.kind == "m1"

    assert len(mt5_access.list_datasets()) == 1
    assert mt5_access.get_dataset(ds.id).symbol == "eurusd"

    root = mt5_access.market_root()
    assert root == str(tmp_path / "market" / "mt5")

    path_m1 = mt5_access.market_path("m1", "eurusd", "2024")
    assert path_m1 == str(
        tmp_path / "market" / "mt5" / "m1" / "eurusd" / "2024.parquet"
    )

    path_ticks = mt5_access.market_path("ticks", "eurusd", "2024-05")
    assert path_ticks == str(
        tmp_path / "market" / "mt5" / "ticks" / "eurusd" / "2024" / "05-may.parquet"
    )

    unauthorized = MarketAccess("plugin.unauthorized", store)
    with pytest.raises(PermissionError, match="ownership denied"):
        unauthorized.register_dataset("eurusd", "m1", "EURUSD")
    with pytest.raises(PermissionError, match="ownership denied"):
        unauthorized._authorized_source()
