"""Demonstrate the MT5 adapter against a real configured demo account.

Typed shared settings load the real ``MT5_*`` profile. The examples perform a
genuine terminal connection, account read, and disconnect. If the profile is
incomplete, the script reports a skip and never fabricates success.
"""

import asyncio
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
from app.utils import logger

from tests.brokers.provider_settings import ProviderTestSettings


def _mt5_credentials() -> ProviderTestSettings | None:
    """Return typed MT5 settings only when the required profile is complete."""
    logger.info("Checking the typed MT5 demo settings profile")
    settings = ProviderTestSettings()
    if not settings.mt5_enabled:
        return None
    if (
        settings.mt5_login is None
        or settings.mt5_password is None
        or settings.mt5_server is None
    ):
        return None
    return settings


def _config(settings: ProviderTestSettings) -> BrokerConnectionConfig:
    """Build a validated MT5 config without exposing credential values."""
    logger.info("Building the typed MT5 connection configuration")
    if (
        settings.mt5_login is None
        or settings.mt5_password is None
        or settings.mt5_server is None
    ):
        raise ValueError("MT5 settings are incomplete")
    credentials = {
        "login": settings.mt5_login,
        "password": settings.mt5_password,
        "server": settings.mt5_server,
    }
    if settings.mt5_terminal_path is not None:
        credentials["terminal_path"] = settings.mt5_terminal_path
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=(
            BrokerEnvironment.LIVE
            if settings.mt5_environment == "live"
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
        account_reference=settings.mt5_login.get_secret_value(),
        credentials=credentials,
    )


def example_registry_adapter_connects_to_a_real_demo_account(
    settings: ProviderTestSettings,
) -> None:
    """Connect and disconnect a registry-created adapter against a real terminal."""
    logger.info("Example 1: registry adapter connects to a real MT5 demo terminal")

    async def exercise() -> None:
        """Exercise one genuine registry-created MT5 connection lifecycle."""
        logger.info("Connecting the registry-created MT5 adapter")
        adapter = create_broker_adapter(BrokerId.MT5, _config(settings)).data
        if adapter is None:
            raise AssertionError("registry did not return an adapter")
        connected = await adapter.connect()
        logger.info("connect() status=%s error=%s", connected.status, connected.error)
        if not connected.is_success:
            raise AssertionError("real MT5 connect failed")
        status = await adapter.is_connected()
        logger.info("is_connected()=%s", status.data)
        await adapter.disconnect()

    asyncio.run(exercise())


def example_adapter_maps_real_account_state(settings: ProviderTestSettings) -> None:
    """Map a genuine demo account into the canonical account DTO."""
    logger.info("Example 2: adapter maps real account state")
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
    adapter = MT5BrokerAdapter(_config(settings), capabilities)

    async def exercise() -> None:
        """Connect, read the real account DTO, and disconnect."""
        logger.info("Reading the genuine MT5 account state")
        connected = await adapter.connect()
        if not connected.is_success:
            raise AssertionError("real MT5 connect failed")
        account = await adapter.get_account_info()
        logger.info(
            "Account id=%s currency=%s balance=%s",
            account.data.account_id if account.data else None,
            account.data.currency if account.data else None,
            account.data.balance if account.data else None,
        )
        if not account.is_success or account.data is None:
            raise AssertionError("real MT5 account read failed")
        await adapter.disconnect()

    asyncio.run(exercise())


if __name__ == "__main__":
    demo_settings = _mt5_credentials()
    if demo_settings is None:
        logger.info("MT5 demo credentials are not configured; skipping")
    else:
        example_registry_adapter_connects_to_a_real_demo_account(demo_settings)
        example_adapter_maps_real_account_state(demo_settings)
