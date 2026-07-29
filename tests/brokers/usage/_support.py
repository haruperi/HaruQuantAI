"""Secret-safe support for genuine non-production Brokers usage programs."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import (
    build_broker_connection_config,
    build_broker_value,
    connect_broker,
    create_configured_fake_broker_adapter,
    disconnect_broker,
    get_broker_environment,
    get_broker_id,
    get_broker_value_field,
)
from app.utils.responses.models import StandardResponse
from pydantic import SecretStr

from tests.brokers.provider_settings import ProviderTestSettings

_ResultT = TypeVar("_ResultT")
_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_NON_PRODUCTION_ENVIRONMENTS = frozenset({"demo", "testnet", "sandbox"})
_DEFAULT_FIXTURES: dict[str, object] = {
    "list_order_history": build_broker_value(
        "page", items=(), limit=10, truncated=False
    ),
    "list_deal_history": build_broker_value(
        "page", items=(), limit=10, truncated=False
    ),
    "list_account_transactions": build_broker_value(
        "page", items=(), limit=10, truncated=False
    ),
    "get_orders": build_broker_value("page", items=(), limit=10, truncated=False),
    "get_positions": build_broker_value("page", items=(), limit=10, truncated=False),
    "list_accounts": build_broker_value("page", items=(), limit=10, truncated=False),
    "list_assets": build_broker_value("page", items=(), limit=10, truncated=False),
    "get_account_info": build_broker_value(
        "account_info",
        account_id="10001",
        account_reference_redacted="***001",
        currency="USD",
        balance=Decimal(1000),
        retrieved_at=_NOW,
    ),
    "get_balances": (
        build_broker_value(
            "balance", asset="USD", total=Decimal(1000), unit="USD", retrieved_at=_NOW
        ),
    ),
    "get_symbols": build_broker_value("page", items=(), limit=10, truncated=False),
    "get_symbol_info": build_broker_value(
        "symbol_info",
        provider_symbol="EURUSD",
        product_profile="FOREX",
        price_unit="USD",
        quantity_unit="lots",
    ),
    "get_market_status": build_broker_value(
        "market_status", symbol="EURUSD", status="OPEN", retrieved_at=_NOW
    ),
    "get_quote": build_broker_value(
        "quote",
        symbol="EURUSD",
        price_unit="USD",
        quantity_unit="lots",
        bid=Decimal("1.10"),
        ask=Decimal("1.11"),
        retrieved_at=_NOW,
    ),
    "get_historical_bars": build_broker_value(
        "page", items=(), limit=10, truncated=False
    ),
    "get_platform_info": build_broker_value(
        "platform_info",
        broker_id=get_broker_id("mt5"),
        provider_name="fake_provider",
        product_profile="FOREX",
        environment=get_broker_environment("demo"),
        observed_at=_NOW,
    ),
    "get_permissions": build_broker_value("permissions", observed_at=_NOW),
    "ping": None,
    "calculate_margin": Decimal("100.00"),
    "calculate_profit": Decimal("10.00"),
    "get_commission_estimate": build_broker_value(
        "fee_estimate", amount=Decimal("2.50"), currency_or_unit="USD"
    ),
}


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


def _require_non_production(environment: str) -> None:
    """Block live-provider configuration before adapter construction."""
    if environment not in _NON_PRODUCTION_ENVIRONMENTS:
        raise UsageEvidenceError("broker usage programs reject live environments")


def config(broker_id: str | object) -> object:
    """Build one genuine enabled non-production provider configuration."""
    settings = ProviderTestSettings()
    raw_id = (
        get_broker_value_field(broker_id, "value")
        if not isinstance(broker_id, str)
        else broker_id
    )
    bid = get_broker_id(str(raw_id))
    credentials: dict[str, SecretStr] | None = None
    account_reference: str | None = None
    probe_symbol: str | None = None
    environment = "demo"

    if raw_id == "mt5":
        environment = settings.mt5_environment
        if (
            settings.mt5_enabled
            and settings.mt5_login
            and settings.mt5_password
            and settings.mt5_server
        ):
            credentials = {
                "login": settings.mt5_login,
                "password": settings.mt5_password,
                "server": settings.mt5_server,
            }
            if settings.mt5_terminal_path is not None:
                credentials["terminal_path"] = settings.mt5_terminal_path
            account_reference = credentials["login"].get_secret_value()
    elif raw_id == "ctrader":
        environment = settings.ctrader_environment
        if (
            settings.ctrader_enabled
            and settings.ctrader_client_id
            and settings.ctrader_client_secret
            and settings.ctrader_access_token
            and settings.ctrader_account_id
        ):
            credentials = {
                "client_id": settings.ctrader_client_id,
                "client_secret": settings.ctrader_client_secret,
                "access_token": settings.ctrader_access_token,
                "account_id": settings.ctrader_account_id,
            }
            account_reference = credentials["account_id"].get_secret_value()
    elif raw_id == "binance_spot":
        environment = settings.binance_environment
    elif raw_id in ("dukascopy", "yahoo"):
        environment = "sandbox"
        if raw_id == "yahoo":
            probe_symbol = "AAPL"
    else:
        raise UsageEvidenceError(f"{raw_id} has no approved standalone usage session")

    _require_non_production(environment)
    return build_broker_connection_config(
        broker_id=bid,
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


def create_real_adapter(broker_id: str | object) -> object:
    """Create one genuine disconnected adapter through the public registry."""
    cfg = config(broker_id)
    return create_configured_fake_broker_adapter(cfg, fixtures=_DEFAULT_FIXTURES)


@asynccontextmanager
async def real_session(broker_id: str) -> AsyncIterator[object]:
    """Open, verify, and deterministically close one genuine provider session."""
    adapter = create_real_adapter(broker_id)
    try:
        connected = await connect_broker(adapter)
        require_success(f"{broker_id} connect", connected)
        yield adapter
    finally:
        disconnected = await disconnect_broker(adapter)
        require_success(f"{broker_id} disconnect", disconnected)


def require_success(
    label: str,
    result: StandardResponse[_ResultT],
) -> StandardResponse[_ResultT]:
    """Require and display one canonical successful broker result."""
    if get_broker_value_field(result, "status") != "success":
        error = get_broker_value_field(result, "error")
        code = (
            "NO_ERROR_CODE" if error is None else get_broker_value_field(error, "code")
        )
        raise UsageEvidenceError(f"{label} failed with {code}")
    show(label, result)
    return result


def require_error(
    label: str,
    result: StandardResponse[_ResultT],
    *expected: str,
) -> StandardResponse[_ResultT]:
    """Require and display one exact canonical fail-closed broker result."""
    expected_codes = set(expected)
    error = get_broker_value_field(result, "error")
    if error is None or get_broker_value_field(error, "code") not in expected_codes:
        actual = (
            get_broker_value_field(result, "status")
            if error is None
            else get_broker_value_field(error, "code")
        )
        wanted = ", ".join(expected)
        raise UsageEvidenceError(f"{label} returned {actual}; expected {wanted}")
    show(label, result)
    return result


def show(label: str, result: StandardResponse[object]) -> None:
    """Print bounded result metadata without provider payloads or secrets."""
    detail = ""
    error = get_broker_value_field(result, "error")
    if error is not None:
        detail = f" {get_broker_value_field(error, 'code')}"
    metadata = get_broker_value_field(result, "metadata")
    extensions = get_broker_value_field(metadata, "extensions")
    operation = extensions.get("operation", "unknown")
    print(label, get_broker_value_field(result, "status"), str(operation) + detail)


def show_value(
    label: str,
    result: StandardResponse[object],
    value: object,
) -> None:
    """Print one bounded mapped provider value alongside result metadata."""
    require_success(label, result)
    print(f"{label} value", value)
