"""Deterministic offline BI5 examples, with no provider request."""

import asyncio
import lzma
import re
import sqlite3
import struct
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    NetworkAccess,
)
from app.host.jobs import JobManager
from app.host.network import HistoricalNetwork, NetworkResult
from app.persistence.market import (
    MarketDataset,
    MarketDataStore,
    create_isolated_schema,
)
from app.plugin.DataSource.dukascopy import (
    RateCorrector,
    _fetch_day,
    cdn_archive_url,
    cdn_base_url,
    cdn_metadata_url,
    decode_m1,
    decode_ticks,
    prepare,
    standard_url,
)
from pydantic import JsonValue


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
        "http://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/15/00h_ticks.bi5"
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


def test_corrupt_and_invalid_volume_fail() -> None:
    """Malformed records and negative or non-finite volume cannot be published."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    with pytest.raises(ValueError):
        decode_ticks(b"not bi5", instant, "EURUSD")
    payload = lzma.compress(
        struct.pack(">IIIff", 0, 110002, 110000, -0.01, 0.0),
        format=lzma.FORMAT_ALONE,
    )
    with pytest.raises(ValueError, match="Invalid provider volume"):
        decode_ticks(payload, instant, "EURUSD")
    with pytest.raises(ValueError, match="supported FX"):
        standard_url("XAUUSD", instant, "ticks")


def test_real_world_float32_volume_decoding() -> None:
    """Float32 candle volume from real Dukascopy feeds decodes without precision drift."""
    instant = datetime(2024, 1, 15, tzinfo=UTC)
    # 157.14 in float32 has exact value 157.1399993896484375
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 157.14),
        format=lzma.FORMAT_ALONE,
    )
    rows = decode_m1(payload, instant, "EURUSD")
    assert rows == (
        (
            int(instant.timestamp() * 1000) + 60000,
            1.1,
            1.1002,
            1.0999,
            1.1001,
            157140000,
        ),
    )


def test_saturday_forex_is_skipped(tmp_path: Path) -> None:
    """Saturday forex acquisition is recognized as weekend and skipped."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)

    class CountingNetwork(HistoricalNetwork):
        def __init__(self) -> None:
            self.requests: list[str] = []

        async def get(self, url: str) -> NetworkResult:
            self.requests.append(url)
            return NetworkResult(404, b"")

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        jobs = JobManager(1, 256 * 1024 * 1024)
        market = MarketAccess(owner, MarketDataStore(tmp_path, database))
        net = CountingNetwork()
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, jobs),
            log=None,
            market_data=market,
            network=NetworkAccess(owner, net),
        )
        contribution = await prepare(context)
        dataset = await contribution.invoke(
            "add", {"symbol": "EURUSD", "kind": "m1", "instrument": "EURUSD"}
        )
        assert isinstance(dataset, dict)
        # 2024-01-13 was a Saturday
        started = await contribution.invoke(
            "download.start",
            {
                "dataset_id": dataset["id"],
                "date_from": "2024-01-13",
                "date_to": "2024-01-13",
                "mode": "standard",
                "overwrite": False,
            },
        )
        assert isinstance(started, dict)
        status: Any = {}
        for _ in range(100):
            status = await contribution.invoke(
                "download.status", {"job_id": started["job_id"]}
            )
            assert isinstance(status, dict)
            if status["state"] in ("succeeded", "failed", "cancelled"):
                break
            await asyncio.sleep(0.01)

        assert isinstance(status, dict)
        assert status["state"] == "succeeded", status
        assert status["skipped_days"] == 1
        assert len(net.requests) == 0
        await contribution.close()
        await jobs.close()

    asyncio.run(scenario())


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
    net_access = NetworkAccess("plugin.data_manager.dukascopy", PartialNetwork())
    with pytest.raises(ValueError, match="Incomplete Dukascopy tick day"):
        asyncio.run(
            _fetch_day(net_access, dataset, datetime(2020, 4, 2, tzinfo=UTC).date())
        )


