"""Canonical registration, bounded retrieval and storage across broker sources."""

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pandas as pd
import pyarrow.parquet as pq
import pytest
from app.core.data.market_storage import M1_SCHEMA, TICK_SCHEMA, provider_storage_name
from app.core.enums import Timeframe
from app.core.host.persistence import HostPersistence
from app.core.trading.connection.contracts import BridgeError
from app.workspace.data_manager.sources import (
    CRYPTO,
    PROVIDERS,
    Sources,
    capabilities,
    intervals,
    make_client,
    provider_id,
)


class Provider:
    """Return native bars for precisely the requested range, like a bounded REST page."""

    def __init__(self):
        self.calls = []
        self.closed = False
        self.fail = False

    def get_bars(self, symbol, timeframe, *, date_from, date_to, count, limit):
        assert count is None
        self.calls.append((symbol, date_from, date_to))
        if self.fail:
            raise BridgeError("Network failed", code="NETWORK_ERROR")
        seconds = Timeframe.resolve(timeframe).to_seconds()
        dates = pd.date_range(date_from, date_to, freq=pd.Timedelta(seconds=seconds))
        assert len(dates) <= limit
        return pd.DataFrame(
            {
                **dict.fromkeys(
                    ["Open", "High", "Low", "Close"], [1.12345678] * len(dates)
                ),
                "Volume": 10,
            },
            index=dates,
        )

    def get_ticks(self, symbol, *, date_from, date_to, count):
        assert count is None
        return pd.DataFrame(
            {"Bid": [1.1], "Ask": [1.10001], "Flags": [3]},
            index=pd.to_datetime([date_from], utc=True),
        )

    def disconnect(self):
        self.closed = True


@pytest.fixture
def sources(tmp_path):
    database = tmp_path / "datasets.db"
    sqlite3.connect(database).close()
    gateway = HostPersistence(database)
    provider = Provider()
    service = Sources(
        gateway, market_root=tmp_path / "market", client_factory=lambda _: provider
    )
    return service, provider


