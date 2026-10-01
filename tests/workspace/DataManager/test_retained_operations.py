"""Retained source management and lossless exports without a running producer."""

import base64
import io
import json
import struct
import zipfile
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import MarketAccess
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.workspace.DataManager.operations import execute


def test_legacy_definition_round_trip_preserves_acquisition_storage(
    tmp_path: Path,
) -> None:
    from app.persistence.market import DefinitionRequest

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    provider = MarketAccess("plugin.data_manager.dukascopy", store)
    workspace = MarketAccess("workspace.data_manager", store)
    original = provider.register_definitions(
        (DefinitionRequest("EURUSD", "m1", postfix="_test", instrument="EURUSD"),)
    )[0]
    saved = workspace.export_definition(original.id)
    assert workspace.import_definition(saved) == original.id
    workspace.remove_source(original.id, clear_only=False)
    restored = workspace.import_definition(saved)
    assert workspace.retained_source(restored)["storage_backend"] == "market_files"
    assert provider.get_dataset(restored).symbol == "eurusd"


@pytest.mark.parametrize(
    "malformed", [{"symbol": ""}, {"owner": "unexpected"}, {"options": []}]
)
def test_transfer_validates_entire_batch_before_writing(
    tmp_path: Path, malformed: dict[str, object]
) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    workspace = MarketAccess(
        "workspace.data_manager", MarketDataStore(tmp_path, database)
    )
    valid = {
        "owner": "plugin.data_manager.yahoo",
        "source": "Yahoo",
        "symbol": "AAPL",
        "underlying": "AAPL",
        "instrument": "AAPL",
        "timeframe": "D1",
        "timezone": "UTC",
        "broker": "-1",
        "options": {},
    }
    with pytest.raises((ValueError, TypeError)):
        execute(
            workspace, "actions.load", {"definitions": [valid, {**valid, **malformed}]}
        )
    assert workspace.inventory() == ()


