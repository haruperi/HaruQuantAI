"""Tests for Data Manager Actions."""

from __future__ import annotations

import asyncio
import sqlite3
import struct
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import HostCapabilities, ResourceAccess
from app.persistence.market import (
    M1_SCHEMA,
    TICK_SCHEMA,
    MarketDataStore,
    create_isolated_schema,
    preseed_native_sqx_datasets,
)
from app.persistence.resources import ResourceStore
from app.workspace.DataManager.actions import (
    broker_data,
    broker_data_update,
    clone_to_timezone,
    delete_datasets,
    export_to_csv,
    export_to_mt4,
    export_to_mt5,
    list_datasets,
    load_definitions,
    review_chart,
    review_data,
    review_quality,
    save_data_changes,
    save_definitions,
    update_all,
    update_selected,
)
from app.workspace.DataManager.workspace import prepare


@pytest.fixture
def test_env(tmp_path: Path) -> tuple[Path, Path]:
    """Fixture providing initialized database and market directory."""
    db_path = tmp_path / "haruquantai.db"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)

    create_isolated_schema(db_path)
    csv_path = Path("data/market/dukascopy/dukascopy.csv")
    preseed_native_sqx_datasets(db_path, csv_path if csv_path.is_file() else None)

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_broker ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, "
            "server_timezone TEXT DEFAULT 'UTC', postfix TEXT DEFAULT '', enabled INTEGER DEFAULT 1, mt_use INTEGER DEFAULT 1)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO datamgr_broker (id, name, server_timezone, postfix, enabled, mt_use) "
            "VALUES (1, 'Dukascopy', 'UTC', '_dukascopy', 1, 1)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_instruments ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL UNIQUE, "
            "description TEXT DEFAULT '', broker_id INTEGER DEFAULT 1, "
            "point_value REAL DEFAULT 100000.0, tick_size REAL DEFAULT 0.00001, "
            "tick_step REAL DEFAULT 0.00001, default_spread REAL DEFAULT 0.0001, "
            "default_slippage REAL DEFAULT 0.0, margin_rate REAL DEFAULT 0.05, "
            "data_type TEXT DEFAULT 'Forex', decimals INTEGER DEFAULT 5)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO datamgr_instruments (id, symbol, description, broker_id, point_value, default_spread) "
            "VALUES (1, 'EURUSD', 'Euro / US Dollar', 1, 100000.0, 0.0001)"
        )
        conn.commit()

    store = MarketDataStore(data_root, db_path)

    # Publish sample M1 data for EURUSD
    times = [datetime(2026, 3, 2, 10, i, 0, tzinfo=UTC) for i in range(15)]  # Monday
    table = pa.Table.from_pylist(
        [
            {
                "DateTime": dt,
                "Open": 1.0850 + i * 0.0001,
                "High": 1.0860 + i * 0.0001,
                "Low": 1.0845 + i * 0.0001,
                "Close": 1.0855 + i * 0.0001,
                "Volume": 100 + i * 10,
            }
            for i, dt in enumerate(times)
        ],
        schema=M1_SCHEMA,
    )
    first_ms = int(times[0].timestamp() * 1000)
    last_ms = int(times[-1].timestamp() * 1000)
    store.publish(
        source="dukascopy",
        kind="m1",
        symbol="eurusd",
        period="2026",
        table=table,
        coverage=((first_ms, last_ms),),
        provider_mode="test",
    )

    # Publish sample Tick data for GBPUSD
    tick_times = [datetime(2026, 3, 2, 10, 0, i, tzinfo=UTC) for i in range(10)]
    tick_table = pa.Table.from_pylist(
        [
            {
                "DateTime": dt,
                "Ask": 125050 + i * 10,
                "Bid": 125030 + i * 10,
                "Volume": 5 + i,
            }
            for i, dt in enumerate(tick_times)
        ],
        schema=TICK_SCHEMA,
    )
    t_first = int(tick_times[0].timestamp() * 1000)
    t_last = int(tick_times[-1].timestamp() * 1000)
    store.publish(
        source="dukascopy",
        kind="ticks",
        symbol="gbpusd",
        period="2026-03",
        table=tick_table,
        coverage=((t_first, t_last),),
        provider_mode="test",
    )

    return db_path, data_root


def test_broker_data_and_update(test_env: tuple[Path, Path]) -> None:
    db_path, _ = test_env
    data = broker_data(db_path, query="EUR")
    assert len(data) > 0
    assert data[0]["symbol"].startswith("EUR")
    assert "pointValue" in data[0]

    update_res = broker_data_update(db_path)
    assert update_res["success"] is True


