"""Source binary/log formats and actual archive job publication."""

import asyncio
import base64
import io
import struct
import zipfile
from pathlib import Path
from typing import Any, cast

import httpx
from app.host.capabilities import JobAccess, MarketAccess
from app.host.jobs import JobManager
from app.host.network import SourceNetwork
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.darwinex import (
    DarwinexFileImporter,
    DarwinexRuntime,
    SQBinaryDatDecoder,
)


def dat_file() -> Any:
    def utf(text: Any) -> Any:
        encoded = text.encode()
        return struct.pack(">H", len(encoded)) + encoded

    return (
        utf("4.2")
        + utf("D")
        + utf("EURUSD")
        + struct.pack(">qi", 1, 0)
        + utf("SnRbTs")
        + bytes(range(15))
        + struct.pack(">i", 0)
        + bytes([0xBA, 0xAA])
        + struct.pack(">QIII", 1704067200123, 1200000, 1100000, 175000)
    )


def test_dat_absolute_fields_and_fixed_units() -> None:
    result = SQBinaryDatDecoder.decode(dat_file())
    assert [column.tolist() for column in result] == [
        [1704067200123],
        [1200000],
        [1100000],
        [175000],
    ]


def test_log_pair_carry_and_volume_scaling() -> None:
    ask = b"1704067200123,1.2,90\n1704067200125,1.3,99\n"
    bid = b"1704067200124,1.1,1.75\n"
    times, asks, bids, volumes, state = DarwinexFileImporter.merge_ask_bid_files(
        ask, bid
    )
    assert times.tolist() == [1704067200123, 1704067200124, 1704067200125]
    assert asks.tolist() == [1200000, 1200000, 1300000]
    assert bids.tolist() == [0, 1100000, 1100000]
    assert volumes.tolist() == [0, 175000, 175000]
    assert state == {"last_ask": 1.3, "last_bid": 1.1, "last_vol": 1.75}


def test_download_job_reads_archive_and_retains_after_close(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("2024_01_01.dat", dat_file())

    def response(request: Any) -> Any:
        if request.url.path.endswith("metadata.dat"):
            return httpx.Response(200, text="2024.zip;")
        return httpx.Response(200, content=content.getvalue())

    async def scenario() -> None:
        owner = "plugin.data_manager.darwinex"
        jobs = JobManager(1, 1024 * 1024 * 1024)
        network = SourceNetwork(
            ("https://cdn.strategyquantcdn.com", "https://cdn005.strategyquantcdn.com"),
            client=httpx.AsyncClient(transport=httpx.MockTransport(response)),
        )
        runtime = DarwinexRuntime(
            MarketAccess(owner, store), JobAccess(owner, jobs), network
        )
        created = cast("Any", await runtime.invoke("add", {"symbol": "EURUSD"}))
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
        await asyncio.wait_for(jobs.tasks[started["job_id"]], timeout=3)
        status = cast(
            "Any",
            await runtime.invoke("download.status", {"job_id": started["job_id"]}),
        )
        assert status["state"] == "succeeded"
        assert status["rows"] == 1
        await runtime.close()
        partition = store.source_partitions(created["id"])[0]
        assert store.read_source_partition(partition).column("Volume").to_pylist() == [
            175000
        ]
        await jobs.close()

    asyncio.run(scenario())


def test_import_aggregates_consecutive_days_before_weekly_resampling(
    tmp_path: Path,
) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)

    async def scenario() -> None:
        owner = "plugin.data_manager.darwinex"
        jobs = JobManager(1, 1024**3)
        network = SourceNetwork(("https://cdn.strategyquantcdn.com",))
        runtime = DarwinexRuntime(
            MarketAccess(owner, MarketDataStore(tmp_path, database)),
            JobAccess(owner, jobs),
            network,
        )
        created = cast(
            "Any", await runtime.invoke("add", {"symbol": "EURUSD", "timeframe": "W1"})
        )
        pairs = [
            {
                "ask_base64": base64.b64encode(f"{stamp},1.3,0\n".encode()).decode(),
                "bid_base64": base64.b64encode(
                    f"{stamp},{bid},1.75\n".encode()
                ).decode(),
            }
            for stamp, bid in [(1704153600123, 1.1), (1704240000123, 1.2)]
        ]
        started = cast(
            "Any",
            await runtime.invoke(
                "import.start",
                {"dataset_id": created["id"], "pairs": cast("Any", pairs)},
            ),
        )
        await jobs.tasks[started["job_id"]]
        assert runtime.jobs.status(started["job_id"]).state == "succeeded"
        table = runtime.market.read_source_partition(created["id"], "2024")
        assert table.num_rows == 1
        assert table.column("Open").to_pylist() == [1.1]
        assert table.column("Close").to_pylist() == [1.2]
        assert table.column("Volume").to_pylist() == [350000]
        await runtime.close()
        await jobs.close()

    asyncio.run(scenario())
