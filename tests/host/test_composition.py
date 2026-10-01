"""Real isolated modules prove validation precedes trusted activation."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from app.host.jobs import JobManager
from app.host.packages import Composition, scan_packages
from app.persistence.resources import ResourceStore


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
from app.host.packages import PreparedContribution
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


def test_healthy_and_failed_children_are_isolated(tmp_path: Path) -> None:
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
        assert cast(
            "Any", await composition.invoke("test.good", "echo", {"value": 1})
        ) == {"value": 1}
        assert {i.code for i in composition.issues} == {
            "activation_failed",
            "incompatible_slot",
        }
        with pytest.raises(ValueError, match="Missing"):
            cast("Any", await composition.invoke("test.bad", "echo", None))
        await composition.close()
        assert not composition.active

    asyncio.run(run())


def test_missing_owner_does_not_import_orphan(tmp_path: Path) -> None:
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


def test_bound_operations_are_published_and_dispatchable(tmp_path: Path) -> None:
    """A workspace's post-attachment routes pass the host operation allowlist."""
    parent = package(tmp_path, "owner")
    package(tmp_path, "child", "test.owner")
    entry = parent / "entry.py"
    source = entry.read_text()
    source = source.replace(
        "    return PreparedContribution(('echo',), invoke, close)",
        """    bindings = ()
    async def attach(children):
        nonlocal bindings
        bindings = children
    def routes():
        return tuple('child.' + op for child in bindings for op in child.operations)
    return PreparedContribution(('echo',), invoke, close, attach, routes)""",
    )
    entry.write_text(source)

    async def run() -> None:
        composition = Composition(
            tmp_path, ResourceStore(tmp_path / "data"), JobManager(1, 1024)
        )
        await composition.start(scan_packages(tmp_path))
        assert not composition.issues
        assert cast(
            "Any", await composition.invoke("test.owner", "child.echo", {"value": 7})
        ) == {"value": 7}
        parent_catalog = next(
            item
            for item in composition.catalog()["domains"]
            if item["id"] == "test.owner"
        )
        assert parent_catalog["operations"] == ["echo", "child.echo"]
        with pytest.raises(ValueError, match="Missing capability"):
            cast("Any", await composition.invoke("test.owner", "child.undeclared", {}))
        await composition.close()

    asyncio.run(run())


def test_empty_workspace_and_empty_installation(tmp_path: Path) -> None:
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