@pytest.mark.parametrize("source", PROVIDERS)
def test_each_source_persists_real_bars_with_native_timeframe_and_catalog(
    sources, source
):
    service, provider = sources
    tf = capabilities(source)["default_timeframe"]
    symbol = (
        "@ES"
        if source == "sq_futures"
        else "EURUSD=X"
        if source == "yahoo"
        else "BTCUSD_PERP"
        if source == "binance_coinm"
        else "TEST"
    )
    record = service.add(source, [{"symbol": symbol, "timeframe": tf}])["data"][
        "records"
    ][0]
    result = service.download(
        record["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:04:00Z"
    )
    assert result["success"]
    row = result["data"]["record"]
    path = (
        service.market_root
        / provider_storage_name(source)
        / tf.lower()
        / symbol.lower()
        / "2025.parquet"
    )
    assert json.loads(row["lineage_json"])["partitions"] == [str(path)]
    metadata = pq.read_metadata(path)
    assert metadata.num_rows == row["bars"] > 0
    assert metadata.schema.to_arrow_schema().remove_metadata().equals(M1_SCHEMA)
    assert metadata.row_group(0).column(0).compression == "ZSTD"
    table = pq.ParquetFile(path).read()
    assert table["Open"][0].as_py() == 112345678
    assert provider.closed == (source != "mt5")


def test_crypto_requests_cover_more_than_one_thousand_rows_without_truncation(sources):
    service, provider = sources
    row = service.add("coinbase", [{"symbol": "BTC-USD", "timeframe": "M1"}])["data"][
        "records"
    ][0]
    start = datetime(2025, 1, 6, tzinfo=UTC)
    result = service.download(row["id"], start, start + timedelta(minutes=1199))
    assert result["data"]["record"]["bars"] == 1200
    assert len(provider.calls) == 6
    assert all(
        (upper - lower).total_seconds() < 200 * 60 for _, lower, upper in provider.calls
    )


def test_darwinex_ticks_use_one_month_file_and_unsigned_flags(sources):
    service, _ = sources
    row = service.add("darwinex", [{"symbol": "EURUSD", "timeframe": "TICK"}])["data"][
        "records"
    ][0]
    result = service.download(row["id"], "2025-04-01", "2025-04-01")
    path = (
        service.market_root
        / "darwinex"
        / "ticks"
        / "eurusd"
        / "2025"
        / "04-apr.parquet"
    )
    assert result["data"]["record"]["bars"] == 1
    assert pq.read_schema(path).remove_metadata().equals(TICK_SCHEMA)


def test_failure_does_not_publish_fake_files_or_counts(sources):
    service, provider = sources
    row = service.add("yahoo", [{"symbol": "AAPL"}])["data"]["records"][0]
    provider.fail = True
    with pytest.raises(BridgeError, match="Network failed"):
        service.download(row["id"], "2025-01-01", "2025-01-02")
    assert service.record(row["id"])["bars"] == 0
    assert list(service.market_root.rglob("*.parquet")) == []


def test_invalid_registration_is_atomic_and_native_capabilities_are_truthful(sources):
    service, _ = sources
    with pytest.raises(ValueError):
        service.add(
            "sq_equity", [{"symbol": "AAPL"}, {"symbol": "MSFT", "timeframe": "M1"}]
        )
    assert service.gateway.read_records("datamgr_datasets")["data"]["records"] == []
    with pytest.raises(ValueError):
        service.add("yahoo", [{"symbol": "../../outside"}])
    with pytest.raises(ValueError):
        service.add("coinbase", [{"symbol": "BTC-USD", "timeframe": "TICK"}])


def test_crypto_market_routing_does_not_merge_derivative_symbols():
    for source, (exchange, venue) in CRYPTO.items():
        client = make_client(source)
        try:
            assert client.exchange == exchange
            assert client.venue == venue
            if source == "binance_coinm":
                assert client._normalize_symbol("BTCUSD_PERP") == "BTCUSD_PERP"
        finally:
            client.disconnect()
    assert provider_id("BinanceCoinM") == "binance_coinm"
    assert provider_id("BinanceUsdtM") == "binance_usdtm"


def test_yearly_cdn_intervals_cover_the_whole_request():
    lower = datetime(2023, 6, 1, tzinfo=UTC)
    upper = datetime(2025, 2, 1, tzinfo=UTC)
    chunks = intervals("darwinex", "M1", lower, upper)
    assert len(chunks) == 3 and chunks[0][0] == lower and chunks[-1][1] == upper


def test_mt5_awaitable_runs_on_its_own_bridge_loop_and_publishes(sources):
    import asyncio
    import threading

    service, provider = sources
    loop = asyncio.new_event_loop()
    ready = threading.Event()
    loop.call_soon(ready.set)
    thread = threading.Thread(target=loop.run_forever)
    thread.start()
    assert ready.wait(5)

    class AsyncTerminal:
        _loop = loop

        async def get_bars(self, *args, **kwargs):
            assert asyncio.get_running_loop() is loop
            return provider.get_bars(*args, **kwargs)

    service.client_factory = lambda _: AsyncTerminal()
    try:
        row = service.add("mt5", [{"symbol": "EURUSD", "timeframe": "M1"}])["data"][
            "records"
        ][0]
        result = service.download(
            row["id"], "2025-01-06T00:00:00Z", "2025-01-06T00:04:00Z"
        )
        assert result["data"]["record"]["bars"] == 5
        assert not provider.closed
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)
        loop.close()


def test_later_source_failure_keeps_earlier_committed_intervals(sources, monkeypatch):
    service, provider = sources
    original = provider.get_bars

    def fetch(*args, **kwargs):
        if provider.calls:
            provider.fail = True
        return original(*args, **kwargs)

    monkeypatch.setattr(provider, "get_bars", fetch)
    row = service.add("coinbase", [{"symbol": "BTC-USD", "timeframe": "M1"}])["data"][
        "records"
    ][0]
    with pytest.raises(BridgeError):
        service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T06:00:00Z")
    assert service.record(row["id"])["bars"] == 200


