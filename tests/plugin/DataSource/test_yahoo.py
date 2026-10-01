"""Real source-runtime tests using bounded recorded-format HTTP documents."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import pandas as pd  # type: ignore[import-untyped]
import pytest
from app.host.capabilities import JobAccess, MarketAccess
from app.host.jobs import JobManager
from app.host.network import SourceNetwork
from app.persistence.market import MarketDataStore, create_isolated_schema
from app.plugin.DataSource.yahoo import (
    YahooDefinition,
    YahooRuntime,
    YahooSession,
    _generate_date_chunks,
    normalize_timeframe,
    parse_chart,
    parse_date_param,
    resample_to_timeframe,
)


def chart_document() -> Any:
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": "AAPL",
                        "priceHint": 2,
                        "shortName": "Apple",
                        "exchangeName": "NASDAQ",
                    },
                    "timestamp": [1704182400, 1704268800, 1704355200],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.123, 11, None],
                                "high": [12, 13, None],
                                "low": [9, 10, None],
                                "close": [11.123, 12, None],
                                "volume": [101, None, 3],
                            }
                        ],
                        "adjclose": [{"adjclose": [10.456, None, 9]}],
                    },
                }
            ],
            "error": None,
        }
    }


def test_chart_nulls_adjustment_and_script_timeframes() -> None:
    frame = parse_chart(chart_document(), "AAPL")
    assert len(frame) == 2
    assert frame["Volume"].tolist() == [101.0, 0.0]
    assert frame["Adj Close"].tolist() == [10.456, 12.0]
    assert str(frame.index.tz) == "UTC"
    assert normalize_timeframe("H4") == ("1h", "4h")
    assert normalize_timeframe("M10") == ("5m", "10min")
    assert normalize_timeframe("D1") == ("1d", None)
    with pytest.raises(ValueError):
        YahooDefinition(symbol="AAPL", timeframe="H0")
    with pytest.raises(ValueError):
        parse_chart({"chart": {"result": None}}, "missing")
    assert parse_date_param("2024-01-01", True).hour == 23
    chunks = _generate_date_chunks(
        parse_date_param("2024-01-01"), parse_date_param("2024-01-10"), "1m"
    )
    assert len(chunks) == 2
    assert (chunks[1][0] - chunks[0][1]).total_seconds() == 1


def test_resample_preserves_script_ohlcv_and_adjusted_close() -> None:
    frame = pd.DataFrame(
        {
            "Open": [1.0, 2.0],
            "High": [3.0, 5.0],
            "Low": [0.0, 1.0],
            "Close": [2.0, 4.0],
            "Volume": [10.0, 20.0],
            "Adj Close": [1.5, 3.5],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="h", tz="UTC"),
    )
    result = resample_to_timeframe(frame, "H2")
    assert result.iloc[0].to_dict() == {
        "Open": 1.0,
        "High": 5.0,
        "Low": 0.0,
        "Close": 4.0,
        "Volume": 30.0,
        "Adj Close": 3.5,
    }


def test_job_download_commits_and_survives_producer_close(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    requested = []

    def transport(request: Any) -> Any:
        requested.append(request.url.path)
        if request.url.host == "fc.yahoo.com":
            return httpx.Response(404)
        if request.url.path.endswith("getcrumb"):
            return httpx.Response(200, text="test-crumb")
        return httpx.Response(200, json=chart_document())

    async def scenario() -> None:
        jobs = JobManager(1, 512 * 1024 * 1024)
        network = SourceNetwork(
            (
                "https://fc.yahoo.com",
                "https://query1.finance.yahoo.com",
                "https://query2.finance.yahoo.com",
            ),
            client=httpx.AsyncClient(transport=httpx.MockTransport(transport)),
        )
        owner = "plugin.data_manager.yahoo"
        runtime = YahooRuntime(
            MarketAccess(owner, store), JobAccess(owner, jobs), YahooSession(network)
        )
        created = cast("Any", await runtime.invoke("add", {"symbol": "AAPL"}))
        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": created["id"],
                    "date_from": "2024-01-01",
                    "date_to": "2024-01-05",
                },
            ),
        )
        await asyncio.wait_for(jobs.tasks[started["job_id"]], timeout=3)
        status = cast(
            "Any",
            await runtime.invoke("download.status", {"job_id": started["job_id"]}),
        )
        assert status["state"] == "succeeded"
        assert status["rows"] == 2
        assert status["published_partitions"] == 1
        records = store.source_partitions(created["id"])
        await runtime.close()
        await jobs.close()
        table = store.read_source_partition(records[0])
        assert table.column("Close").to_pylist() == [11.12, 12.0]
        assert table.column("Adj Close").to_pylist() == [10.46, 12.0]
        assert table.column("DateTime").to_pylist()[0] == datetime.fromtimestamp(
            1704182400, tz=UTC
        )
        assert store.source_definition(owner, created["id"])["bars"] == 2
        assert requested.count("/v1/test/getcrumb") == 1

    asyncio.run(scenario())
