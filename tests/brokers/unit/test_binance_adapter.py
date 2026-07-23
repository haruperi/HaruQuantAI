"""Binance adapter tests using an injected fake transport."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.binance_session.adapter import BinanceBrokerAdapter
from pydantic import SecretStr


def _config(broker_id: BrokerId = BrokerId.BINANCE_SPOT) -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={
            "api_key": SecretStr("test-key"),
            "api_secret": SecretStr("test-secret"),
        },
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    mutations = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
    }
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE" if operation in mutations else "AVAILABLE",
            access_mode="WRITE" if operation in mutations else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
            reason="test release gate" if operation in mutations else None,
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self) -> None:
        self.closed = False
        self._klines = [
            [
                0,
                "1",
                "2",
                "0.5",
                "1.5",
                "10",
                60_000,
                "",
                0,
                "",
                "",
            ]
        ]

    async def connect(self) -> bool:
        return True

    async def call(self, name: str, **kwargs: object) -> object:
        del kwargs
        if name == "ping":
            return {}
        if name == "get_server_time":
            return {"serverTime": int(datetime.now(UTC).timestamp() * 1000)}
        if name == "get_exchange_info":
            return {
                "symbols": [
                    {
                        "symbol": "BTCUSDT",
                        "baseAsset": "BTC",
                        "quoteAsset": "USDT",
                        "quoteAssetPrecision": 2,
                        "baseAssetPrecision": 5,
                        "isSpotTradingAllowed": True,
                    }
                ]
            }
        if name == "get_klines":
            return self._klines
        return None

    async def close(self) -> None:
        self.closed = True


def _implementation_adapter(transport: Any) -> BinanceBrokerAdapter:
    """Build a private provider-mapping harness without changing production policy."""
    adapter = BinanceBrokerAdapter(_config(), transport=transport)
    adapter._capabilities = _capabilities()
    return adapter


def test_adapter_rejects_environment_profile_mismatch() -> None:
    """Spot/Futures profiles reject any non-LIVE/TESTNET environment."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    with pytest.raises(ValueError, match="profile/environment mismatch"):
        BinanceBrokerAdapter(bad)


