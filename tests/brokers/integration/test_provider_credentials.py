"""Credential-gated live provider evidence.

Each test is skipped unless its exact profile's credential marker and
environment are present in ``.env`` (or the process environment). A skip is
not release evidence: it only means this run could not exercise a real
provider connection, never that the capability is verified available.

Importing the real ``MetaTrader5`` SDK here is unavoidable for a genuine
connection, so the MT5 test restores ``sys.modules`` afterward — other tests
in this package assert that an ordinary root import never eagerly loads a
provider SDK, and that assertion must hold regardless of test run order.
"""

import asyncio
import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from app.services.brokers.registry.catalogue import get_broker_capability_catalogue
from app.utils import load_dotenv_file, resolve_named_secrets


@pytest.fixture(autouse=True)
def _restore_sdk_import_isolation() -> Iterator[None]:
    """Undo this module's real ``MetaTrader5`` import for later tests."""
    was_imported = "MetaTrader5" in sys.modules
    yield
    if not was_imported:
        sys.modules.pop("MetaTrader5", None)


_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def _environment() -> dict[str, str]:
    values = load_dotenv_file(_ENV_PATH)
    values.update(os.environ)
    return values


def test_mt5_demo_credential_gated_connection() -> None:
    """A configured MT5 demo credential set verifies a genuine session."""
    values = _environment()
    if values.get("MT5_ENABLED", "").casefold() != "true" or not all(
        values.get(key) for key in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER")
    ):
        pytest.skip("MT5 demo credentials are not configured")

    credentials = resolve_named_secrets(
        {
            "login": "MT5_LOGIN",
            "password": "MT5_PASSWORD",
            "server": "MT5_SERVER",
            "terminal_path": "MT5_TERMINAL_PATH",
        },
        values,
    )
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
        account_reference=values["MT5_LOGIN"],
        credentials=credentials,
    )
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.MT5]
    }
    adapter = MT5BrokerAdapter(config, capabilities)

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success, result.error
        await adapter.disconnect()

    asyncio.run(exercise())


def test_ctrader_demo_credentials_validate_without_a_network_transport() -> None:
    """Configured cTrader demo credentials pass construction-time validation.

    No live handshake is attempted: ``ctrader/transport.py`` has no concrete
    network client yet (see the cTrader usage examples for the full
    explanation). This still counts as genuine credential-gated evidence for
    the credential/config validation this domain owns.
    """
    values = _environment()
    if values.get("CTRADER_ENABLED", "").casefold() != "true" or not all(
        values.get(key)
        for key in (
            "CTRADER_ACCOUNT_ID",
            "CTRADER_CLIENT_ID",
            "CTRADER_CLIENT_SECRET",
            "CTRADER_ACCESS_TOKEN",
        )
    ):
        pytest.skip("cTrader demo credentials are not configured")

    credentials = resolve_named_secrets(
        {
            "client_id": "CTRADER_CLIENT_ID",
            "client_secret": "CTRADER_CLIENT_SECRET",
            "access_token": "CTRADER_ACCESS_TOKEN",
            "account_id": "CTRADER_ACCOUNT_ID",
        },
        values,
    )
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
        account_reference=values["CTRADER_ACCOUNT_ID"],
        credentials=credentials,
    )
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.CTRADER]
    }
    adapter = CTraderBrokerAdapter(config, capabilities)
    assert adapter is not None
