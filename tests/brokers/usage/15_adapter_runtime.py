"""FEAT-BRK-15: exercise adapter-runtime lifecycle through public APIs."""

import asyncio

import _support  # noqa: F401
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    """Build one bounded demo configuration for runtime evidence.

    Returns:
        Immutable offline MT5 configuration.
    """
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1.0,
        request_timeout_sec=1.0,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1.0,
        circuit_half_open_max_calls=1,
        account_reference="100001",
        credentials={
            "login": SecretStr("100001"),
            "password": SecretStr("offline"),
            "server": SecretStr("Offline-Demo"),
        },
    )


async def _run() -> None:
    """Exercise lifecycle and invocation-local result wrapping."""
    adapter = FakeBrokerAdapter(_config())
    connected = await adapter.connect()
    status = await adapter.get_connection_status()
    disconnected = await adapter.disconnect()
    print("connect", connected.status, connected.latency_ms)
    print("status", status.data.state if status.data else None)
    print("disconnect", disconnected.status)


def main() -> None:
    """Run the standalone runtime usage program."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