def test_adapter_rejects_unknown_credential_keys() -> None:
    """Only the profile's declared credential keys are accepted."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={"unexpected": SecretStr("x")},
    )
    with pytest.raises(ValueError, match="unknown Binance credential key"):
        BinanceBrokerAdapter(bad)


def test_futures_profiles_remain_registry_only_for_connect() -> None:
    """Futures profiles never verify a connection; Spot is the only live path."""
    adapter = BinanceBrokerAdapter(
        _config(BrokerId.BINANCE_USD_M_FUTURES),
        transport=_FakeTransport(),
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success

    asyncio.run(exercise())


def test_spot_adapter_connects_and_maps_symbols_and_klines() -> None:
    """A verified Spot session maps genuine symbols and klines."""
    transport = _FakeTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        connected = await adapter.connect()
        assert connected.is_success

        symbols = await adapter.get_symbols(limit=10)
        assert symbols.data is not None
        assert symbols.data.items[0].provider_symbol == "BTCUSDT"

        bars = await adapter.get_historical_bars("BTCUSDT", "1m", limit=10)
        assert bars.data is not None
        assert str(bars.data.items[0].open) == "1"

        await adapter.disconnect()

    asyncio.run(exercise())
    assert transport.closed


def test_spot_adapter_platform_info_reports_profile() -> None:
    """Platform info reports the immutable selected product profile."""
    adapter = _implementation_adapter(_FakeTransport())

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.product_profile == "spot"

    asyncio.run(exercise())


def test_adapter_rejects_custom_endpoints() -> None:
    """BinanceBrokerAdapter raises ValueError when an endpoint override is specified."""
    bad = BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        endpoint="http://localhost:5000",
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )
    with pytest.raises(ValueError, match="Binance custom endpoints are unavailable"):
        BinanceBrokerAdapter(bad)


def test_adapter_connect_handles_probe_failure() -> None:
    """A transport connection failure transitions to failed connection state."""

    class _FailingTransport(_FakeTransport):
        async def connect(self) -> bool:
            raise ConnectionError("failed to connect")

    adapter = _implementation_adapter(_FailingTransport())

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success

    asyncio.run(exercise())


def test_adapter_ping() -> None:
    """Spot ping request succeeds on a verified transport."""
    transport = _FakeTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.ping()
        assert result.is_success

    asyncio.run(exercise())


def test_adapter_get_server_time() -> None:
    """Spot server time returns estimated clock offset and latency."""
    transport = _FakeTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_server_time()
        assert result.is_success
        assert result.data is not None
        assert result.data.provider_time is not None

    asyncio.run(exercise())


def test_adapter_get_symbols_filtering_and_errors() -> None:
    """Retrieving symbols handles limit checks and query filtering."""
    transport = _FakeTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        invalid = await adapter.get_symbols(limit=0)
        assert invalid.error is not None
        assert invalid.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID
        res = await adapter.get_symbols(query="BTC", limit=5)
        assert len(res.data.items) == 1
        assert res.data.items[0].provider_symbol == "BTCUSDT"
        res_empty = await adapter.get_symbols(query="ETH", limit=5)
        assert len(res_empty.data.items) == 0

    asyncio.run(exercise())


def test_adapter_get_symbol_info() -> None:
    """Spot symbol info maps a valid configuration or reports missing symbols."""

    class _SymbolTransport(_FakeTransport):
        async def call(self, name: str, **kwargs: object) -> object:
            if name == "get_symbol_info":
                if kwargs.get("symbol") == "BTCUSDT":
                    return {
                        "symbol": "BTCUSDT",
                        "baseAsset": "BTC",
                        "quoteAsset": "USDT",
                        "quoteAssetPrecision": 2,
                        "baseAssetPrecision": 5,
                        "isSpotTradingAllowed": True,
                    }
                return None
            return await super().call(name, **kwargs)

    transport = _SymbolTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        res = await adapter.get_symbol_info("BTCUSDT")
        assert res.is_success
        assert res.data.provider_symbol == "BTCUSDT"
        res_error = await adapter.get_symbol_info("UNKNOWN")
        assert not res_error.is_success

    asyncio.run(exercise())


def test_adapter_get_quote() -> None:
    """Spot quote request maps latest book-ticker ticks."""

    class _QuoteTransport(_FakeTransport):
        async def call(self, name: str, **kwargs: object) -> object:
            if name == "get_orderbook_ticker":
                return {
                    "bidPrice": "1.0",
                    "askPrice": "1.1",
                    "bidQty": "10.0",
                    "askQty": "20.0",
                }
            return await super().call(name, **kwargs)

    transport = _QuoteTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        res = await adapter.get_quote("BTCUSDT")
        assert res.is_success
        assert str(res.data.bid) == "1.0"

    asyncio.run(exercise())


def test_adapter_get_ticks() -> None:
    """Spot tick retrieval maps aggregate trade payloads."""

    class _TicksTransport(_FakeTransport):
        async def call(self, name: str, **kwargs: object) -> object:
            if name == "get_aggregate_trades":
                return [{"T": 1700000000000, "p": "1.2", "q": "5.0", "a": 12345}]
            return await super().call(name, **kwargs)

    transport = _TicksTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        invalid = await adapter.get_ticks("BTCUSDT", limit=0)
        assert invalid.error is not None
        assert invalid.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID
        res = await adapter.get_ticks("BTCUSDT", limit=1)
        assert res.is_success
        assert len(res.data.items) == 1
        assert str(res.data.items[0].last_price) == "1.2"

    asyncio.run(exercise())


def test_adapter_get_historical_bars_parameters() -> None:
    """Spot historical bars map klines and handle bounding datetime inputs."""
    transport = _FakeTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        invalid = await adapter.get_historical_bars("BTCUSDT", "1m", limit=0)
        assert invalid.error is not None
        assert invalid.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID
        res = await adapter.get_historical_bars(
            "BTCUSDT",
            "1m",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
            limit=5,
        )
        assert res.is_success

    asyncio.run(exercise())


def test_adapter_maps_canonical_h1_to_binance_interval() -> None:
    """Canonical H1 is sent as 1h while retaining request provenance."""

    class _RecordingTransport(_FakeTransport):
        def __init__(self) -> None:
            super().__init__()
            self.kline_kwargs: dict[str, object] = {}

        async def call(self, name: str, **kwargs: object) -> object:
            if name == "get_klines":
                self.kline_kwargs = dict(kwargs)
            return await super().call(name, **kwargs)

    transport = _RecordingTransport()
    adapter = _implementation_adapter(transport)

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars("BTCUSDT", "H1", limit=5)
        assert result.is_success
        assert result.data is not None
        assert transport.kline_kwargs["interval"] == "1h"
        assert result.data.items[0].provider_timeframe == "1h"
        assert result.data.items[0].requested_timeframe == "H1"

        unsupported = await adapter.get_historical_bars("BTCUSDT", "H3", limit=5)
        assert unsupported.error is not None
        assert unsupported.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())


def test_adapter_streams_quotes_bars_and_snapshot_first_depth() -> None:
    """Binance websocket subscriptions map genuine bounded provider events."""

    class _StreamTransport(_FakeTransport):
        async def call(self, name: str, **kwargs: object) -> object:
            if name == "get_order_book":
                return {
                    "lastUpdateId": 10,
                    "bids": [["1.0", "2"]],
                    "asks": [["1.1", "3"]],
                }
            return await super().call(name, **kwargs)

        async def stream(
            self, name: str, **kwargs: object
        ) -> AsyncIterator[dict[str, object]]:
            del kwargs
            if name == "symbol_book_ticker_socket":
                yield {
                    "b": "1.0",
                    "a": "1.1",
                    "B": "2",
                    "A": "3",
                    "u": 11,
                    "E": 1_700_000_000_000,
                }
            elif name == "kline_socket":
                yield {
                    "k": {
                        "t": 1_700_000_000_000,
                        "T": 1_700_000_060_000,
                        "o": "1.0",
                        "h": "1.2",
                        "l": "0.9",
                        "c": "1.1",
                        "v": "5",
                        "i": "1m",
                        "x": True,
                    }
                }
            else:
                yield {
                    "E": 1_700_000_000_000,
                    "U": 11,
                    "u": 12,
                    "b": [["1.0", "1"]],
                    "a": [["1.1", "1"]],
                }

    adapter = _implementation_adapter(_StreamTransport())

    async def exercise() -> None:
        await adapter.connect()
        quote_result = await adapter.subscribe_quotes(("BTCUSDT",))
        assert quote_result.data is not None
        quote = await anext(quote_result.data.events())
        assert str(quote.bid) == "1.0"
        await adapter.unsubscribe(quote_result.data.info.subscription_id)

        bar_result = await adapter.subscribe_bars(("BTCUSDT",), "1m")
        assert bar_result.data is not None
        bar = await anext(bar_result.data.events())
        assert bar.is_closed
        await adapter.unsubscribe(bar_result.data.info.subscription_id)

        depth_result = await adapter.subscribe_order_book(("BTCUSDT",), depth=5)
        assert depth_result.data is not None
        snapshot = await anext(depth_result.data.events())
        assert snapshot.is_snapshot
        assert snapshot.last_sequence_id == 10
        listed = await adapter.list_subscriptions()
        assert listed.data is not None
        assert len(listed.data) == 1
        await adapter.unsubscribe(depth_result.data.info.subscription_id)

    asyncio.run(exercise())
