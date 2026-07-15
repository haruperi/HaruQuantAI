"""Demonstrate the cTrader adapter against real configured demo credentials.

Reads real ``CTRADER_*`` credentials from the repository ``.env`` (or the
process environment). Unlike MT5, ``ctrader/transport.py`` has no concrete
network implementation yet: ``_CTraderTransport`` only accepts an injected
``sender`` callable, and no Twisted/reactor-based client to Spotware's
servers exists anywhere in this codebase. This script is honest about that:
it proves the real credentials construct a valid, validated adapter, then
genuinely attempts ``connect()`` and prints the real (fail-closed) outcome —
it does not fabricate a live handshake.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import BrokerConnectionConfig, BrokerEnvironment, BrokerId
from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter
from app.services.brokers.registry.catalogue import get_broker_capability_catalogue
from app.utils import load_dotenv_file, resolve_named_secrets

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_ACCOUNT_ID_KEY = "CTRADER_ACCOUNT_ID"


def _environment() -> dict[str, str]:
    values = load_dotenv_file(_ENV_PATH)
    values.update(os.environ)
    return values


def _ctrader_credentials() -> dict[str, str] | None:
    values = _environment()
    if values.get("CTRADER_ENABLED", "").casefold() != "true":
        return None
    required = (
        _ACCOUNT_ID_KEY,
        "CTRADER_CLIENT_ID",
        "CTRADER_CLIENT_SECRET",
        "CTRADER_ACCESS_TOKEN",
    )
    if not all(values.get(key) for key in required):
        return None
    return values


def _config(values: dict[str, str]) -> BrokerConnectionConfig:
    credentials = resolve_named_secrets(
        {
            "client_id": "CTRADER_CLIENT_ID",
            "client_secret": "CTRADER_CLIENT_SECRET",
            "access_token": "CTRADER_ACCESS_TOKEN",
            "account_id": _ACCOUNT_ID_KEY,
        },
        values,
    )
    return BrokerConnectionConfig(
        broker_id=BrokerId.CTRADER,
        environment=(
            BrokerEnvironment.LIVE
            if values.get("CTRADER_ENVIRONMENT", "demo").casefold() == "live"
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
        account_reference=values[_ACCOUNT_ID_KEY],
        credentials=credentials,
    )


def example_real_demo_credentials_build_a_valid_adapter(values: dict[str, str]) -> None:
    """Real demo credentials pass construction-time validation."""
    print("\n1. Real cTrader demo credentials build a valid adapter")
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.CTRADER]
    }
    adapter = CTraderBrokerAdapter(_config(values), capabilities)
    print("Adapter constructed:", type(adapter).__name__)


def example_connect_reports_the_real_missing_transport_outcome(
    values: dict[str, str],
) -> None:
    """Attempt a genuine connect() and print the real fail-closed outcome."""
    print("\n2. connect() genuinely attempted (no fabricated success)")
    capabilities = {
        entry.capability: entry
        for entry in get_broker_capability_catalogue()[BrokerId.CTRADER]
    }
    adapter = CTraderBrokerAdapter(_config(values), capabilities)

    async def exercise() -> None:
        result = await adapter.connect()
        print("connect():", result.status, result.error)

    asyncio.run(exercise())


if __name__ == "__main__":
    demo_values = _ctrader_credentials()
    if demo_values is None:
        print("cTrader demo credentials are not configured in .env — skipping.")
    else:
        example_real_demo_credentials_build_a_valid_adapter(demo_values)
        example_connect_reports_the_real_missing_transport_outcome(demo_values)
