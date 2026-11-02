"""Isolated legacy adoption: exact prices, archive preservation and rollback."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from app.core.data.market_storage import M1_SCHEMA, TICK_SCHEMA, scan_catalog
from app.core.host.persistence import HostPersistence
from app.workspace.data_manager.data.coverage import missing_ranges
from app.workspace.data_manager.sources.dukascopy import Dukascopy

from scripts import adopt_legacy_dukascopy as adoption


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    project = tmp_path / "project"
    root = project / "data/market/dukascopy"
    root.mkdir(parents=True)
    (root / "dukascopy.csv").write_text(
        "EURUSD;EURUSD;Forex;Majors;1;1;5;100000;3;0.0001;0.00001;3\n"
    )
    work = tmp_path / "adoption"
    work.mkdir()
    date = datetime(2025, 1, 6, tzinfo=UTC)
    bars = pa.table(
        {
            "DateTime": pa.array(
                [date, date + timedelta(minutes=1)], pa.timestamp("us", tz="UTC")
            ),
            "Open": [1.1, 1.11],
            "High": [1.2, 1.2],
            "Low": [1.0, 1.0],
            "Close": [1.11, 1.12],
            "Volume": pa.array([10, 11], pa.uint64()),
        }
    ).replace_schema_metadata({b"tick_size": b"0.00001"})
    ticks = pa.table(
        {
            "DateTime": pa.array(
                [date + timedelta(seconds=n) for n in [1, 2, 3]],
                pa.timestamp("ms", tz="UTC"),
            ),
            "Ask": pa.array([1100010, 1100020, 1100030], pa.int64()),
            "Bid": pa.array([1100000, 1100010, 1100020], pa.int64()),
            "Volume": pa.array([101, 102, 103], pa.uint64()),
        }
    )
    for relative, table in [
        ("m1/eurusd/2025.parquet", bars),
        ("ticks/eurusd/2025/01-jan.parquet", ticks),
    ]:
        path = root / relative
        path.parent.mkdir(parents=True)
        pq.write_table(table, path)
    database = project / "data/database/haruquantai.db"
    database.parent.mkdir(parents=True)
    sqlite3.connect(database).close()
    gateway = HostPersistence(database)
    adoption.require(gateway.ensure_datasets_schema())
    monkeypatch.setattr(adoption, "ensure_offline", lambda: None)
    monkeypatch.setattr(adoption, "RESERVE", 0)
    return project, work, root, gateway


def test_full_adoption_preserves_prices_counts_sources_and_future_update_plan(
    legacy, caplog
):
    project, work, root, gateway = legacy
    originals = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*.parquet")
    }
    with caplog.at_level("INFO"):
        report = adoption.run(project, work, phase="audit")
        assert not report["failures"]
        adoption.run(project, work, phase="convert")
        rows = adoption.run(project, work, phase="publish")
    assert len(rows) == 2
    for row in rows:
        lineage = json.loads(row["lineage_json"])
        assert lineage["coverage_basis"] == "owner-accepted-legacy-file-spans"
        decoded = scan_catalog(row, decode=True).collect()
        assert decoded.height == row["bars"]
        raw = pq.read_schema(lineage["partitions"][0]).remove_metadata()
        assert raw.equals(M1_SCHEMA if row["timeframe"] == "M1" else TICK_SCHEMA)
        if row["timeframe"] == "TICK":
            assert decoded["Bid"].to_list() == [1.1, 1.10001, 1.10002]
            assert decoded["Flags"].null_count() == 3
            end = datetime.fromisoformat(row["date_to"])
            assert (
                missing_ranges(row, datetime.fromisoformat(row["date_from"]), end) == []
            )
            assert missing_ranges(row, end, end + timedelta(days=1))[0][
                0
            ] == end + timedelta(microseconds=1)
        else:
            assert decoded["Open"].to_list() == [1.1, 1.11]
    for relative, digest in originals.items():
        assert (
            hashlib.sha256((work / "original" / relative).read_bytes()).hexdigest()
            == digest
        )
    assert "registered 2 datasets" in caplog.text
    assert len(adoption.records(gateway)) == 2


def test_wrong_tick_scale_quarantines_tick_dataset(legacy):
    project, work, root, _ = legacy
    path = root / "ticks/eurusd/2025/01-jan.parquet"
    table = pq.ParquetFile(path).read()
    table = table.set_column(2, "Bid", pa.array([11000, 11001, 11002], pa.int64()))
    pq.write_table(table, path)
    report = adoption.run(project, work, phase="audit")
    assert len(report["failures"]) == 1
    assert "scale" in report["failures"][0]["error"]
    assert all(item["kind"] == "m1" for item in adoption.eligible(report))


def test_resume_skips_completed_verified_files(legacy, monkeypatch):
    project, work, _, _ = legacy
    adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    monkeypatch.setattr(
        adoption,
        "convert_file",
        lambda *args: pytest.fail("Completed file must not be converted again"),
    )
    assert len(adoption.run(project, work, phase="convert")) == 2


def test_input_change_is_rejected_before_conversion(legacy):
    project, work, root, _ = legacy
    report = adoption.run(project, work, phase="audit")
    item = report["items"][0]
    path = root / item["relative"]
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Source changed"):
        adoption.convert_file(path, work / "output.parquet", item)


def test_registration_failure_rolls_back_moves_and_database(
    legacy, monkeypatch, caplog
):
    project, work, root, gateway = legacy
    adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    monkeypatch.setattr(
        HostPersistence, "create_records", lambda *args: {"success": False}
    )
    with caplog.at_level("WARNING"), pytest.raises(RuntimeError):
        adoption.run(project, work, phase="publish")
    assert (root / "m1/eurusd/2025.parquet").is_file()
    assert pq.read_schema(root / "ticks/eurusd/2025/01-jan.parquet").names == [
        "DateTime",
        "Ask",
        "Bid",
        "Volume",
    ]
    assert not adoption.records(gateway)
    assert "rolled back publication" in caplog.text


def test_space_reserve_stops_before_conversion(legacy, monkeypatch):
    project, work, _, _ = legacy
    adoption.run(project, work, phase="audit")
    monkeypatch.setattr(adoption, "RESERVE", 10**30)
    with pytest.raises(RuntimeError, match="Insufficient"):
        adoption.run(project, work, phase="convert")
    assert not (work / "progress.json").exists()


def test_non_grid_prices_are_not_rounded_silently(legacy):
    project, work, root, _ = legacy
    item = adoption.run(project, work, phase="audit")["items"][0]
    batch = next(pq.ParquetFile(root / item["relative"]).iter_batches())
    changed = pa.Table.from_batches([batch]).set_column(
        1, "Open", pa.array([1.100001, 1.11])
    )
    with pytest.raises(ValueError, match="exactly"):
        adoption.canonical(changed.to_batches()[0], item)


def test_observed_file_spans_do_not_fill_missing_months(legacy):
    project, work, _, _ = legacy
    item = adoption.run(project, work, phase="audit")["items"][-1]
    other = {
        **item,
        "relative": "ticks/eurusd/2025/03-mar.parquet",
        "first": "2025-03-01T00:00:00+00:00",
        "last": "2025-03-10T00:00:00+00:00",
    }
    row = adoption.dataset_records(project, work, [item, other])[0]
    spans = json.loads(row["lineage_json"])["covered_ranges"]
    assert len(spans) == 2
    assert spans[0]["to"] < spans[1]["from"]


@pytest.mark.parametrize("timeframe", ["M1", "TICK"])
def test_adopted_partitions_accept_real_app_publication_without_redownload(
    legacy, timeframe
):
    project, work, root, gateway = legacy
    adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    adoption.run(project, work, phase="publish")
    service = Dukascopy(gateway, storage_root=root, catalog_path=root / "dukascopy.csv")
    frame = pd.DataFrame(
        {"Open": [1.12], "High": [1.13], "Low": [1.11], "Close": [1.12], "Volume": [10]}
        if timeframe == "M1"
        else {"Bid": [1.12], "Ask": [1.12001], "Flags": [3]},
        index=pd.to_datetime(
            ["2025-01-06T00:02:00Z" if timeframe == "M1" else "2025-01-06T00:00:04Z"]
        ),
    )
    response = service.download("EURUSD", timeframe=timeframe, data_frame=frame)
    assert response["success"], response.get("error")
    row = next(
        row for row in adoption.records(gateway) if row["timeframe"] == timeframe
    )
    assert row["bars"] == (3 if timeframe == "M1" else 4)
    data = scan_catalog(row, decode=True).collect()
    if timeframe == "TICK":
        assert data["Flags"].to_list() == [None, None, None, 3]


def test_dataset_collision_preserves_registered_records_and_source_files(legacy):
    project, work, root, gateway = legacy
    report = adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    row = adoption.dataset_records(project, work, report["items"])[0]
    adoption.require(gateway.create_records("datamgr_datasets", [row]))
    with pytest.raises(ValueError, match="collision"):
        adoption.run(project, work, phase="publish")
    assert len(adoption.records(gateway)) == 1
    assert not (work / "original").exists()


def test_work_directory_must_be_outside_checkout(legacy):
    project, _, _, _ = legacy
    with pytest.raises(ValueError, match="outside checkout"):
        adoption.run(project, project / "staging", phase="audit")


def test_tick_anchor_accounts_for_recorded_bar_rounding(legacy):
    project, work, root, _ = legacy
    catalog = root / "dukascopy.csv"
    catalog.write_text(catalog.read_text().replace("0.00001", "0.000001"))
    path = root / "m1/eurusd/2025.parquet"
    bars = pq.ParquetFile(path).read().set_column(3, "Low", pa.array([1.1, 1.1]))
    pq.write_table(bars.replace_schema_metadata({b"tick_size": b"0.01"}), path)
    path = root / "ticks/eurusd/2025/01-jan.parquet"
    ticks = (
        pq.ParquetFile(path)
        .read()
        .set_column(2, "Bid", pa.array([1099995, 1100010, 1100020], pa.int64()))
    )
    pq.write_table(ticks, path)
    assert not adoption.run(project, work, phase="audit")["failures"]


def test_volume_upgrade_verifies_every_value_and_removes_originals(legacy):
    project, work, root, gateway = legacy
    adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    adoption.run(project, work, phase="publish")
    path = root / "ticks/eurusd/2025/01-jan.parquet"
    table = pq.read_table(path).drop(["Volume"])
    pq.write_table(table, path)
    progress = adoption.load(work / "progress.json")
    progress[str(path.relative_to(root))]["fingerprint"] = adoption.fingerprint(path)
    adoption.save(work / "progress.json", progress)
    result = adoption.run(project, work, phase="preserve-volume")
    assert result == {"verified_files": 2, "rows": 5, "legacy_originals_removed": True}
    assert pq.read_table(path)["Volume"].to_pylist() == [101, 102, 103]
    assert pq.read_table(path)["Flags"].to_pylist() == [None, None, None]
    assert not (work / "original").exists()
    assert not list(root.rglob("*.volume-backup"))
    tick = next(row for row in adoption.records(gateway) if row["timeframe"] == "TICK")
    from app.workspace.data_manager.data.review import DatasetReview

    page = DatasetReview(gateway, tick["id"]).rows()
    assert [row["volume"] for row in page["rows"]] == [101, 102, 103]
    assert tick["schema_version"] == 3
    assert json.loads(tick["lineage_json"])["legacy_originals_removed"]
    assert adoption.run(project, work, phase="preserve-volume") == result


def test_volume_upgrade_refuses_changed_active_file_before_retiring(legacy):
    project, work, root, _ = legacy
    adoption.run(project, work, phase="audit")
    adoption.run(project, work, phase="convert")
    adoption.run(project, work, phase="publish")
    path = root / "ticks/eurusd/2025/01-jan.parquet"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="changed"):
        adoption.run(project, work, phase="preserve-volume")
    assert len(list((work / "original").rglob("*.parquet"))) == 2


def test_volume_alignment_failure_keeps_originals(legacy):
    _, _, root, _ = legacy
    path = root / "ticks/eurusd/2025/01-jan.parquet"
    original = next(pq.ParquetFile(path).iter_batches())
    raw = pa.Table.from_batches([original])
    active = pa.table(
        {
            "DateTime": raw["DateTime"].cast(pa.timestamp("us", tz="UTC")),
            "Bid": [1, 2, 3],
            "Ask": [2, 3, 4],
            "Flags": pa.array([None] * 3, pa.uint16()),
        }
    )
    reversed_raw = raw.take(pa.array([2, 1, 0]))
    with pytest.raises(ValueError, match="aligns"):
        adoption.with_volume(active.to_batches()[0], reversed_raw.to_batches()[0])
    assert path.exists()
