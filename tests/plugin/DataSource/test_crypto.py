"""Exchange-specific field ordering, units and decimal volume preservation."""

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import pytest
from app.host.network import NetworkResult
from app.plugin.DataSource.crypto import (
    BinanceCoinMExchange,
    BinanceExchange,
    BinanceUsdtMExchange,
    BitfinexExchange,
    CoinbaseProExchange,
    ExchangeType,
    PoloniexExchange,
    normalize_symbol_for_exchange,
)


@pytest.mark.parametrize(
    "factory, timeframe, payload",
    [
        (BinanceExchange, "M1", [[1000, "2", "4", "1", "3", "0.125"]]),
        (BinanceCoinMExchange, "M1", [[1000, "2", "4", "1", "3", "0.125"]]),
        (BinanceUsdtMExchange, "M1", [[1000, "2", "4", "1", "3", "0.125"]]),
        (BitfinexExchange, "M1", [[1000, "2", "3", "4", "1", "0.125"]]),
        (CoinbaseProExchange, "M1", [[1, "1", "4", "2", "3", "0.125"]]),
        (
            PoloniexExchange,
            "M5",
            [
                [
                    "1",
                    "4",
                    "2",
                    "3",
                    "0.125",
                    "0",
                    "0",
                    "0",
                    0,
                    1000,
                    0,
                    "MINUTE_5",
                    1000,
                    2000,
                ]
            ],
        ),
    ],
)
def test_exchange_candle_mapping(
    factory: Any, timeframe: Any, payload: Any, monkeypatch: Any
) -> None:
    calls = []

    class FixtureNetwork:
        async def get(
            self, url: Any, params: Any = None, request_seconds: Any = 30
        ) -> Any:
            calls.append((url, params))
            return NetworkResult(200, json.dumps(payload).encode())

    async def no_sleep(seconds: Any) -> Any:
        return

    monkeypatch.setattr("app.plugin.DataSource.crypto.asyncio.sleep", no_sleep)
    frame = asyncio.run(
        factory(FixtureNetwork()).download_candles("BTCUSD", timeframe, 1000, 1000)
    )
    assert len(frame) == 1
    assert frame.iloc[0]["DateTime"].value // 1_000_000 == 1000
    assert frame[["Open", "High", "Low", "Close", "Volume"]].iloc[0].tolist() == [
        2,
        4,
        1,
        3,
        0.125,
    ]
    assert len(calls) == 1


def test_native_symbol_and_timeframe_policies() -> None:
    assert normalize_symbol_for_exchange("BTC/USDT", ExchangeType.BINANCE) == "BTCUSDT"
    assert (
        normalize_symbol_for_exchange("BTCUSD", ExchangeType.BINANCE_COIN_M)
        == "BTCUSD_PERP"
    )
    assert (
        normalize_symbol_for_exchange("BTCUSDT", ExchangeType.COINBASE_PRO)
        == "BTC-USDT"
    )
    assert normalize_symbol_for_exchange("BTCUSDT", ExchangeType.POLONIEX) == "BTC_USDT"
    with pytest.raises(ValueError, match="Unsupported"):
        ExchangeType.resolve("not-an-exchange")


def test_nested_retries_and_retry_after(monkeypatch: Any) -> None:
    from app.plugin.DataSource.crypto import CryptoNetwork

    responses = [NetworkResult(503, b"")] * 6 + [
        NetworkResult(429, b"", "7"),
        NetworkResult(200, b"[]"),
    ]
    sleeps = []

    class Session:
        async def get(self, *args: Any, **kwargs: Any) -> Any:
            return responses.pop(0)

    async def sleep(seconds: Any) -> Any:
        sleeps.append(seconds)

    monkeypatch.setattr("app.plugin.DataSource.crypto.asyncio.sleep", sleep)
    result = asyncio.run(
        CryptoNetwork(cast("Any", Session())).get("https://api.binance.com")
    )
    assert result.status == 200
    assert not responses
    assert sleeps == [3, 6, 12, 24, 1, 7]


def test_crypto_job_publishes_fractional_volume_and_retains_after_close(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import httpx
    from app.host.capabilities import JobAccess, MarketAccess
    from app.host.jobs import JobManager
    from app.host.network import SourceNetwork
    from app.persistence.market import MarketDataStore, create_isolated_schema
    from app.plugin.DataSource.crypto import CryptoNetwork, CryptoRuntime

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)

    def transport(request: Any) -> Any:
        return httpx.Response(200, json=[[1704067200000, "2", "4", "1", "3", "0.125"]])

    async def no_sleep(seconds: Any) -> Any:
        return

    monkeypatch.setattr("app.plugin.DataSource.crypto.asyncio.sleep", no_sleep)

    async def scenario() -> None:
        owner = "plugin.data_manager.crypto"
        market = MarketAccess(owner, store)
        jobs = JobManager(1, 512 * 1024 * 1024)
        session = SourceNetwork(
            ("https://api.binance.com",),
            client=httpx.AsyncClient(transport=httpx.MockTransport(transport)),
        )
        runtime = CryptoRuntime(
            market,
            JobAccess(owner, jobs),
            {ExchangeType.BINANCE: BinanceExchange(CryptoNetwork(session))},
        )
        dataset_id = market.register_source(
            source="Crypto",
            symbol="BTCUSDT",
            underlying="BTCUSDT",
            instrument="BTCUSDT",
            timeframe="D1",
            options={
                "parameters": {
                    "exchange": "Binance",
                    "symbol": "BTCUSDT",
                    "timeframe": "D1",
                }
            },
        )
        started = cast(
            "Any",
            await runtime.invoke(
                "download.start",
                {
                    "dataset_id": dataset_id,
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
        assert status["published_partitions"] == 1
        await runtime.close()
        await jobs.close()
        partition = store.source_partitions(dataset_id)[0]
        table = store.read_source_partition(partition)
        assert table.column("Volume").to_pylist() == [0.125]
        assert table.column("Close").to_pylist() == [3.0]
        assert store.source_definition(owner, dataset_id)["bars"] == 1

    asyncio.run(scenario())
