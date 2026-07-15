"""Demonstrate the MT5 adapter against a real configured demo account.

Reads real ``MT5_*`` credentials from the repository ``.env`` (or the
process environment) through the shared ``app.utils.settings`` dotenv/
credential helpers, then performs a genuine terminal connection, account
read, and disconnect. Prints exactly what the account returns rather than a
scripted fixture. If no demo credentials are configured, this prints a clear
notice and exits without fabricating success.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from app.utils import load_dotenv_file, resolve_named_secrets

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_LOGIN_KEY = "MT5_LOGIN"


def _environment() -> dict[str, str]:
    values = load_dotenv_file(_ENV_PATH)
    values.update(os.environ)
    return values


def _mt5_credentials() -> dict[str, str] | None:
    values = _environment()
    if values.get("MT5_ENABLED", "").casefold() != "true":
        return None
    required = (_LOGIN_KEY, "MT5_PASSWORD", "MT5_SERVER")
    if not all(values.get(key) for key in required):
        return None
    return values


def _config(values: dict[str, str]) -> BrokerConnectionConfig:
    credentials = resolve_named_secrets(
        {
            "login": _LOGIN_KEY,
            "password": "MT5_PASSWORD",
            "server": "MT5_SERVER",
            "terminal_path": "MT5_TERMINAL_PATH",
        },
        values,
    )
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=(
            BrokerEnvironment.LIVE
            if values.get("MT5_ENVIRONMENT", "demo").casefold() == "live"
            else BrokerEnvironment.DEMO
        ),
        provider_enabled=True,
        connect_timeout_sec=15,
        request_timeout_sec=15,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=3,
        circuit_recovery_timeout_sec=5,
        circuit_half_open_max_calls=1,
        account_reference=values[_LOGIN_KEY],
        credentials=credentials,
    )


def example_registry_adapter_connects_to_a_real_demo_account(
    values: dict[str, str],
) -> None:
    """Connect and disconnect a registry-created adapter against a real terminal."""
    print("\n1. Registry adapter connects to a real MT5 demo terminal")

    async def exercise() -> None:
        adapter = create_broker_adapter(BrokerId.MT5, _config(values)).data
        if adapter is None:
            raise AssertionError("registry did not return an adapter")
        connected = await adapter.connect()
        print("connect():", connected.status, connected.error)
        if not connected.is_success:
            raise AssertionError("real MT5 connect failed")
        status = await adapter.is_connected()
        print("is_connected():", status.data)
        await adapter.disconnect()

    asyncio.run(exercise())


def example_adapter_maps_real_account_state(values: dict[str, str]) -> None:
    """Map a genuine demo account into the canonical account DTO."""
    print("\n2. Adapter maps real account state")
    capabilities = {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="REAL_DEMO_USAGE_EXAMPLE",
        )
        for operation in BrokerCapabilityId
    }
    adapter = MT5BrokerAdapter(_config(values), capabilities)

    async def exercise() -> None:
        connected = await adapter.connect()
        if not connected.is_success:
            raise AssertionError("real MT5 connect failed")
        account = await adapter.get_account_info()
        print(
            "Account:",
            "id=",
            account.data.account_id if account.data else None,
            "currency=",
            account.data.currency if account.data else None,
            "balance=",
            account.data.balance if account.data else None,
        )
        if not account.is_success or account.data is None:
            raise AssertionError("real MT5 account read failed")
        await adapter.disconnect()

    asyncio.run(exercise())


if __name__ == "__main__":
    demo_values = _mt5_credentials()
    if demo_values is None:
        print("MT5 demo credentials are not configured in .env — skipping.")
    else:
        example_registry_adapter_connects_to_a_real_demo_account(demo_values)
        example_adapter_maps_real_account_state(demo_values)
