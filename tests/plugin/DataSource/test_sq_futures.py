"""Futures source Open Interest semantics and actual snapshot lookup."""

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
from app.plugin.DataSource.sq_futures import (
    ORIGIN,
    Runtime,
    Search,
    SQFuturesDatDecoder,
    dataframe_to_canonical_table,
)


def test_open_interest_preserved_in_daily_schema() -> None:
    def utf(value: Any) -> Any:
        return struct.pack(">H", len(value)) + value.encode()

    raw = (
        utf("4.2")
        + utf("D")
        + utf("ES")
        + struct.pack(">qi", 1, 0)
        + utf("SnRbTs")
        + bytes(range(15))
        + struct.pack(">i", 0)
        + bytes([0xBA, 0xAA, 0xAA, 0xA0])
        + struct.pack(
            ">QIIIIII",
            1704067200000,
            1250000,
            1500000,
            1000000,
            1300000,
            175000,
            975000,
        )
    )
    frame = SQFuturesDatDecoder.decode(raw)
    assert frame["OpenInterest"].tolist() == [9]
    assert dataframe_to_canonical_table(frame, "d1").column(
        "OpenInterest"
    ).to_pylist() == [9]
    assert "OpenInterest" not in dataframe_to_canonical_table(frame, "m1").column_names


def test_actual_catalog_and_owner_definition(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    async def scenario() -> None:
        owner = "plugin.data_manager.sq_futures"
        jobs = JobManager(1, 1024**3)
        runtime = Runtime(
            MarketAccess(owner, store), JobAccess(owner, jobs), SourceNetwork((ORIGIN,))
        )
        result = cast(
            "Any",
            await runtime.invoke(
                "lookup", {"query": "ES", "continuous_only": True, "search_name": False}
            ),
        )
        assert result["symbols"]
        assert all(row["ticker"].startswith("@") for row in result["symbols"])
        chosen = result["symbols"][0]
        created = cast(
            "Any",
            await runtime.invoke(
                "add",
                {
                    "symbol": chosen["ticker"],
                    "timeframe": "D1" if chosen["timeframe"] == "D" else "M1",
                },
            ),
        )
        assert store.retained_source(created["id"])["owner"] == owner
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())


def test_futures_archive_routing_publication_and_denied_auth(tmp_path: Path) -> None:
    def utf(value: str) -> bytes:
        return struct.pack(">H", len(value)) + value.encode()

    raw = (
        utf("4.2")
        + utf("D")
        + utf("ES")
        + struct.pack(">qi", 1, 0)
        + utf("SnRbTs")
        + bytes(range(15))
        + struct.pack(">i", 0)
        + bytes([0xBA, 0xAA, 0xAA, 0xA0])
        + struct.pack(
            ">QIIIIII",
            1704067200000,
            1250000,
            1500000,
            1000000,
            1300000,
            175000,
            975000,
        )
    )
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("2024.dat", raw)
        output.writestr("2010.dat", b"out of range must not decode")
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    denied = False
    calls: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(
            401 if denied else 200,
            content=archive.getvalue() if request.method == "GET" else b"",
        )

    async def scenario() -> None:
        nonlocal denied
        owner = "plugin.data_manager.sq_futures"
        jobs = JobManager(1, 1024**3)
        runtime = Runtime(
            MarketAccess(owner, store),
            JobAccess(owner, jobs),
            SourceNetwork(
                (ORIGIN,),
                client=httpx.AsyncClient(transport=httpx.MockTransport(response)),
            ),
        )
        symbols = runtime.lookup(
            Search(query="ES", continuous_only=True, search_name=False)
        )
        chosen = next(row for row in symbols if row["timeframe"] == "D")
        created = cast(
            "Any",
            await runtime.invoke(
                "add", {"symbol": chosen["ticker"], "timeframe": "D1"}
            ),
        )
        await runtime.invoke(
            "credentials.configure",
            {
                "username": "test-user",
                "password": "test-only",  # pragma: allowlist secret -- dummy fixture.
            },
        )
        catalog = cast("Any", await runtime.invoke("catalog", {}))
        assert catalog["credentials_configured"] is True
        for missing in (True, False):
            started = cast(
                "Any",
                await runtime.invoke(
                    "download.start",
                    {
                        "dataset_id": created["id"],
                        "date_from": "2024-01-01",
                        "date_to": "2024-01-01",
                        "only_missing": missing,
                    },
                ),
            )
            await asyncio.wait_for(jobs.tasks[started["job_id"]], 5)
            status = cast(
                "Any",
                await runtime.invoke("download.status", {"job_id": started["job_id"]}),
            )
            assert status["state"] == "succeeded"
        assert store.read_source(created["id"]).column("OpenInterest").to_pylist() == [
            9
        ]
        assert store.retained_source(created["id"])["bars"] == 1
        denied = True
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
        )["state"] == "failed"
        assert store.retained_source(created["id"])["bars"] == 1
        with pytest.raises(ValueError, match="Unknown"):
            await runtime.invoke("unsupported", {})
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())
    assert any(path.endswith("/data01.zip") for path in calls)


def test_resample_preserves_volume_and_canonical_duplicate_precedence() -> None:
    import pandas as pd  # type: ignore[import-untyped]
    from app.plugin.DataSource.sq_futures import (
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
    assert coarse["OpenInterest"].tolist() == [30]
    assert dataframe_to_canonical_table(frame.drop(columns="OpenInterest")).column(
        "OpenInterest"
    ).to_pylist() == [0, 0, 0]
