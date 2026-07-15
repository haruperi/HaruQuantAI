"""Demonstrate cTrader adapter behavior with real configured credentials.

Typed shared settings load the real ``CTRADER_*`` profile. The current adapter
has no concrete network sender, so this honestly demonstrates construction and
the genuine fail-closed connection outcome without fabricating a handshake.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter
from app.services.brokers.registry.catalogue import get_broker_capability_catalogue
from app.utils import logger

from tests.brokers.provider_settings import ProviderTestSettings


def _ctrader_credentials() -> ProviderTestSettings | None:
    """Return typed cTrader settings only when the profile is complete."""
    logger.info("Checking the typed cTrader demo settings profile")
    settings = ProviderTestSettings()
    if not settings.ctrader_enabled:
        return None
    if any(
        value is None
        for value in (
            settings.ctrader_account_id,
            settings.ctrader_client_id,
            settings.ctrader_client_secret,
            settings.ctrader_access_token,
        )
    ):
        return None
    return settings


def _config(settings: ProviderTestSettings) -> BrokerConnectionConfig:
    """Build a validated cTrader config without exposing credential values."""
    logger.info("Building the typed cTrader connection configuration")
    if (
        settings.ctrader_account_id is None
        or settings.ctrader_client_id is None
        or settings.ctrader_client_secret is None
        or settings.ctrader_access_token is None
    ):
        raise ValueError("cTrader settings are incomplete")
    credentials = {
        "client_id": settings.ctrader_client_id,
        "client_secret": settings.ctrader_client_secret,
        "access_token": settings.ctrader_access_token,
        "account_id": settings.ctrader_account_id,
    }
    return BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
        environment=(
            BrokerEnvironment.LIVE
            if settings.ctrader_environment == "live"
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
        account_reference=settings.ctrader_account_id.get_secret_value(),
        credentials=credentials,
    )


def example_real_demo_credentials_build_a_valid_adapter(
    settings: ProviderTestSettings,
) -> None:
    """Prove real demo credentials pass construction-time validation."""
    logger.info("Example 1: real cTrader credentials build a valid adapter")
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.CTRADER]
    }
    adapter = CTraderBrokerAdapter(_config(settings), capabilities)
    logger.info("Adapter constructed=%s", type(adapter).__name__)


def example_connect_reports_the_real_missing_transport_outcome(
    settings: ProviderTestSettings,
) -> None:
    """Attempt a genuine connect and report the real fail-closed outcome."""
    logger.info("Example 2: connect is genuinely attempted without fake success")
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.CTRADER]
    }
    adapter = CTraderBrokerAdapter(_config(settings), capabilities)

    async def exercise() -> None:
        """Run the actual cTrader connection boundary once."""
        logger.info("Calling the cTrader adapter connection boundary")
        result = await adapter.connect()
        logger.info("connect() status=%s error=%s", result.status, result.error)

    asyncio.run(exercise())


if __name__ == "__main__":
    demo_settings = _ctrader_credentials()
    if demo_settings is None:
        logger.info("cTrader demo credentials are not configured; skipping")
    else:
        example_real_demo_credentials_build_a_valid_adapter(demo_settings)
        example_connect_reports_the_real_missing_transport_outcome(demo_settings)