def test_darwinex_tick_archive_filters_days_before_decoding():
    from app.workspace.brokers.darwinex import _tick_archive_names

    start = int(datetime(2025, 1, 6, 12, tzinfo=UTC).timestamp() * 1000)
    names = ["2025_01_05.dat", "2025_01_06.dat", "2025_01_07.dat"]
    assert _tick_archive_names(names, start, start + 120_000) == ["2025_01_06.dat"]


def test_mt5_disconnected_status_never_claims_a_download_connection(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    from app.workspace.brokers import base
    from app.workspace.data_manager import sources

    client = SimpleNamespace(
        bridge=SimpleNamespace(
            connected=False,
            listening=False,
            host="127.0.0.1",
            port=8765,
        )
    )
    monkeypatch.setattr(sources.http, "get_broker", lambda _: client)
    monkeypatch.setattr(base, "get_broker", lambda _: client)
    result = asyncio.run(sources.bridge_action("status", SimpleNamespace()))
    assert not result["connected"] and not result["listening"]
    assert "auth_token" not in result
    with pytest.raises(ValueError, match="Connect the MT5 terminal"):
        make_client("mt5")


def test_mt5_listener_status_tracks_the_actual_server():
    import asyncio

    from app.workspace.brokers.metatrader import Bridge

    async def exercise():
        bridge = Bridge(auth_token="test-token-at-least-16-characters", port=0)
        assert not bridge.listening
        await bridge.start()
        try:
            assert bridge.listening and not bridge.connected
        finally:
            await bridge.close()
        assert not bridge.listening

    asyncio.run(exercise())


def test_mt5_backend_singleton_uses_the_same_configured_factory_as_cli(monkeypatch):
    from unittest.mock import Mock

    from app.workspace.brokers import base, metatrader

    client = object()
    factory = Mock(return_value=client)
    monkeypatch.setattr(base, "_SINGLETONS", {})
    monkeypatch.setattr(metatrader, "create_mt5_client", factory)
    assert base.get_broker("mt5") is client
    assert base.get_broker("metatrader") is client
    factory.assert_called_once_with()


def test_wholly_empty_request_retains_provider_details_and_logs(
    sources, monkeypatch, caplog
):
    service, provider = sources
    row = service.add("sq_futures", [{"symbol": "@ES"}])["data"]["records"][0]

    def empty(*args, **kwargs):
        raise BridgeError(
            "Inspected CDN archives contain 2019-01-02 through 2024-05-15.",
            code="NO_DATA",
        )

    monkeypatch.setattr(provider, "get_bars", empty)
    with caplog.at_level("WARNING"), pytest.raises(ValueError) as caught:
        service.download(row["id"], "2026-01-01", "2026-02-01")
    assert "@ES" in str(caught.value) and "2026-01-01" in str(caught.value)
    assert "2024-05-15" in str(caught.value)
    assert "FR-DATA-SOURCES-EMPTY-RANGE" in caplog.text
    assert service.record(row["id"])["bars"] == 0
    assert not list(service.market_root.rglob("*.parquet"))
    assert provider.closed


def test_empty_subinterval_does_not_discard_successful_observations(
    sources, monkeypatch
):
    service, provider = sources
    row = service.add("coinbase", [{"symbol": "BTC-USD", "timeframe": "M1"}])["data"][
        "records"
    ][0]
    original = provider.get_bars
    calls = 0

    def partly_empty(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise BridgeError("No observations in this subinterval", code="NO_DATA")
        return original(*args, **kwargs)

    monkeypatch.setattr(provider, "get_bars", partly_empty)
    result = service.download(row["id"], "2025-01-06T00:00:00Z", "2025-01-06T06:39:00Z")
    assert result["success"]
    assert result["data"]["received_rows"] > 0
    assert calls == 2 and provider.closed


def test_storage_names_preserve_source_identity_and_log(caplog):
    with caplog.at_level("DEBUG"):
        assert provider_storage_name("sq_futures") == "futures"
        assert provider_storage_name("sq_equity") == "equity"
        assert provider_storage_name("yahoo") == "yahoo"
    assert "FR-MARKET-STORAGE-provider-folders" in caplog.text