def test_unprovisioned_market_is_truthfully_unavailable(tmp_path: Path) -> None:
    """No active database migration means neither direct nor CDN mode starts."""

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, JobManager(1, 1024)),
            log=None,
            market_data=MarketAccess(
                owner,
                MarketDataStore(tmp_path, tmp_path / "database" / "haruquantai.db"),
            ),
            network=NetworkAccess(owner, HistoricalNetwork()),
        )
        contribution = await prepare(context)
        catalog = await contribution.invoke("catalog", {})
        assert isinstance(catalog, dict)
        assert catalog["modes"] == {
            "standard": "unavailable",
            "cdn": "unavailable",
            "cdn-cn": "unavailable",
        }
        assert catalog["brokers"] == []
        assert catalog["broker_catalog_status"] == "unavailable"
        with pytest.raises(ValueError, match="migration is required"):
            await contribution.invoke("download.start", {})
        await contribution.close()

    asyncio.run(scenario())


def test_broker_catalog_is_available_without_market_migration(tmp_path: Path) -> None:
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

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, JobManager(1, 1024)),
            log=None,
            market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
            network=NetworkAccess(owner, HistoricalNetwork()),
        )
        contribution = await prepare(context)
        catalog = await contribution.invoke("catalog", {})
        assert isinstance(catalog, dict)
        modes = catalog["modes"]
        assert isinstance(modes, dict)
        assert modes["standard"] == "unavailable"
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
        await contribution.close()

    asyncio.run(scenario())


def test_definition_operation_without_file_tables(tmp_path: Path) -> None:
    """The mounted operation saves a definition while downloads remain unavailable."""
    from app.persistence.market import SCHEMA

    database = tmp_path / "definitions.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript(SCHEMA.split("CREATE TABLE market_files")[0])

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, JobManager(1, 1024)),
            log=None,
            market_data=MarketAccess(owner, MarketDataStore(tmp_path, database)),
            network=NetworkAccess(owner, HistoricalNetwork()),
        )
        contribution = await prepare(context)
        result = await contribution.invoke(
            "definitions.add",
            {
                "symbols": ["USDJPY", "EURUSD"],
                "kind": "m1",
                "postfix": "_research",
            },
        )
        assert isinstance(result, dict)
        ids = result["ids"]
        assert isinstance(ids, list)
        assert len(ids) == 2
        catalog = await contribution.invoke("catalog", {})
        assert isinstance(catalog, dict)
        assert catalog["definitions_available"] is True
        modes = catalog["modes"]
        assert isinstance(modes, dict)
        assert modes["standard"] == "unavailable"
        datasets = catalog["datasets"]
        assert isinstance(datasets, list)
        assert len(datasets) == 2
        bad_payloads: list[JsonValue] = [
            {"symbols": [], "kind": "m1"},
            {"symbols": [3], "kind": "m1"},
            {"symbols": ["USDJPY"], "kind": "m1", "instruments": ["bad"]},
        ]
        for payload in bad_payloads:
            with pytest.raises((ValueError, TypeError)):
                await contribution.invoke("definitions.add", payload)
        await contribution.close()

    asyncio.run(scenario())


def test_direct_m1_job_publishes_from_offline_provider(tmp_path: Path) -> None:
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
        assert isinstance(dataset, dict)
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
        assert isinstance(started, dict)
        status: Any = {}
        for _ in range(100):
            status = await contribution.invoke(
                "download.status", {"job_id": started["job_id"]}
            )
            assert isinstance(status, dict)
            if status["state"] in ("succeeded", "failed", "cancelled"):
                break
            await asyncio.sleep(0.01)
        assert isinstance(status, dict)
        assert status["state"] == "succeeded", status
        assert status["published_days"] == 1
        records = market.list_files("dukascopy", "m1", "eurusd")
        assert len(records) == 1
        assert records[0].relative_path == "market/dukascopy/m1/eurusd/2020.parquet"
        await contribution.close()
        await jobs.close()

    asyncio.run(scenario())


def test_rate_corrector_backoff_and_recovery() -> None:
    """Delay increases by 25% on failure and decreases by 25% after 100 successes."""
    corrector = RateCorrector(
        min_delay_seconds=0.01, max_delay_seconds=1.0, success_threshold=100
    )
    assert corrector.delay == 0.01

    # Failure triggers +25% backoff
    corrector.record_failure()
    assert abs(corrector.delay - 0.0125) < 1e-6

    # Further failures back off exponentially up to max_delay
    for _ in range(30):
        corrector.record_failure()
    assert corrector.delay == 1.0

    # 100 consecutive successes trigger -25% recovery (1.0 * 0.75 = 0.75)
    for _ in range(99):
        corrector.record_success()
    assert corrector.delay == 1.0
    corrector.record_success()
    assert abs(corrector.delay - 0.75) < 1e-6


