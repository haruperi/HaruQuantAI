"""BI5 numerical preservation, path interpretation and real job custody."""

import asyncio
import base64
import lzma
import struct
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from app.host.capabilities import JobAccess, MarketAccess
from app.host.jobs import JobManager
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.tick_downloader_import import (
    TickRuntime,
    _decompress_bi5,
    _read_tick_file,
    _ticks_to_m1,
    inspect_paths,
)


def binary(ask: Any = 123456, bid: Any = 123450) -> Any:
    return lzma.compress(
        struct.pack(">iiiff", 123, ask, bid, 0.125, 0.25), format=lzma.FORMAT_ALONE
    )


def test_hour_decoder_source_units_and_header_repair() -> None:
    encoded = binary()
    repaired = encoded[:5] + encoded[13:]
    assert _decompress_bi5(encoded) == _decompress_bi5(repaired)
    arrays = _read_tick_file(encoded, datetime(2024, 1, 1, tzinfo=UTC), 5)
    assert arrays is not None
    assert [item.tolist() for item in arrays] == [
        [1704067200123],
        [1.23456],
        [1.2345],
        [125000.0],
        [250000.0],
    ]
    bars = _ticks_to_m1(arrays[0], arrays[1], arrays[2], arrays[3], arrays[4])
    assert bars.iloc[0]["volume"] == 375000
    assert bars.iloc[0]["close"] == 1.2345
    with pytest.raises(ValueError, match="Corrupt"):
        _decompress_bi5(b"corrupt-bytes")


def test_logical_paths_use_catalog_precision_and_zero_based_months() -> None:
    rows = inspect_paths(
        ["TD/tickdata/EURUSD/2024/00/01/00h_ticks.bi5", "TD/readme.txt"]
    )
    assert rows[0]["hour"] == "2024-01-01T00:00:00+00:00"
    assert rows[0]["decimals"] == 5
    with pytest.raises(ValueError, match="relative path"):
        inspect_paths(["TD/../EURUSD/2024/00/01/00h_ticks.bi5"])


def test_import_job_incoming_precedence_and_retained_data(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    async def scenario() -> None:
        owner = "plugin.data_manager.tick_downloader"
        jobs = JobManager(1, 1024 * 1024 * 1024)
        runtime = TickRuntime(MarketAccess(owner, store), JobAccess(owner, jobs))
        request: dict[str, Any] = {
            "symbol": "EURUSD",
            "decimals": 5,
            "files": [
                {
                    "hour": "2024-01-01T00:00:00Z",
                    "content_base64": base64.b64encode(binary()).decode(),
                }
            ],
        }
        for ask in (123456, 123460):
            request["files"][0]["content_base64"] = base64.b64encode(
                binary(ask=ask)
            ).decode()
            started = cast("Any", await runtime.invoke("import.start", request))
            await asyncio.wait_for(jobs.tasks[started["job_id"]], timeout=3)
            status = cast(
                "Any",
                await runtime.invoke("import.status", {"job_id": started["job_id"]}),
            )
            assert status["state"] == "succeeded"
            assert status["rows"] == 1
        dataset_id = status["dataset_id"]
        await runtime.close()
        partition = store.source_partitions(dataset_id)[0]
        assert partition["revision"] == 2
        table = store.read_source_partition(partition)
        assert table.num_rows == 1
        assert table.column("Ask").to_pylist() == [1234600]
        assert table.column("Volume").to_pylist() == [375000]
        await jobs.close()

    asyncio.run(scenario())
