"""Deterministic fake adapter tests (FR-BRK-109)."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import (
    BrokerAdapter,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerQuote,
)
from app.services.brokers.registry import get_broker_capability_catalogue
from app.services.brokers.testing import FakeBrokerAdapter

_BUFFER_SIZE = 2
_MUTATIONS = {
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.MODIFY_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.MODIFY_POSITION,
    BrokerCapabilityId.CLOSE_POSITION,
    BrokerCapabilityId.REPLACE_ORDER,
}


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=_BUFFER_SIZE,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
    )


def _capabilities(
    availability: str = "AVAILABLE",
) -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability=("UNAVAILABLE" if operation in _MUTATIONS else availability),
            access_mode="WRITE" if operation in _MUTATIONS else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


def _fake(**kwargs: object) -> FakeBrokerAdapter:
    return FakeBrokerAdapter(
        _config(),
        _capabilities(),
        **kwargs,  # type: ignore[arg-type]
    )


def _quote() -> BrokerQuote:
    """Return a valid deterministic quote fixture."""
    return BrokerQuote(
        symbol="A",
        price_unit="USD",
        quantity_unit="units",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(1),
        ask=Decimal(2),
    )


def test_fake_adapter_implements_complete_protocol() -> None:
    """The fake structurally exposes every adapter operation."""
    fake = _fake()
    assert isinstance(fake, BrokerAdapter)
    assert all(hasattr(fake, operation.value) for operation in BrokerCapabilityId)


def test_fake_adapter_error_injection() -> None:
    """One injected failure affects only the selected operation."""

    async def exercise() -> None:
        fake = _fake(fixtures={BrokerCapabilityId.GET_QUOTE: _quote()})
        await fake.connect()
        fake.inject_error(
            BrokerCapabilityId.GET_QUOTE,
            BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
        )
        result = await fake.get_quote("A")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_TIMEOUT

    asyncio.run(exercise())


def test_fake_adapter_error_injection_is_reversible_and_isolated() -> None:
    """Clearing one injected failure restores only that operation."""

    async def exercise() -> None:
        fake = _fake(
            fixtures={
                BrokerCapabilityId.GET_QUOTE: _quote(),
                BrokerCapabilityId.GET_SPREAD: Decimal(1),
            }
        )
        await fake.connect()
        fake.inject_error(
            BrokerCapabilityId.GET_QUOTE,
            BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
        )
        assert (await fake.get_spread("A")).data == Decimal(1)
        fake.inject_error(BrokerCapabilityId.GET_QUOTE, None)
        assert isinstance((await fake.get_quote("A")).data, BrokerQuote)

    asyncio.run(exercise())


def test_fixture_cannot_bypass_declared_unavailable_capability() -> None:
    """A fixture never overrides a capability declared UNAVAILABLE."""

    async def exercise() -> None:
        fake = FakeBrokerAdapter(
            _config(),
            fixtures={BrokerCapabilityId.GET_QUOTE: _quote()},
        )
        result = await fake.get_quote("A")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())


def test_injected_error_cannot_bypass_declared_unavailable_capability() -> None:
    """Error injection never re-enables a capability declared UNAVAILABLE."""

    async def exercise() -> None:
        fake = FakeBrokerAdapter(_config())
        fake.inject_error(
            BrokerCapabilityId.GET_QUOTE,
            BrokerError(code=BrokerErrorCode.BROKER_TIMEOUT, message="timeout"),
        )
        result = await fake.get_quote("A")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())


def test_fake_adapter_honours_the_genuine_provider_catalogue() -> None:
    """Supplied the real Yahoo catalogue, unreleased reads stay fail-closed."""

    async def exercise() -> None:
        capabilities = {
            entry.capability: entry
            for entry in get_broker_capability_catalogue()[BrokerId.YAHOO]
        }
        fake = FakeBrokerAdapter(
            _config(),
            capabilities,
            fixtures={BrokerCapabilityId.GET_QUOTE: _quote()},
        )
        result = await fake.get_quote("A")
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())


def test_fake_subscription_is_bounded_and_terminates_on_overflow() -> None:
    """The fake enforces the configured stream buffer exactly as real adapters."""

    async def exercise() -> None:
        fake = _fake()
        await fake.connect()
        opened = await fake.subscribe_quotes(("EURUSD",))
        assert opened.is_success
        handle = opened.data
        assert handle is not None
        assert handle.info.buffer_size == _BUFFER_SIZE

        for index in range(_BUFFER_SIZE):
            assert await fake.publish(handle.info.subscription_id, index)
        assert not await fake.publish(handle.info.subscription_id, _BUFFER_SIZE)

        assert handle.info.resynchronization_required
        assert not handle.info.active
        events = [event async for event in handle.events()]
        assert isinstance(events[-1], BrokerError)
        assert events[-1].code == BrokerErrorCode.BROKER_BACKPRESSURE

    asyncio.run(exercise())


def test_fake_subscriptions_do_not_leak_between_instances() -> None:
    """Two fakes never observe each other's subscriptions."""

    async def exercise() -> None:
        first = _fake()
        second = _fake()
        await first.connect()
        await second.connect()
        await first.subscribe_quotes(("EURUSD",))
        assert len((await first.list_subscriptions()).data or ()) == 1
        assert len((await second.list_subscriptions()).data or ()) == 0

    asyncio.run(exercise())


def test_unknown_unsubscribe_is_isolated_and_explicit() -> None:
    """An unowned subscription ID never disturbs an owned stream."""

    async def exercise() -> None:
        fake = _fake()
        await fake.connect()
        opened = await fake.subscribe_quotes(("EURUSD",))
        assert opened.data is not None

        unknown = await fake.unsubscribe("evt-does-not-exist")
        assert unknown.error is not None
        assert unknown.error.code == BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND
        assert opened.data.info.active

        owned = await fake.unsubscribe(opened.data.info.subscription_id)
        assert owned.is_success
        assert not opened.data.info.active

    asyncio.run(exercise())