def test_clone_to_timezone_and_weekend_filter(
    test_env: tuple[Path, Path],
) -> None:
    db_path, data_root = test_env

    # Clone EURUSD with +2h shift
    results = clone_to_timezone(
        db_path,
        data_root,
        ["EURUSD_dukascopy"],
        shift_hours=2,
        timezone_name="UTC+2",
        remove_weekends=True,
    )
    assert len(results) == 1
    assert "EURUSD_dukascopy_M1_+2h" in results[0]["symbol"]
    assert results[0]["records"] == 15

    # Cloning already cloned data should fail closed
    with pytest.raises(ValueError, match="is cloned data"):
        clone_to_timezone(
            db_path,
            data_root,
            [results[0]["symbol"]],
            shift_hours=1,
        )


def test_delete_datasets_with_cloned_dependency(
    test_env: tuple[Path, Path],
) -> None:
    db_path, data_root = test_env

    # Clone first to establish dependency
    clone_to_timezone(
        db_path,
        data_root,
        ["EURUSD_dukascopy"],
        shift_hours=3,
        timezone_name="UTC+3",
    )

    # Deleting source EURUSD_dukascopy must fail because cloned data depends on it
    with pytest.raises(ValueError, match="used as source for cloned data"):
        delete_datasets(db_path, data_root, ["EURUSD_dukascopy"])

    # Clear mode on an un-dependent symbol works
    res = delete_datasets(db_path, data_root, ["GBPUSD_dukascopy"], mode="clear")
    assert res["success"] is True
    assert res["affected"] == 1
    assert res["deletedCount"] == 1
    assert res["deleted"] == ["GBPUSD_dukascopy"]
    with closing(sqlite3.connect(db_path)) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM datamgr_datasets WHERE symbol=?",
                ("GBPUSD_dukascopy",),
            ).fetchone()[0]
            == 1
        )


def test_delete_datasets_removes_catalog_row(test_env: tuple[Path, Path]) -> None:
    """Removing a dataset deletes its definition and reports the removed symbol."""
    db_path, data_root = test_env

    with closing(sqlite3.connect(db_path)) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM datamgr_datasets WHERE symbol=?",
                ("GBPUSD_dukascopy",),
            ).fetchone()[0]
            == 1
        )

    result = delete_datasets(db_path, data_root, ["GBPUSD_dukascopy"])

    assert result["success"] is True
    assert result["mode"] == "remove"
    assert result["affected"] == 1
    assert result["deletedCount"] == 1
    assert result["deleted"] == ["GBPUSD_dukascopy"]
    with closing(sqlite3.connect(db_path)) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM datamgr_datasets WHERE symbol=?",
                ("GBPUSD_dukascopy",),
            ).fetchone()[0]
            == 0
        )


def test_export_to_csv_and_resampling(
    test_env: tuple[Path, Path], tmp_path: Path
) -> None:
    db_path, data_root = test_env
    out_csv = tmp_path / "eurusd_m5.csv"

    # Export M1 source resampled to M5
    res = export_to_csv(
        db_path,
        data_root,
        "EURUSD_dukascopy",
        timeframe="M5",
        output_path=out_csv,
        target_timezone="+2h",
    )
    assert res["success"] is True
    assert out_csv.is_file()

    content = out_csv.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert lines[0] == "<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>"
    # 15 minutes of M1 bars should resample into 3 M5 bars
    assert len(lines) == 4


def test_export_to_mt4_hst_and_fxt(test_env: tuple[Path, Path], tmp_path: Path) -> None:
    db_path, data_root = test_env
    out_dir = tmp_path / "mt4_out"

    res = export_to_mt4(
        db_path,
        data_root,
        "EURUSD_dukascopy",
        mt4_symbol="EURUSD",
        output_dir=out_dir,
        timeframe="M1",
        export_mode="All",
    )
    assert res["success"] is True
    assert len(res["files"]) == 2  # EURUSD1.hst and EURUSD1_0.fxt

    hst_file = out_dir / "EURUSD1.hst"
    assert hst_file.is_file()
    # 148 bytes header + 15 bars * 64 bytes = 1108 bytes
    assert hst_file.stat().st_size == 148 + 15 * 64

    with hst_file.open("rb") as f:
        version, copyright_bytes, sym = struct.unpack("<I64s12s", f.read(80))
        assert version == 401
        assert b"MetaQuotes" in copyright_bytes
        assert sym.startswith(b"EURUSD")

    fxt_file = out_dir / "EURUSD1_0.fxt"
    assert fxt_file.is_file()
    # 728 bytes header + 15 test bars * 56 bytes = 1568 bytes
    assert fxt_file.stat().st_size == 728 + 15 * 56