def test_dynamically_loaded_module_name_and_logger_identity(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    folder = "app/workspace/logger_test"
    path = tmp_path / folder
    path.mkdir(parents=True)
    descriptor = {
        "id": "test.logger",
        "version": "1.0.0",
        "compatibility": "1",
        "kind": "workspace",
        "slots": [],
        "requires": [{"id": "host.resources", "version": "1.0.0"}],
    }
    source = f"""PLUGIN = {descriptor!r}
from app.host.logging import get_logger
from app.host.packages import PreparedContribution

logger = get_logger(__name__)

async def prepare(context):
    logger.info("Workspace activated with logger: %s", __name__)
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
        "backend_entry": folder + "/entry.py",
        "ui_entry": None,
        "owned_paths": {
            "source": [folder + "/entry.py"],
            "metadata": [folder + "/package.json"],
        },
    }
    (path / "package.json").write_text(json.dumps(metadata))

    async def run() -> None:
        composition = Composition(
            tmp_path, ResourceStore(tmp_path / "data"), JobManager(1, 1024)
        )
        with caplog.at_level("INFO", logger="app.workspace.logger_test.entry"):
            await composition.start(scan_packages(tmp_path))
            assert "test.logger" in composition.active
            mod = composition._modules["test.logger"]
            assert mod.__name__ == "app.workspace.logger_test.entry"
            assert sys.modules.get("app.workspace.logger_test.entry") is mod
            assert (
                "Workspace activated with logger: app.workspace.logger_test.entry"
                in caplog.text
            )

        await composition.close()
        assert not composition.active
        assert "app.workspace.logger_test.entry" not in sys.modules

    asyncio.run(run())


@pytest.mark.parametrize(
    "removed",
    [
        "dukascopy",
        "yahoo",
        "crypto",
        "file_import",
        "meta_trader",
        "tick_downloader",
        "darwinex",
        "sq_equity",
        "sq_futures",
        "indicators",
    ],
)
def test_real_data_manager_pair_removal_preserves_resources(  # noqa: PLR0915 -- isolated lifecycle and custody matrix.
    tmp_path: Path, removed: str
) -> None:
    """Remove actual approved package files, restart, and read retained prices."""
    import shutil
    from datetime import UTC, datetime

    import pyarrow as pa  # type: ignore[import-untyped]
    from app.host.capabilities import MarketAccess
    from app.host.packages import apply_removal, plan_removal, restore_removal
    from app.persistence.market import (
        M1_SCHEMA,
        MarketDataStore,
        create_isolated_schema,
    )

    repository = Path(__file__).resolve().parents[2]
    inventory = scan_packages(repository)
    assert not inventory.issues
    cohort = [
        package
        for package in inventory.packages
        if package.id == "workspace.data_manager"
        or package.owner_workspace_id == "workspace.data_manager"
    ]
    for item in cohort:
        for relative in item.owned_paths.files():
            destination = tmp_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repository / relative, destination)
    original = scan_packages(tmp_path)
    assert not original.issues
    data = tmp_path / "data"
    database = data / "database" / "haruquantai.db"
    create_isolated_schema(database)
    owner = "plugin.data_manager." + removed
    initially_present = any(package.id == owner for package in original.packages)
    store = MarketDataStore(data, database)
    writer = MarketAccess(owner, store)
    identity = writer.register_source(
        source="Removal fixture",
        symbol="EURUSD",
        underlying="EURUSD",
        instrument="EURUSD",
        timeframe="M1",
    )
    table = pa.Table.from_pylist(
        [
            {
                "DateTime": datetime(2024, 1, 1, tzinfo=UTC),
                "Open": 1.1,
                "High": 1.2,
                "Low": 1.0,
                "Close": 1.15,
                "Volume": 7,
            }
        ],
        schema=M1_SCHEMA,
    )
    writer.publish_source(identity, "2024", table, expected_revision=0)
    before = store.source_partitions(identity)

    async def start_and_close(expect_removed: bool) -> None:
        jobs = JobManager(2, 2 * 1024**3)
        composition = Composition(
            tmp_path, ResourceStore(data / "resources"), jobs, settings={}
        )
        await composition.start(scan_packages(tmp_path))
        assert not composition.issues, composition.issues
        assert (owner in composition.active) is not expect_removed
        workspace = composition.active.get("workspace.data_manager")
        if workspace is None:
            assert "workspace.data_manager" not in {
                package.id for package in original.packages
            }
            independent = MarketDataStore(data, database)
            assert independent.source_partitions(identity) == before
            assert independent.read_source(identity).equals(table)
            await composition.close()
            await jobs.close()
            return
        rows = cast("Any", await workspace.invoke("actions.list_datasets", {}))
        assert any(row["id"] == identity for row in rows)
        exported = cast(
            "Any",
            await workspace.invoke("actions.export_to_csv", {"dataset_id": identity}),
        )
        assert exported["records"] == 1
        assert "1.15" in exported["content"]
        for item in cohort:
            if item.backend_entry and item.kind == "plugin" and item.id != owner:
                assert item.id in composition.active
                if "catalog" in composition.active[item.id].operations:
                    actual = cast(
                        "Any", await composition.invoke(item.id, "catalog", {})
                    )
                    if item.id.endswith(".dukascopy"):
                        assert actual["modes"]["standard"] == "available"
                    else:
                        assert actual["available"] is True
        submitted = cast(
            "Any",
            await workspace.invoke(
                "actions.update_selected",
                {
                    "symbols": [identity],
                    "date_from": "2024-01-01",
                    "date_to": "2024-01-01",
                },
            ),
        )
        assert isinstance(submitted["errors"], list)
        assert not any(
            "Invalid acquisition catalog" in row["reason"]
            for row in submitted["errors"]
        )
        await composition.close()
        await jobs.close()

    asyncio.run(start_and_close(not initially_present))
    if not initially_present:
        independent = MarketDataStore(data, database)
        assert independent.source_partitions(identity) == before
        assert independent.read_source(identity).equals(table)
        assert scan_packages(tmp_path).fingerprint == original.fingerprint
        return
    plan = plan_removal(tmp_path, scan_packages(tmp_path), owner)
    assert plan.target_ids == (owner,)
    journal = apply_removal(tmp_path, plan)
    asyncio.run(start_and_close(True))
    independent = MarketDataStore(data, database)
    assert independent.source_partitions(identity) == before
    assert independent.read_source(identity).equals(table)
    restore_removal(tmp_path, journal)
    assert scan_packages(tmp_path).fingerprint == original.fingerprint
    asyncio.run(start_and_close(False))
