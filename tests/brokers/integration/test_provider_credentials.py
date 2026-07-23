"""Credential-gated live provider evidence loaded through typed settings."""

import asyncio
import sys
from collections.abc import Iterator

import pytest
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
    create_broker_adapter,
)

from tests.brokers.provider_settings import ProviderTestSettings


@pytest.fixture(autouse=True)
def _restore_sdk_import_isolation() -> Iterator[None]:
    """Undo this module's real ``MetaTrader5`` import for later tests."""
    was_imported = "MetaTrader5" in sys.modules
    yield
    if not was_imported:
        sys.modules.pop("MetaTrader5", None)


def test_mt5_demo_credential_gated_connection() -> None:
    """A configured MT5 demo credential set verifies a genuine session."""
    settings = ProviderTestSettings()
    if (
        not settings.mt5_enabled
        or settings.mt5_login is None
        or settings.mt5_password is None
        or settings.mt5_server is None
    ):
        pytest.skip("MT5 demo credentials are not configured")
    credentials = {
        "login": settings.mt5_login,
        "password": settings.mt5_password,
        "server": settings.mt5_server,
    }
    if settings.mt5_terminal_path is not None:
        credentials["terminal_path"] = settings.mt5_terminal_path
    config = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
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
    created = create_broker_adapter(BrokerId.MT5, config)
    assert created.is_success
    adapter = created.data
    assert adapter is not None

    async def exercise() -> None:
        """Connect and disconnect one genuine MT5 session."""
        result = await adapter.connect()
        assert result.is_success, result.error
        await adapter.disconnect()

    asyncio.run(exercise())


def test_ctrader_demo_credentials_validate_without_a_network_transport() -> None:
    """Configured cTrader credentials pass construction-time validation."""
    settings = ProviderTestSettings()
    if (
        not settings.ctrader_enabled
        or settings.ctrader_account_id is None
        or settings.ctrader_client_id is None
        or settings.ctrader_client_secret is None
        or settings.ctrader_access_token is None
    ):
        pytest.skip("cTrader demo credentials are not configured")
    credentials = {
        "client_id": settings.ctrader_client_id,
        "client_secret": settings.ctrader_client_secret,
        "access_token": settings.ctrader_access_token,
        "account_id": settings.ctrader_account_id,
    }
    config = BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
        environment=BrokerEnvironment.DEMO,
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
    created = create_broker_adapter(BrokerId.CTRADER, config)
    assert created.is_success
    adapter = created.data
    assert adapter is not None
