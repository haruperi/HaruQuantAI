"""Deterministic offline BI5 examples, with no provider request."""

import asyncio
import lzma
import sqlite3
import struct
from contextlib import closing
from datetime import UTC, datetime

import pytest
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    NetworkAccess,
)
from app.host.jobs import JobManager
from app.host.market_data import MarketDataset, MarketDataStore
from app.host.network import HistoricalNetwork, NetworkResult
from app.persistence.market import create_isolated_schema
from app.plugin.data_source.Dukascopy.dukascopy import (
    _fetch_day,
    decode_m1,
    decode_ticks,
    prepare,
    standard_url,
)


def test_hourly_tick_uses_both_side_volumes() -> None:
    """Two float32 side volumes become one integer base-currency value."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    payload = lzma.compress(
        struct.pack(">IIIff", 17, 110002, 110000, 0.01, 0.02),
        format=lzma.FORMAT_ALONE,
    )
    rows = decode_ticks(payload, instant, "EURUSD")
    assert rows == ((int(instant.timestamp() * 1000) + 17, 1100020, 1100000, 30000),)
    assert standard_url("EURUSD", instant, "ticks") == (
        "https://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/15/00h_ticks.bi5"
    )


def test_m1_bid_candle_field_order() -> None:
    """Day second offset, bid OHLC order and volume are explicit."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.05),
        format=lzma.FORMAT_ALONE,
    )
    rows = decode_m1(payload, instant, "EURUSD")
    assert rows == (
        (int(instant.timestamp() * 1000) + 60000, 1.1, 1.1002, 1.0999, 1.1001, 50000),
    )


