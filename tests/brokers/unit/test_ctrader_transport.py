"""cTrader transport correlation and session tests using an injected sender."""

import asyncio

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader_session.transport import _CTraderTransport


class _Response:
    def __init__(self, client_msg_id: str | None = None) -> None:
        self.clientMsgId = client_msg_id


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
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


def test_transport_requires_connection_before_sending() -> None:
    """Sending before a verified session fails closed."""
    transport = _CTraderTransport(_config(), sender=lambda _request: _Response())

    async def exercise() -> None:
        with pytest.raises(ConnectionError, match="not connected"):
            await transport.send(object(), _Response)

    asyncio.run(exercise())


def test_transport_rejects_unexpected_response_type() -> None:
    """A response of the wrong protobuf type is never accepted."""

    async def sender(_request: object) -> object:
        return "not-a-response"

    transport = _CTraderTransport(_config(), sender=sender)

    async def exercise() -> None:
        await transport.connect()
        with pytest.raises(ValueError, match="unexpected cTrader response type"):
            await transport.send(object(), _Response)

    asyncio.run(exercise())


def test_transport_rejects_native_id_mismatch() -> None:
    """A mismatched native correlation ID is never silently accepted."""

    async def sender(_request: object) -> object:
        return _Response(client_msg_id="other-id")

    transport = _CTraderTransport(_config(), sender=sender)

    async def exercise() -> None:
        await transport.connect()
        with pytest.raises(ValueError, match="native request ID mismatch"):
            await transport.send(object(), _Response, request_id="expected-id")

    asyncio.run(exercise())


def test_transport_serializes_same_response_type_requests() -> None:
    """Concurrent same-type requests never cross-correlate a response."""
    order: list[str] = []

    async def sender(request: object) -> object:
        order.append(f"start-{request}")
        await asyncio.sleep(0.02)
        order.append(f"end-{request}")
        return _Response()

    transport = _CTraderTransport(_config(), sender=sender)

    async def exercise() -> None:
        await transport.connect()
        await asyncio.gather(
            transport.send("a", _Response),
            transport.send("b", _Response),
        )

    asyncio.run(exercise())
    assert order == ["start-a", "end-a", "start-b", "end-b"]


def test_transport_close_requires_reconnect() -> None:
    """Closing the session blocks further sends until reconnected."""

    async def sender(_request: object) -> object:
        return _Response()

    transport = _CTraderTransport(_config(), sender=sender)

    async def exercise() -> None:
        await transport.connect()
        await transport.close()
        with pytest.raises(ConnectionError):
            await transport.send(object(), _Response)

    asyncio.run(exercise())
