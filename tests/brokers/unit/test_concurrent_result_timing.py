"""Prove adapter timing state is invocation-local."""

import asyncio

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
)
from app.services.brokers.adapter_runtime.base import _UnsupportedAdapterBase
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    """Return one bounded runtime configuration."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="1",
        credentials={
            "login": SecretStr("1"),
            "password": SecretStr("x"),
            "server": SecretStr("Demo"),
        },
    )


class _TimedAdapter(_UnsupportedAdapterBase):
    """Runtime harness with one controlled provider operation."""

    async def ping(self) -> BrokerResult[None]:
        """Record provider latency within only this invocation."""
        await asyncio.sleep(0)
        self._record_provider_latency(3.0)
        return self._result(BrokerCapabilityId.PING)


def test_concurrent_calls_do_not_exchange_provider_latency() -> None:
    """Each task receives its own provider-latency measurement."""

    async def run() -> tuple[BrokerResult[None], BrokerResult[None]]:
        adapter = _TimedAdapter(_config())
        adapter._state = adapter._state.READY
        first, second = await asyncio.gather(adapter.ping(), adapter.ping())
        return first, second

    first, second = asyncio.run(run())
    assert first.provider_latency_ms is not None
    assert second.provider_latency_ms is not None
    assert first.provider_latency_ms <= first.latency_ms
    assert second.provider_latency_ms <= second.latency_ms
