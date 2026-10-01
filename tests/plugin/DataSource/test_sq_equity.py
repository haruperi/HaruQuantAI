"""Equity DAT scaling and real catalog-to-archive publication in isolated custody."""

import asyncio
import io
import struct
import zipfile
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from app.host.capabilities import JobAccess, MarketAccess
from app.host.jobs import JobManager
from app.host.network import SourceNetwork
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.sq_equity import ORIGIN, Runtime, SQBinaryDatDecoder


def dat_file(version: Any = "4.2") -> Any:
    def utf(value: Any) -> Any:
        return struct.pack(">H", len(value)) + value.encode()

    return (
        utf(version)
        + utf("D")
        + utf("AAPL")
        + struct.pack(">qi", 1, 0)
        + utf("SnRbTs")
        + bytes(range(15))
        + struct.pack(">i", 0)
        + bytes([0xBA, 0xAA, 0xAA])
        + struct.pack(
            ">QIIIII", 1704067200000, 1250000, 1500000, 1000000, 1300000, 175000
        )
    )


@pytest.mark.parametrize(("version", "volume"), [("4.1", 1750), ("4.2", 1)])
def test_dat_version_scaling(version: Any, volume: Any) -> None:
    frame = SQBinaryDatDecoder.decode(dat_file(version))
    assert frame[["Open", "High", "Low", "Close", "Volume"]].values.tolist() == [
        [1.25, 1.5, 1.0, 1.3, volume]
    ]


def test_catalog_and_adjusted_archive_job(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("AAPL/2024.dat", dat_file())
        output.writestr("AAL/2024.dat", b"must not decode a different symbol")
    requests = []

    def response(request: Any) -> Any:
        requests.append((request.method, request.url.path))
        return httpx.Response(200, content=archive.getvalue())

    async def scenario() -> None:
        owner = "plugin.data_manager.sq_equity"
        jobs = JobManager(1, 1024**3)
        runtime = Runtime(
            MarketAccess(owner, store),
            JobAccess(owner, jobs),
            SourceNetwork(
                (ORIGIN,),
                client=httpx.AsyncClient(transport=httpx.MockTransport(response)),
            ),
        )
        lookup = cast(
            "Any",
            await runtime.invoke(
                "lookup", {"query": "AAPL.D", "exact": True, "search_name": False}
            ),
        )
        assert lookup["symbols"][0]["ticker"] == "AAPL.D"
        created = cast("Any", await runtime.invoke("add", {"symbol": "AAPL.D"}))
        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": created["id"],
                    "date_from": "2024-01-01",
                    "date_to": "2024-01-01",
                },
            ),
        )
        await asyncio.wait_for(jobs.tasks[started["job_id"]], 5)
        assert (
            cast(
                "Any",
                await runtime.invoke("download.status", {"job_id": started["job_id"]}),
            )
        )["state"] == "succeeded"
        await runtime.close()
        assert store.read_source(created["id"]).column("Close").to_pylist() == [1.3]
        await jobs.close()

    asyncio.run(scenario())
    assert ("GET", "/data/barchart/eod/adjusted_AA/data.zip") in requests


def test_resample_preserves_volume_and_canonical_duplicate_precedence() -> None:
    import pandas as pd  # type: ignore[import-untyped]
    from app.plugin.DataSource.sq_equity import (
        dataframe_to_canonical_table,
        resample_candles,
    )

    frame = pd.DataFrame(
        {
            "DateTime": pd.to_datetime(
                ["2024-01-01T00:00:00Z", "2024-01-01T00:01:00Z", "2024-01-01T00:02:00Z"]
            ),
            "Open": [2.0, 1.0, 4.0],
            "High": [3.0, 5.0, 4.0],
            "Low": [1.0, 0.5, 4.0],
            "Close": [1.0, 4.0, 4.0],
            "Volume": [2, 3, 7],
            "OpenInterest": [10, 20, 30],
        }
    )
    coarse = resample_candles(frame, "M5")
    assert coarse[["Open", "High", "Low", "Close", "Volume"]].values.tolist() == [
        [2, 5, 0.5, 4, 12]
    ]
    duplicated = pd.concat([frame, frame.iloc[[0]].assign(Close=2.5)])
    table = dataframe_to_canonical_table(duplicated)
    assert table.num_rows == 3
    assert table.column("Close").to_pylist() == [2.5, 4.0, 4.0]
    indexed = dataframe_to_canonical_table(frame.set_index("DateTime"))
    assert indexed.num_rows == 3
    assert (
        dataframe_to_canonical_table(
            frame.rename(columns={"DateTime": "datetime"}), "m1"
        ).num_rows
        == 3
    )
    assert resample_candles(frame.iloc[:0], "M5").empty
    with pytest.raises(ValueError, match="Unsupported"):
        resample_candles(frame, "bad")
    with pytest.raises(KeyError, match="missing"):
        dataframe_to_canonical_table(frame.drop(columns="DateTime"))
