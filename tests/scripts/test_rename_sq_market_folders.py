"""Offline market folder migration tests using isolated host stores."""

import json
import sqlite3
from pathlib import Path

import pytest
from app.core.host.persistence import HostPersistence
from app.workspace.data_manager.sources import Sources

from scripts import rename_sq_market_folders as migration


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(migration, "ensure_offline", lambda: None)
    database = tmp_path / "data/database/haruquantai.db"
    database.parent.mkdir(parents=True)
    sqlite3.connect(database).close()
    gateway = HostPersistence(database)
    root = tmp_path / "data/market"
    service = Sources(gateway, market_root=root)
    for provider in migration.RENAMES:
        old = root / provider
        old.mkdir(parents=True)
        (old / (provider + ".csv")).write_text("Symbol\nTEST\n")
    row = service.add("sq_futures", [{"symbol": "@ES"}])["data"]["records"][0]
    path = root / "sq_futures/d1/@es"
    path.mkdir(parents=True)
    (path / "2024.parquet").write_bytes(b"fixture-preserved-byte-for-byte")
    lineage = json.loads(row["lineage_json"])
    lineage.update(
        partitions=[str(path / "2024.parquet")],
        note="sq_futures",
        nested={"source_path": "data/market/sq_futures/d1/@es"},
    )
    migration.require(
        gateway.update_record(
            "datamgr_datasets",
            {"path": str(path), "lineage_json": json.dumps(lineage)},
            filters={"id": row["id"]},
        )
    )
    return tmp_path, gateway, row["id"]


def test_moves_files_and_rewrites_paths_without_changing_identity(workspace, caplog):
    project, gateway, identity = workspace
    with caplog.at_level("INFO"):
        backup = migration.migrate(project)
    row = migration.require(gateway.read_records("datamgr_datasets"))["records"][0]
    assert row["id"] == identity and row["source"] == "sq_futures"
    assert Path(row["path"]) == project / "data/market/futures/d1/@es"
    lineage = json.loads(row["lineage_json"])
    assert lineage["partitions"] == [str(Path(row["path"]) / "2024.parquet")]
    assert Path(lineage["nested"]["source_path"]) == Path("data/market/futures/d1/@es")
    assert lineage["note"] == "sq_futures"
    assert (
        Path(row["path"]) / "2024.parquet"
    ).read_bytes() == b"fixture-preserved-byte-for-byte"
    assert (backup / "sq_futures/d1/@es/2024.parquet").is_file()
    assert (backup / "haruquantai.db").is_file()
    assert (backup / "manifest.json").is_file()
    assert not (project / "data/market/sq_futures").exists()
    assert (project / "data/market/equity/sq_equity.csv").is_file()
    assert "migrated 2 folders" in caplog.text


def test_collision_never_overwrites_existing_destination(workspace):
    project, _, _ = workspace
    destination = project / "data/market/futures"
    destination.mkdir()
    with pytest.raises(FileExistsError):
        migration.migrate(project)
    assert (project / "data/market/sq_futures").is_dir()


def test_host_transaction_failure_rolls_back_folders_and_references(
    workspace, monkeypatch, caplog
):
    project, gateway, identity = workspace
    before = migration.require(gateway.read_records("datamgr_datasets"))["records"]
    monkeypatch.setattr(
        HostPersistence, "update_record", lambda *args, **kwargs: {"success": False}
    )
    with caplog.at_level("WARNING"), pytest.raises(RuntimeError):
        migration.migrate(project)
    assert (
        migration.require(gateway.read_records("datamgr_datasets"))["records"] == before
    )
    assert (project / "data/market/sq_futures/d1/@es/2024.parquet").is_file()
    assert not (project / "data/market/futures").exists()
    assert "rolled back directory moves" in caplog.text


def test_pending_publication_is_rejected_before_moves(workspace):
    project, _, _ = workspace
    (project / "data/market/sq_futures/.pending.publication.json").write_text("{}")
    with pytest.raises(ValueError, match="pending publications"):
        migration.migrate(project)
    assert (project / "data/market/sq_futures").exists()


def test_host_guard_refuses_running_host(monkeypatch):
    class Process:
        def __init__(self):
            self.info = {"cmdline": ["python", "-m", "app.main", "--reload"]}

    monkeypatch.setattr(migration.psutil, "process_iter", lambda *args: [Process()])
    with pytest.raises(RuntimeError, match="Stop the app host"):
        migration.ensure_offline()