def test_sunday_forex_ticks_starts_at_19_utc() -> None:
    """Sunday tick acquisition ignores closed hours 0-18 and begins at hour 19."""
    instant = datetime(2024, 1, 14, tzinfo=UTC)  # 2024-01-14 is a Sunday
    assert instant.weekday() == 6
    payload = lzma.compress(
        struct.pack(">IIIff", 0, 110002, 110000, 0.01, 0.02),
        format=lzma.FORMAT_ALONE,
    )
    requested_hours: list[int] = []

    class SundayNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            match = re.search(r"/(\d{2})h_ticks\.bi5$", url)
            if match:
                requested_hours.append(int(match.group(1)))
            return NetworkResult(200, payload)

    dataset = MarketDataset("id", "dukascopy", "eurusd", "ticks", "EURUSD", "-1", "UTC")
    network = NetworkAccess("plugin.data_manager.dukascopy", SundayNetwork())
    table = asyncio.run(_fetch_day(network, dataset, instant.date()))
    # Hours 0..18 must not be requested at all on Sunday
    assert requested_hours == list(range(19, 24))
    assert table.num_rows == 5


def test_cdn_url_builders() -> None:
    """Global and China CDN URLs format descriptors and archive paths."""
    assert (
        cdn_base_url("cdn", "m1")
        == "https://cdn.strategyquantcdn.com/data/dukascopy/m1"
    )
    assert (
        cdn_base_url("cdn-cn", "tick")
        == "https://cdn005.strategyquantcdn.com/data/dukascopy/tick"
    )
    assert (
        cdn_metadata_url("cdn", "m1", "EURUSD")
        == "https://cdn.strategyquantcdn.com/data/dukascopy/m1/EURUSD/metadata.dat"
    )
    assert (
        cdn_archive_url("cdn", "m1", "EURUSD", "2020")
        == "https://cdn.strategyquantcdn.com/data/dukascopy/m1/EURUSD/2020.zip"
    )
    assert (
        cdn_archive_url("cdn-cn", "ticks", "EURUSD", "2020-04")
        == "https://cdn005.strategyquantcdn.com/data/dukascopy/tick/EURUSD/2020_04.zip"
    )


def test_cdn_mode_with_automatic_fallback(tmp_path: Path) -> None:
    """CDN mode checks metadata and automatically falls back to direct download."""
    database = tmp_path / "database" / "haruquantai.db"
    create_isolated_schema(database)
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.05),
        format=lzma.FORMAT_ALONE,
    )

    class FallbackNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            if "metadata.dat" in url:
                return NetworkResult(404, b"")
            if url.endswith("/2020/03/02/BID_candles_min_1.bi5"):
                return NetworkResult(200, payload)
            return NetworkResult(404, b"")

    async def scenario() -> None:
        owner = "plugin.data_manager.dukascopy"
        jobs = JobManager(1, 256 * 1024 * 1024)
        market = MarketAccess(owner, MarketDataStore(tmp_path, database))
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess(owner, jobs),
            log=None,
            market_data=market,
            network=NetworkAccess(owner, FallbackNetwork()),
        )
        contribution = await prepare(context)
        catalog = await contribution.invoke("catalog", {})
        assert isinstance(catalog, dict)
        modes = catalog["modes"]
        assert isinstance(modes, dict)
        assert modes["cdn"] == "available"
        assert modes["cdn-cn"] == "available"

        dataset = await contribution.invoke(
            "add", {"symbol": "EURUSD", "kind": "m1", "instrument": "EURUSD"}
        )
        assert isinstance(dataset, dict)
        started = await contribution.invoke(
            "download.start",
            {
                "dataset_id": dataset["id"],
                "date_from": "2020-04-02",
                "date_to": "2020-04-02",
                "mode": "cdn",
                "overwrite": False,
            },
        )
        assert isinstance(started, dict)
        status: Any = {}
        for _ in range(100):
            status = await contribution.invoke(
                "download.status", {"job_id": started["job_id"]}
            )
            assert isinstance(status, dict)
            if status["state"] in ("succeeded", "failed", "cancelled"):
                break
            await asyncio.sleep(0.01)

        assert isinstance(status, dict)
        assert status["state"] == "succeeded", status
        assert status["requested_mode"] == "cdn"
        assert status["effective_mode"] == "standard"
        assert status["published_days"] == 1
        await contribution.close()
        await jobs.close()

    asyncio.run(scenario())


