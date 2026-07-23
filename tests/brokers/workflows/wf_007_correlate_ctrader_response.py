"""WF-BRK-007: correlate cTrader response (cTrader-specific workflow)."""

import asyncio

import _bootstrap  # noqa: F401
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)
from pydantic import SecretStr
from wf_support import build_mt5_connection_config


def _ctrader_config() -> BrokerConnectionConfig:
    """Build an isolated cTrader config for correlation demonstration.

    Returns:
        Bounded demo cTrader configuration.
    """
    return BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
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
            "client_id": SecretStr("offline-client"),
            "client_secret": SecretStr("offline-secret"),
            "access_token": SecretStr("offline-token"),
            "account_id": SecretStr("100001"),
        },
    )


async def _run() -> None:
    """Run two boundary calls that depend on cTrader response correlation internals."""
    # Ensure workflow settings bootstrap runs and validates .env path discovery
    # through ``from app.utils import settings``.
    build_mt5_connection_config()

    created = create_broker_adapter(BrokerId.CTRADER, _ctrader_config())
    if created.data is None:
        print("WF-BRK-007: adapter creation failed")
        return

    adapter = created.data
    status_one = await adapter.get_connection_status()
    status_two = await adapter.get_connection_status()

    state_one = status_one.data.state if status_one.data is not None else None
    state_two = status_two.data.state if status_two.data is not None else None
    print("WF-BRK-007: first status", state_one)
    print("WF-BRK-007: second status", state_two)
    print(
        "WF-BRK-007: both calls resolved to same state",
        state_one == state_two and state_one == BrokerConnectionState.DISCONNECTED,
    )


def main() -> None:
    """Execute WF-BRK-007 demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