def test_corrupt_and_fractional_volume_fail() -> None:
    """Malformed records and non-integral unit amounts cannot be published."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    with pytest.raises(ValueError):
        decode_ticks(b"not bi5", instant, "EURUSD")
    payload = lzma.compress(
        struct.pack(">IIIff", 0, 110002, 110000, 0.0000015, 0.0),
        format=lzma.FORMAT_ALONE,
    )
    with pytest.raises(ValueError):
        decode_ticks(payload, instant, "EURUSD")
    with pytest.raises(ValueError, match="supported FX"):
        standard_url("XAUUSD", instant, "ticks")


def test_missing_tick_hour_cannot_claim_day_coverage() -> None:
    """A mixed 200/404 hourly day is incomplete and cannot be published."""
    payload = lzma.compress(
        struct.pack(">IIIff", 0, 110002, 110000, 0.01, 0.02),
        format=lzma.FORMAT_ALONE,
    )

    class PartialNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            return NetworkResult(404 if url.endswith("01h_ticks.bi5") else 200, payload)

    dataset = MarketDataset("id", "dukascopy", "eurusd", "ticks", "EURUSD", "-1", "UTC")
    with pytest.raises(ValueError, match="Incomplete Dukascopy tick day"):
        asyncio.run(
            _fetch_day(
                PartialNetwork(), dataset, datetime(2020, 4, 2, tzinfo=UTC).date()
            )
        )


def test_unprovisioned_market_is_truthfully_unavailable(tmp_path) -> None:
    """No active database migration means neither direct nor CDN mode starts."""
    owner = "plugin.data_manager.dukascopy"
    context = HostCapabilities(
        resources=None,
        jobs=JobAccess(owner, JobManager(1, 1024)),
        log=None,
        market_data=MarketAccess(
            owner, MarketDataStore(tmp_path, tmp_path / "database" / "haruquantai.db")
        ),
        network=NetworkAccess(owner, HistoricalNetwork()),
    )
    contribution = asyncio.run(prepare(context))
    catalog = asyncio.run(contribution.invoke("catalog", {}))
    assert catalog["modes"] == {
        "standard": "unavailable",
        "cdn": "unavailable",
        "cdn-cn": "unavailable",
    }
    assert catalog["brokers"] == []
    assert catalog["broker_catalog_status"] == "unavailable"
    with pytest.raises(ValueError, match="migration is required"):
        asyncio.run(contribution.invoke("download.start", {}))


def test_broker_catalog_is_available_without_market_migration(tmp_path) -> None:
    """The plugin reads host broker summaries even when acquisition is gated."""
    database = tmp_path / "database" / "haruquantai.db"
    database.parent.mkdir(parents=True)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, "
            "postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (2,'RoboForex','_robo','EET',1,1)"
        )
    owner = "plugin.data_manager.dukascopy"
    context = HostCapabilities(
        resources=None,
        jobs=JobAccess(owner, JobManager(1, 1024)),
        log=None,
        market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
        network=NetworkAccess(owner, HistoricalNetwork()),
    )
    contribution = asyncio.run(prepare(context))
    catalog = asyncio.run(contribution.invoke("catalog", {}))
    assert catalog["modes"]["standard"] == "unavailable"
    assert catalog["broker_catalog_status"] == "available"
    assert catalog["brokers"] == [
        {
            "id": "2",
            "name": "RoboForex",
            "postfix": "_robo",
            "timezone": "EET",
            "mtUse": True,
            "instruments": [],
        }
    ]

    assert catalog["definitions_available"] is False


def test_definition_operation_without_file_tables(tmp_path) -> None:
    """The mounted operation saves a definition while downloads remain unavailable."""
    from app.persistence.market import SCHEMA

    database = tmp_path / "definitions.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript(SCHEMA.split("CREATE TABLE market_files")[0])
    owner = "plugin.data_manager.dukascopy"
    context = HostCapabilities(
        resources=None,
        jobs=JobAccess(owner, JobManager(1, 1024)),
        log=None,
        market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
        network=NetworkAccess(owner, HistoricalNetwork()),
    )
    contribution = asyncio.run(prepare(context))
    result = asyncio.run(
        contribution.invoke(
            "definitions.add",
            {
                "symbols": ["USDJPY", "EURUSD"],
                "kind": "m1",
                "postfix": "_research",
            },
        )
    )
    assert len(result["ids"]) == 2
    catalog = asyncio.run(contribution.invoke("catalog", {}))
    assert catalog["definitions_available"] is True
    assert catalog["modes"]["standard"] == "unavailable"
    assert len(catalog["datasets"]) == 2
    for payload in (
        {"symbols": [], "kind": "m1"},
        {"symbols": [3], "kind": "m1"},
        {"symbols": ["USDJPY"], "kind": "m1", "instruments": ["bad"]},
    ):
        with pytest.raises((ValueError, TypeError)):
            asyncio.run(contribution.invoke("definitions.add", payload))


def test_direct_m1_job_publishes_from_offline_provider(tmp_path) -> None:
    """A host job downloads, decodes and catalogs one canonical M1 year."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.05),
        format=lzma.FORMAT_ALONE,
    )

    class FixtureNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            assert url.endswith("/2020/03/02/BID_candles_min_1.bi5")
            return NetworkResult(200, payload)

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        jobs = JobManager(1, 256 * 1024 * 1024)
        market = MarketAccess(owner, MarketDataStore(tmp_path, database))
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, jobs),
            log=None,
            market_data=market,
            network=NetworkAccess(owner, FixtureNetwork()),
        )
        contribution = await prepare(context)
        dataset = await contribution.invoke(
            "add", {"symbol": "EURUSD", "kind": "m1", "instrument": "EURUSD"}
        )
        started = await contribution.invoke(
            "download.start",
            {
                "dataset_id": dataset["id"],
                "date_from": "2020-04-02",
                "date_to": "2020-04-02",
                "mode": "standard",
                "overwrite": False,
            },
        )
        for _ in range(100):
            status = await contribution.invoke(
                "download.status", {"job_id": started["job_id"]}
            )
            if status["state"] in ("succeeded", "failed", "cancelled"):
                break
            await asyncio.sleep(0.01)
        assert status["state"] == "succeeded", status
        assert status["published_days"] == 1
        records = market.list_files("dukascopy", "m1", "eurusd")
        assert len(records) == 1
        assert records[0].relative_path == "market/dukascopy/m1/eurusd/2020.parquet"
        await contribution.close()
        await jobs.close()

    asyncio.run(scenario())