def test_disclaimer_operation(tmp_path: Path) -> None:
    """Disclaimer operation returns official legal disclaimer texts."""

    async def scenario() -> None:
        db_path = tmp_path / "haruquantai.db"
        create_isolated_schema(db_path)
        store = MarketDataStore(tmp_path, db_path)
        market = MarketAccess("plugin.data_manager.dukascopy", store)
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess("plugin.data_manager.dukascopy", JobManager(1, 1024 * 1024)),
            log=None,
            market_data=market,
            network=NetworkAccess("plugin.data_manager.dukascopy", HistoricalNetwork()),
        )
        contribution = await prepare(context)
        res = await contribution.invoke("disclaimer", {})
        assert isinstance(res, dict)
        assert isinstance(res["dukascopy_disclaimer"], str)
        assert "Dukascopy Bank SA" in res["dukascopy_disclaimer"]
        assert isinstance(res["cdn_disclaimer"], str)
        assert "StrategyQuant" in res["cdn_disclaimer"]
        await contribution.close()

    asyncio.run(scenario())


def test_dukascopy_logging(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Plugin emits expected info logs during lifecycle and operations."""

    async def scenario() -> None:
        db_path = tmp_path / "haruquantai.db"
        create_isolated_schema(db_path)
        store = MarketDataStore(tmp_path, db_path)
        market = MarketAccess("plugin.data_manager.dukascopy", store)
        context = HostCapabilities(
            resources=None,
            jobs=JobAccess("plugin.data_manager.dukascopy", JobManager(1, 1024 * 1024)),
            log=None,
            market_data=market,
            network=NetworkAccess("plugin.data_manager.dukascopy", HistoricalNetwork()),
        )
        with caplog.at_level("INFO", logger="app.plugin.DataSource.dukascopy"):
            contribution = await prepare(context)
            await contribution.invoke("disclaimer", {})
            await contribution.close()

        assert "Preparing Dukascopy data source plugin" in caplog.text
        assert "Dukascopy plugin invoking operation: disclaimer" in caplog.text
        assert "Dukascopy data source plugin closed" in caplog.text

    asyncio.run(scenario())


def test_fetch_day_transient_rate_limit_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_day retries on transient 429 and succeeds when endpoint recovers."""
    from app.persistence.market import MarketDataset
    from app.plugin.DataSource.dukascopy import _fetch_day

    # Speed up backoff sleep for tests
    monkeypatch.setattr(
        "app.plugin.DataSource.dukascopy.INITIAL_RATE_BACKOFF_SECONDS", 0.001
    )

    instant = datetime(2024, 1, 15, tzinfo=UTC)
    payload = lzma.compress(
        struct.pack(">IIIIIf", 60, 110000, 110010, 109990, 110020, 0.05),
        format=lzma.FORMAT_ALONE,
    )

    call_count = 0

    class TransientRateLimitNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return NetworkResult(429, b"")
            return NetworkResult(200, payload)

    dataset = MarketDataset("id", "dukascopy", "eurusd", "m1", "EURUSD", "-1", "UTC")
    network = NetworkAccess(
        "plugin.data_manager.dukascopy", TransientRateLimitNetwork()
    )
    table = asyncio.run(_fetch_day(network, dataset, instant.date()))
    assert table.num_rows == 1
    assert call_count == 2

    # Persistent 429 raises ValueError
    class PersistentRateLimitNetwork(HistoricalNetwork):
        async def get(self, url: str) -> NetworkResult:
            return NetworkResult(429, b"")

    persistent_network = NetworkAccess(
        "plugin.data_manager.dukascopy", PersistentRateLimitNetwork()
    )
    with pytest.raises(ValueError, match="rate limit reached"):
        asyncio.run(_fetch_day(persistent_network, dataset, instant.date()))
