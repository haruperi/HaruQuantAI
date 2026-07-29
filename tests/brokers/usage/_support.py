"""Secret-safe support for genuine non-production Brokers usage programs."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import (
    create_broker_adapter,
)
from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.utils.responses.models import StandardResponse
from pydantic import SecretStr

from tests.brokers.provider_settings import ProviderTestSettings

_ResultT = TypeVar("_ResultT")
_NON_PRODUCTION_ENVIRONMENTS = frozenset(
    {
        BrokerEnvironment.DEMO,
        BrokerEnvironment.TESTNET,
        BrokerEnvironment.SANDBOX,
    }
)


class UsageEvidenceError(RuntimeError):
    """Report one bounded usage-evidence failure without sensitive values."""


def _require_enabled(provider: str, enabled: bool) -> None:
    """Require explicit provider enablement for genuine usage evidence."""
    if not enabled:
        raise UsageEvidenceError(f"{provider} usage requires provider enablement")


def _require_credentials(
    provider: str,
    values: dict[str, SecretStr | None],
) -> dict[str, SecretStr]:
    """Require a complete resolved credential set without exposing its values."""
    missing = tuple(name for name, value in values.items() if value is None)
    if missing:
        names = ", ".join(missing)
        raise UsageEvidenceError(f"{provider} usage credentials missing: {names}")
    return {name: value for name, value in values.items() if value is not None}


def _require_non_production(environment: BrokerEnvironment) -> None:
    """Block live-provider configuration before adapter construction."""
    if environment not in _NON_PRODUCTION_ENVIRONMENTS:
        raise UsageEvidenceError("broker usage programs reject live environments")


def config(broker_id: BrokerId) -> BrokerConnectionConfig:
    """Build one genuine enabled non-production provider configuration."""
    settings = ProviderTestSettings()
    credentials: dict[str, SecretStr] | None = None
    account_reference: str | None = None
    probe_symbol: str | None = None

    if broker_id == BrokerId.MT5:
        _require_enabled("MT5", settings.mt5_enabled)
        environment = BrokerEnvironment(settings.mt5_environment)
        credentials = _require_credentials(
            "MT5",
            {
                "login": settings.mt5_login,
                "password": settings.mt5_password,
                "server": settings.mt5_server,
            },
        )
        if settings.mt5_terminal_path is not None:
            credentials["terminal_path"] = settings.mt5_terminal_path
        account_reference = credentials["login"].get_secret_value()
    elif broker_id == BrokerId.CTRADER:
        _require_enabled("cTrader", settings.ctrader_enabled)
        environment = BrokerEnvironment(settings.ctrader_environment)
        credentials = _require_credentials(
            "cTrader",
            {
                "client_id": settings.ctrader_client_id,
                "client_secret": settings.ctrader_client_secret,
                "access_token": settings.ctrader_access_token,
                "account_id": settings.ctrader_account_id,
            },
        )
        account_reference = credentials["account_id"].get_secret_value()
    elif broker_id == BrokerId.BINANCE_SPOT:
        _require_enabled("Binance", settings.binance_enabled)
        environment = BrokerEnvironment(settings.binance_environment)
    elif broker_id == BrokerId.DUKASCOPY:
        _require_enabled("Dukascopy", settings.dukascopy_enabled)
        environment = BrokerEnvironment.SANDBOX
    elif broker_id == BrokerId.YAHOO:
        _require_enabled("Yahoo", settings.yahoo_enabled)
        environment = BrokerEnvironment.SANDBOX
        probe_symbol = "AAPL"
    else:
        raise UsageEvidenceError(
            f"{broker_id.value} has no approved standalone usage session"
        )

    _require_non_production(environment)
    return BrokerConnectionConfig(
        broker_id=broker_id,
        environment=environment,
        provider_enabled=True,
        connect_timeout_sec=15.0,
        request_timeout_sec=15.0,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1.0,
        circuit_half_open_max_calls=1,
        account_reference=account_reference,
        credentials=credentials,
        probe_symbol=probe_symbol,
    )


def create_real_adapter(broker_id: BrokerId) -> BrokerAdapter:
    """Create one genuine disconnected adapter through the public registry."""
    created = create_broker_adapter(broker_id, config(broker_id))
    require_success(f"{broker_id.value} adapter creation", created)
    if created.data is None:
        raise UsageEvidenceError(f"{broker_id.value} adapter creation returned no data")
    return created.data


@asynccontextmanager
async def real_session(broker_id: BrokerId) -> AsyncIterator[BrokerAdapter]:
    """Open, verify, and deterministically close one genuine provider session."""
    adapter = create_real_adapter(broker_id)
    try:
        connected = await adapter.connect()
        require_success(f"{broker_id.value} connect", connected)
        yield adapter
    finally:
        disconnected = await adapter.disconnect()
        require_success(f"{broker_id.value} disconnect", disconnected)


def require_success(
    label: str,
    result: StandardResponse[_ResultT],
) -> StandardResponse[_ResultT]:
    """Require and display one canonical successful broker result."""
    if result.status != "success":
        code = result.error.code if result.error is not None else "NO_ERROR_CODE"
        raise UsageEvidenceError(f"{label} failed with {code}")
    show(label, result)
    return result


def require_error(
    label: str,
    result: StandardResponse[_ResultT],
    *expected: BrokerErrorCode,
) -> StandardResponse[_ResultT]:
    """Require and display one exact canonical fail-closed broker result."""
    expected_codes = {code.value for code in expected}
    if result.error is None or result.error.code not in expected_codes:
        actual = result.error.code if result.error is not None else result.status
        wanted = ", ".join(code.value for code in expected)
        raise UsageEvidenceError(f"{label} returned {actual}; expected {wanted}")
    show(label, result)
    return result


def show(label: str, result: StandardResponse[object]) -> None:
    """Print bounded result metadata without provider payloads or secrets."""
    detail = ""
    if result.error is not None:
        detail = f" {result.error.code}"
    operation = result.metadata.extensions.get("operation", "unknown")
    print(label, result.status, str(operation) + detail)


def show_value(
    label: str,
    result: StandardResponse[object],
    value: object,
) -> None:
    """Print one bounded mapped provider value alongside result metadata."""
    require_success(label, result)
    print(f"{label} value", value)
