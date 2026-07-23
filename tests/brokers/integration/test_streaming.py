"""WF-BRK-006: stream provider and connection events.

The workflow is driven through the genuine `BinanceBrokerAdapter`, so the
adapter-scoped subscription is created by `subscribe_quotes()`, bounded by the
configured `stream_buffer_size`, mapped by `binance/mapping.py`, and released by
`unsubscribe()`. The private runtime handle is covered separately by
`tests/brokers/unit/test_subscription.py`.
"""

import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerQuote,
)
from app.services.brokers.binance.adapter import BinanceBrokerAdapter
from pydantic import SecretStr

_BUFFER_SIZE = 2
_SYMBOL = "BTCUSDT"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.BINANCE_SPOT,
        environment=BrokerEnvironment.TESTNET,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=_BUFFER_SIZE,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={
            "api_key": SecretStr("offline-key"),
            "api_secret": SecretStr("offline-secret"),
        },
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


class _StreamTransport:
    """Emit a bounded number of genuine-shaped provider quote messages."""

    def __init__(self, message_count: int = 1) -> None:
        self._message_count = message_count
        self.closed = False
        self.streamed: list[str] = []

    async def connect(self) -> bool:
        return True

    async def call(self, name: str, **kwargs: object) -> object:
        del kwargs
        if name in {"ping", "get_server_time"}:
            return {"serverTime": 1_700_000_000_000}
        return None

    async def stream(
        self, name: str, **kwargs: object
    ) -> AsyncIterator[dict[str, object]]:
        del kwargs
        self.streamed.append(name)
        for index in range(self._message_count):
            yield {
                "b": f"1.{index}",
                "a": "1.5",
                "B": "2",
                "A": "3",
                "u": 11 + index,
                "E": 1_700_000_000_000,
            }

    async def close(self) -> None:
        self.closed = True


def test_streaming_delivers_canonical_provider_events_in_order() -> None:
    """A subscription yields canonical quotes mapped from provider messages."""
    transport = _StreamTransport(message_count=1)
    adapter = BinanceBrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        opened = await adapter.subscribe_quotes((_SYMBOL,))
        assert opened.is_success, opened.error
        handle = opened.data
        assert handle is not None

        # Metadata is adapter-scoped and bounded by the configured buffer.
        assert handle.info.capability == BrokerCapabilityId.SUBSCRIBE_QUOTES
        assert handle.info.symbols == (_SYMBOL,)
        assert handle.info.buffer_size == _BUFFER_SIZE

        event = await asyncio.wait_for(anext(handle.events()), timeout=1)
        assert isinstance(event, BrokerQuote)
        assert event.bid == Decimal("1.0")
        assert event.ask == Decimal("1.5")
        assert transport.streamed  # a genuine provider stream was opened

        listed = await adapter.list_subscriptions()
        assert listed.data is not None
        assert len(listed.data) == 1

        await adapter.unsubscribe(handle.info.subscription_id)

    asyncio.run(exercise())


def test_streaming_reports_backpressure_and_resync() -> None:
    """Buffer overflow terminates the stream and requires resynchronization."""
    transport = _StreamTransport(message_count=_BUFFER_SIZE + 2)
    adapter = BinanceBrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        opened = await adapter.subscribe_quotes((_SYMBOL,))
        handle = opened.data
        assert handle is not None

        # Let the producer outpace the (absent) consumer.
        for _ in range(20):
            await asyncio.sleep(0)
        events: list[object] = []
        async for event in handle.events():
            events.append(event)
            if isinstance(event, BrokerError):
                break

        terminal = events[-1]
        assert isinstance(terminal, BrokerError)
        assert terminal.code == BrokerErrorCode.BROKER_BACKPRESSURE
        assert handle.info.resynchronization_required
        assert not handle.info.active

    asyncio.run(exercise())


def test_unknown_subscription_never_affects_others() -> None:
    """Unsubscribing an unowned ID never disturbs an owned subscription."""
    adapter = BinanceBrokerAdapter(
        _config(), _capabilities(), transport=_StreamTransport()
    )

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        opened = await adapter.subscribe_quotes((_SYMBOL,))
        handle = opened.data
        assert handle is not None

        unknown = await adapter.unsubscribe("evt-does-not-exist")
        assert not unknown.is_success
        assert unknown.error is not None
        assert unknown.error.code == BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND

        listed = await adapter.list_subscriptions()
        assert listed.data is not None
        assert len(listed.data) == 1

        await adapter.unsubscribe(handle.info.subscription_id)

    asyncio.run(exercise())


def test_disconnect_terminates_every_owned_subscription() -> None:
    """Disconnect closes owned streams; silent data loss never occurs."""
    adapter = BinanceBrokerAdapter(
        _config(), _capabilities(), transport=_StreamTransport()
    )

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        opened = await adapter.subscribe_quotes((_SYMBOL,))
        handle = opened.data
        assert handle is not None

        await adapter.disconnect()
        assert not handle.info.active

        listed = await adapter.list_subscriptions()
        assert listed.data is not None
        assert len(listed.data) == 0

    asyncio.run(exercise())


def test_subscriptions_do_not_leak_between_adapters() -> None:
    """Independent adapters never observe each other's subscriptions."""

    async def exercise() -> None:
        first = BinanceBrokerAdapter(
            _config(), _capabilities(), transport=_StreamTransport()
        )
        second = BinanceBrokerAdapter(
            _config(), _capabilities(), transport=_StreamTransport()
        )
        assert (await first.connect()).is_success
        assert (await second.connect()).is_success
        await first.subscribe_quotes((_SYMBOL,))

        first_listed = await first.list_subscriptions()
        second_listed = await second.list_subscriptions()
        assert first_listed.data is not None
        assert second_listed.data is not None
        assert len(first_listed.data) == 1
        assert len(second_listed.data) == 0

    asyncio.run(exercise())