def test_export_to_mt5(test_env: tuple[Path, Path], tmp_path: Path) -> None:
    db_path, data_root = test_env
    out_mt5 = tmp_path / "eurusd_mt5.txt"

    res = export_to_mt5(
        db_path,
        data_root,
        "EURUSD_dukascopy",
        timeframe="M1",
        output_path=out_mt5,
    )
    assert res["success"] is True
    assert out_mt5.is_file()

    content = out_mt5.read_text(encoding="utf-8")
    assert "<DATE>\t<TIME>\t<OPEN>" in content

    # Test tick export for GBPUSD
    tick_out = tmp_path / "gbpusd_ticks.txt"
    res_tick = export_to_mt5(
        db_path,
        data_root,
        "GBPUSD_dukascopy",
        timeframe="TICK",
        output_path=tick_out,
    )
    assert res_tick["success"] is True
    assert "<DATE>\t<TIME>\t<BID>\t<ASK>" in tick_out.read_text(encoding="utf-8")


def test_save_and_load_definitions(test_env: tuple[Path, Path], tmp_path: Path) -> None:
    db_path, data_root = test_env
    backup_file = tmp_path / "definitions_backup.json"

    save_res = save_definitions(db_path, data_root, file_path=backup_file)
    assert save_res["success"] is True
    assert backup_file.is_file()

    load_res = load_definitions(db_path, data_root, file_path=backup_file)
    assert load_res["success"] is True
    assert load_res["loadedDatasets"] > 0


def test_review_actions(test_env: tuple[Path, Path]) -> None:
    db_path, data_root = test_env

    # 1. review_data
    r_data = review_data(
        db_path, data_root, "EURUSD_dukascopy", timeframe="M1", limit=5
    )
    assert r_data["totalRecords"] == 15
    assert len(r_data["rows"]) == 5

    # 2. review_chart
    r_chart = review_chart(db_path, data_root, "EURUSD_dukascopy", timeframe="M1")
    assert len(r_chart["chart"]) == 15

    # 3. review_quality
    r_qual = review_quality(db_path, data_root, "EURUSD_dukascopy", timeframe="M1")
    assert r_qual["totalBars"] == 15
    assert r_qual["qualityScore"] >= 90.0

    # 4. save_data_changes
    r_save = save_data_changes(
        db_path,
        data_root,
        "EURUSD_dukascopy",
        timeframe="M1",
        session="Default",
        changes={},
    )
    assert r_save["success"] is True


def test_update_all_and_selected(test_env: tuple[Path, Path]) -> None:
    db_path, data_root = test_env

    all_res = update_all(db_path, data_root, provider="dukascopy")
    assert all_res["success"] is True
    assert all_res["totalEligible"] > 0

    sel_res = update_selected(
        db_path, data_root, ["EURUSD_dukascopy"], provider="dukascopy"
    )
    assert sel_res["success"] is True
    assert sel_res["queuedUpdates"] == 1


def test_workspace_actions_dispatch(
    test_env: tuple[Path, Path], tmp_path: Path
) -> None:
    db_path, data_root = test_env
    store = ResourceStore(tmp_path / "resources")

    async def run() -> None:
        context = HostCapabilities(
            ResourceAccess("workspace.data_manager", "1.0.0", store), None, None
        )
        owner = await prepare(context)

        # Broker data operation
        b_data = await owner.invoke(
            "actions.broker_data",
            {"query": "EUR", "db_path": str(db_path), "data_root": str(data_root)},
        )
        assert isinstance(b_data, list)

        # Review quality operation
        qual = await owner.invoke(
            "actions.review_quality",
            {
                "symbol": "EURUSD_dukascopy",
                "timeframe": "M1",
                "db_path": str(db_path),
                "data_root": str(data_root),
            },
        )
        assert isinstance(qual, dict)
        assert "qualityScore" in qual

        # Update all operation
        up_all = await owner.invoke(
            "actions.update_all",
            {"db_path": str(db_path), "data_root": str(data_root)},
        )
        assert isinstance(up_all, dict)
        assert up_all["success"] is True

        # List datasets operation
        all_ds = await owner.invoke(
            "actions.list_datasets",
            {"db_path": str(db_path), "data_root": str(data_root)},
        )
        assert isinstance(all_ds, list)
        assert len(all_ds) > 0

        await owner.close()

    asyncio.run(run())


def test_list_datasets(test_env: tuple[Path, Path]) -> None:
    """Test listing datasets returns structured records from datamgr_datasets."""
    db_path, data_root = test_env
    rows = list_datasets(db_path, data_root)
    assert isinstance(rows, list)
    assert len(rows) > 0

    first = rows[0]
    assert "id" in first
    assert "symbol" in first
    assert "underlying" in first
    assert "instrument" in first
    assert "timeframe" in first
    assert "broker" in first
    assert "brokerName" in first
    assert "timezone" in first
    assert "category" in first
    assert "from" in first
    assert "to" in first
    assert "bars" in first
    assert "quality" in first
    assert "status" in first
    assert first["status"] == "Ready"
