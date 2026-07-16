"""cTrader concurrent-request correlation integration test (WF-BRK-007)."""

import asyncio

from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader.transport import _CTraderTransport


class _Response:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.clientMsgId = None


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


def test_ctrader_does_not_cross_correlate_concurrent_requests() -> None:
    """Two concurrent same-type requests each receive their own response."""

    async def sender(request: object) -> object:
        delay = 0.03 if request == "slow" else 0.0
        await asyncio.sleep(delay)
        return _Response(str(request))

    transport = _CTraderTransport(_config(), sender=sender)

    async def exercise() -> tuple[object, object]:
        await transport.connect()
        slow, fast = await asyncio.gather(
            transport.send("slow", _Response),
            transport.send("fast", _Response),
        )
        return slow, fast

    slow_response, fast_response = asyncio.run(exercise())
    assert slow_response.tag == "slow"
    assert fast_response.tag == "fast"