def test_export_clone_definition_transfer_and_clear(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    provider = MarketAccess("plugin.data_manager.yahoo", store)
    workspace = MarketAccess("workspace.data_manager", store)
    dataset_id = provider.register_source(
        source="Yahoo",
        symbol="AAPL",
        underlying="AAPL",
        instrument="AAPL",
        timeframe="D1",
        options={"parameters": {"symbol": "AAPL"}},
    )
    frame = pd.DataFrame(
        {
            "DateTime": pd.to_datetime(["2024-01-02T00:00:00Z"]),
            "Open": [1.123456789],
            "High": [2.0],
            "Low": [1.0],
            "Close": [1.5],
            "Volume": [12.75],
            "Adj Close": [1.25],
        }
    )
    provider.publish_source(
        dataset_id, "2024", pa.Table.from_pandas(frame, preserve_index=False)
    )
    csv = execute(workspace, "actions.export_to_csv", {"dataset_id": dataset_id})
    assert "1.123456789" in csv["content"]
    assert "12.75" in csv["content"]
    projected = execute(
        workspace,
        "actions.export_to_csv",
        {
            "dataset_id": dataset_id,
            "header": "<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>",
        },
    )
    assert len(projected["content"].splitlines()[0].split(",")) == 7
    assert "<ADJ CLOSE>" not in projected["content"]
    assert "<ADJ CLOSE>" in csv["content"]
    cloned = execute(
        workspace,
        "actions.clone_to_timezone",
        {"dataset_id": dataset_id, "shift_hours": 2, "postfix": "_two"},
    )
    assert cloned["bars"] == 1
    clone = next(row for row in workspace.inventory() if row["symbol"] == "AAPL_two")
    assert (
        workspace.read_source(clone["id"]).column("DateTime").to_pylist()[0].hour == 2
    )
    saved = json.loads(
        execute(workspace, "actions.save", {"dataset_ids": [dataset_id]})["content"]
    )
    assert saved["datasets"][0]["owner"] == "plugin.data_manager.yahoo"
    assert (
        execute(workspace, "actions.load", {"definitions": saved["datasets"]})[
            "loadedDatasets"
        ]
        == 1
    )
    execute(workspace, "actions.delete", {"dataset_ids": [dataset_id], "mode": "clear"})
    assert workspace.retained_source(dataset_id)["bars"] == 0
    assert list(tmp_path.rglob("*.parquet"))


def test_ambiguous_symbols_and_caller_paths_rejected(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    workspace = MarketAccess("workspace.data_manager", store)
    for owner in ("plugin.data_manager.yahoo", "plugin.data_manager.crypto"):
        MarketAccess(owner, store).register_source(
            source=owner,
            symbol="SAME",
            underlying="SAME",
            instrument="SAME",
            timeframe="M1",
        )
    with pytest.raises(ValueError, match="identity"):
        execute(workspace, "actions.export_to_csv", {"symbol": "SAME"})
    with pytest.raises(ValueError, match="filesystem"):
        execute(workspace, "actions.save", {"db_path": "untrusted.db"})


def test_atomic_row_edit_delete_and_stale_rejection(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    provider = MarketAccess("plugin.data_manager.yahoo", store)
    workspace = MarketAccess("workspace.data_manager", store)
    dataset_id = provider.register_source(
        source="Yahoo",
        symbol="EDIT",
        underlying="EDIT",
        instrument="EDIT",
        timeframe="D1",
    )
    frame = pd.DataFrame(
        {
            "DateTime": pd.to_datetime(
                ["2023-01-02T00:00:00Z", "2024-01-02T00:00:00Z"]
            ),
            "Open": [1.0, 1.0],
            "High": [2.0, 2.0],
            "Low": [1.0, 1.0],
            "Close": [1.5, 1.5],
            "Volume": [12.75, 12.75],
        }
    )
    for year, part in frame.groupby(frame["DateTime"].dt.year):
        provider.publish_source(
            dataset_id, str(year), pa.Table.from_pandas(part, preserve_index=False)
        )
    revisions = workspace.retained_revisions(dataset_id)
    edits = {
        "dataset_id": dataset_id,
        "expected_revisions": revisions,
        "changes": [
            {"timestamp": "2023-01-02T00:00:00Z", "delete": True},
            {"timestamp": "2024-01-02T00:00:00Z", "values": {"Close": 1.75}},
        ],
    }
    result = execute(workspace, "actions.save_data_changes", edits)
    assert result["bars"] == 1
    assert workspace.retained_source(dataset_id)["bars"] == 1
    assert workspace.read_source(dataset_id).column("Close").to_pylist() == [1.75]
    with pytest.raises(ValueError, match="changed"):
        workspace.replace_source(dataset_id, {}, expected_revisions=revisions)
    assert workspace.retained_source(dataset_id)["bars"] == 1
    current = workspace.retained_revisions(dataset_id)
    with pytest.raises(ValueError, match="OHLC"):
        execute(
            workspace,
            "actions.save_data_changes",
            {
                "dataset_id": dataset_id,
                "expected_revisions": current,
                "changes": [
                    {"timestamp": "2024-01-02T00:00:00Z", "values": {"Close": 3.0}}
                ],
            },
        )
    assert workspace.retained_revisions(dataset_id) == current


def test_mt4_binary_headers_and_tick_exports_preserve_actual_rows(
    tmp_path: Path,
) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    source = MarketAccess("plugin.data_manager.tick_downloader", store)
    workspace = MarketAccess("workspace.data_manager", store)
    identity = source.register_source(
        source="TickDownloader",
        symbol="EURUSD",
        underlying="EURUSD",
        instrument="EURUSD",
        timeframe="TICK",
    )
    ticks = pa.table(
        {
            "DateTime": pa.array(
                [1704067200123, 1704067220456], type=pa.timestamp("ms", tz="UTC")
            ),
            "Bid": [1234567, 1234568],
            "Ask": [1234577, 1234578],
            "Volume": [3, 5],
        }
    )
    source.publish_source(identity, "2024-01", ticks)
    result = execute(
        workspace,
        "actions.export_to_mt4",
        {"dataset_id": identity, "export_mode": "All", "timeframe": "M1"},
    )
    with zipfile.ZipFile(
        io.BytesIO(base64.b64decode(result["archive_base64"]))
    ) as archive:
        assert set(archive.namelist()) == {"EURUSD1.hst", "EURUSD1_0.fxt"}
        hst = archive.read("EURUSD1.hst")
        assert struct.unpack_from("<I", hst)[0] == 401
        assert len(hst) == 148 + 60
        candle = struct.unpack_from("<QddddQiQ", hst, 148)
        assert candle[1:5] == (1.234567, 1.234568, 1.234567, 1.234568)
        assert candle[5] == 8
        fxt = archive.read("EURUSD1_0.fxt")
        assert struct.unpack_from("<I", fxt)[0] == 405
        assert len(fxt) == 728 + 2 * 56
        assert struct.unpack_from("<QddddQii", fxt, 728)[1] == 1.234567
    mt5 = execute(
        workspace,
        "actions.export_to_mt5",
        {
            "dataset_id": identity,
            "spread_mode": "fixed",
            "spread_points": 10,
            "digits": 5,
        },
    )
    assert mt5["records"] == 2
    assert "1.234667" in mt5["content"]
    assert "00:00:00.123" in mt5["content"]
    csv = execute(
        workspace,
        "actions.export_to_csv",
        {"dataset_id": identity, "header": "date,time,bid,ask,volume"},
    )
    assert csv["content"].startswith("date,time,bid,ask,volume\n")
    with pytest.raises(ValueError, match="header"):
        execute(
            workspace,
            "actions.export_to_csv",
            {"dataset_id": identity, "header": "incorrect"},
        )
    for values, match in (
        ({"mt4_symbol": "../bad"}, "symbol"),
        ({"spread": -1}, "precision"),
        ({"export_mode": "bad"}, "mode"),
    ):
        with pytest.raises(ValueError, match=match):
            execute(
                workspace, "actions.export_to_mt4", {"dataset_id": identity, **values}
            )
