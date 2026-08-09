"""Broker-owned provider connection resolution.

The Brokers domain owns broker credential resolution and connection. Credentials
are injected by an approved composition root through the public
:func:`app.utils.load_broker_provider_settings`. Cross-domain consumers (the
Data composition root, usage examples, and integration tests) select a route
only and never read credentials directly.

Only non-production environments (demo, testnet, sandbox) are permitted through
this boundary. Any live configuration is rejected before an adapter is built so
no caller can open a production connection through the standalone path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from pydantic import SecretStr

from app.services.brokers.contracts.enums import BrokerEnvironment, BrokerId
from app.services.brokers.operations import (
    build_broker_connection_config,
    connect_broker,
)
from app.services.brokers.registry.factory import create_broker_adapter
from app.utils import get_logger, load_broker_provider_settings

if TYPE_CHECKING:
    from app.services.brokers.contracts.models import BrokerConnectionConfig
    from app.services.brokers.contracts.protocols import BrokerAdapter

logger = get_logger(__name__)

_NON_PRODUCTION_ENVIRONMENTS = frozenset({"demo", "testnet", "sandbox"})
_YAHOO_PROBE_SYMBOL = "AAPL"


class _ProviderSettings(Protocol):
    """Private structural contract for broker-provider settings."""

    mt5_enabled: bool
    mt5_login: SecretStr | None
    mt5_password: SecretStr | None
    mt5_server: SecretStr | None
    mt5_terminal_path: SecretStr | None
    mt5_environment: str
    ctrader_enabled: bool
    ctrader_account_id: SecretStr | None
    ctrader_client_id: SecretStr | None
    ctrader_client_secret: SecretStr | None
    ctrader_access_token: SecretStr | None
    ctrader_environment: str
    binance_enabled: bool
    binance_environment: str
    dukascopy_enabled: bool
    yahoo_enabled: bool


def _require_provider_settings(settings: object) -> _ProviderSettings:
    """Narrow an opaque validated broker-settings object.

    Args:
        settings: Candidate settings object.

    Returns:
        The candidate narrowed to the private provider-settings contract.

    The Utils boundary performs model validation. Focused unit tests may supply a
    structural settings object containing only the selected provider's fields.
    """
    return cast("_ProviderSettings", settings)


@dataclass(frozen=True, slots=True, kw_only=True)
class _TransportParams:
    """Immutable transport and circuit-breaker bounds for one connection."""

    connect_timeout_sec: float = 10.0
    request_timeout_sec: float = 30.0
    transport_reconnect_max_attempts: int = 3
    stream_buffer_size: int = 1_000
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 1


def _require_non_production(provider: str, environment: str) -> None:
    """Block live-provider configuration before adapter construction.

    Args:
        provider: Canonical provider identifier for diagnostics.
        environment: Resolved provider environment.

    Raises:
        ValueError: If the environment is not an approved non-production target.
    """
    if environment not in _NON_PRODUCTION_ENVIRONMENTS:
        message = f"{provider} standalone connections reject live environments"
        raise ValueError(message)


def _resolve_credentials(
    provider: str, values: dict[str, SecretStr | None]
) -> dict[str, SecretStr]:
    """Return a complete non-empty credential set without exposing its values.

    Args:
        provider: Canonical provider identifier for diagnostics.
        values: Resolved credential candidates keyed by credential field name.

    Returns:
        The complete credential mapping with no None entries.

    Raises:
        ValueError: If any required credential is missing.
    """
    missing = tuple(name for name, value in values.items() if value is None)
    if missing:
        names = ", ".join(missing)
        message = f"{provider} standalone credentials missing: {names}"
        raise ValueError(message)
    return {name: value for name, value in values.items() if value is not None}


def _mt5_config(
    settings: _ProviderSettings,
    transport: _TransportParams,
) -> BrokerConnectionConfig:
    """Resolve the MT5 connection configuration from enabled settings.

    Returns:
        Resolved immutable MT5 connection configuration.

    Raises:
        ValueError: If MT5 is disabled, credentials are missing, or the
            environment is live.
    """
    if not settings.mt5_enabled:
        raise ValueError("mt5 standalone usage requires provider enablement")
    credentials = _resolve_credentials(
        "mt5",
        {
            "login": settings.mt5_login,
            "password": settings.mt5_password,
            "server": settings.mt5_server,
        },
    )
    if settings.mt5_terminal_path is not None:
        credentials["terminal_path"] = settings.mt5_terminal_path
    _require_non_production("mt5", settings.mt5_environment)
    return build_broker_connection_config(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment(settings.mt5_environment),
        provider_enabled=True,
        account_reference=credentials["login"].get_secret_value(),
        credentials=credentials,
        connect_timeout_sec=transport.connect_timeout_sec,
        request_timeout_sec=transport.request_timeout_sec,
        transport_reconnect_max_attempts=transport.transport_reconnect_max_attempts,
        stream_buffer_size=transport.stream_buffer_size,
        circuit_failure_threshold=transport.circuit_failure_threshold,
        circuit_recovery_timeout_sec=transport.circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=transport.circuit_half_open_max_calls,
    )


def _ctrader_config(
    settings: _ProviderSettings,
    transport: _TransportParams,
) -> BrokerConnectionConfig:
    """Resolve the cTrader connection configuration from enabled settings.

    Returns:
        Resolved immutable cTrader connection configuration.

    Raises:
        ValueError: If cTrader is disabled, credentials are missing, or the
            environment is live.
    """
    if not settings.ctrader_enabled:
        raise ValueError("ctrader standalone usage requires provider enablement")
    credentials = _resolve_credentials(
        "ctrader",
        {
            "account_id": settings.ctrader_account_id,
            "client_id": settings.ctrader_client_id,
            "client_secret": settings.ctrader_client_secret,
            "access_token": settings.ctrader_access_token,
        },
    )
    _require_non_production("ctrader", settings.ctrader_environment)
    return build_broker_connection_config(
        broker_id=BrokerId.CTRADER,
        environment=BrokerEnvironment(settings.ctrader_environment),
        provider_enabled=True,
        account_reference=credentials["account_id"].get_secret_value(),
        credentials=credentials,
        connect_timeout_sec=transport.connect_timeout_sec,
        request_timeout_sec=transport.request_timeout_sec,
        transport_reconnect_max_attempts=transport.transport_reconnect_max_attempts,
        stream_buffer_size=transport.stream_buffer_size,
        circuit_failure_threshold=transport.circuit_failure_threshold,
        circuit_recovery_timeout_sec=transport.circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=transport.circuit_half_open_max_calls,
    )


def _credential_free_config(
    provider: str,
    settings: _ProviderSettings,
    transport: _TransportParams,
) -> BrokerConnectionConfig:
    """Resolve a credential-free provider configuration from enabled settings.

    Returns:
        Resolved immutable credential-free connection configuration.

    Raises:
        ValueError: If the provider is disabled, unsupported, or the environment
            is live.
    """
    broker = BrokerId(provider)
    environment: str
    probe_symbol: str | None
    if broker == BrokerId.BINANCE_SPOT:
        if not settings.binance_enabled:
            message = "binance_spot standalone usage requires provider enablement"
            raise ValueError(message)
        environment, probe_symbol = settings.binance_environment, None
    elif broker == BrokerId.DUKASCOPY:
        if not settings.dukascopy_enabled:
            raise ValueError("dukascopy standalone usage requires provider enablement")
        environment, probe_symbol = "sandbox", None
    elif broker == BrokerId.YAHOO:
        if not settings.yahoo_enabled:
            raise ValueError("yahoo standalone usage requires provider enablement")
        environment, probe_symbol = "sandbox", _YAHOO_PROBE_SYMBOL
    else:
        message = f"{provider} has no approved standalone provider session"
        raise ValueError(message)
    _require_non_production(provider, environment)
    return build_broker_connection_config(
        broker_id=broker,
        environment=BrokerEnvironment(environment),
        provider_enabled=True,
        probe_symbol=probe_symbol,
        connect_timeout_sec=transport.connect_timeout_sec,
        request_timeout_sec=transport.request_timeout_sec,
        transport_reconnect_max_attempts=transport.transport_reconnect_max_attempts,
        stream_buffer_size=transport.stream_buffer_size,
        circuit_failure_threshold=transport.circuit_failure_threshold,
        circuit_recovery_timeout_sec=transport.circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=transport.circuit_half_open_max_calls,
    )


def resolve_provider_connection_config(
    broker_id: BrokerId | str,
    *,
    settings: object | None = None,
    connect_timeout_sec: float = 10.0,
    request_timeout_sec: float = 30.0,
    transport_reconnect_max_attempts: int = 3,
    stream_buffer_size: int = 1_000,
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout_sec: float = 30.0,
    circuit_half_open_max_calls: int = 1,
) -> BrokerConnectionConfig:
    """Resolve one governed non-production provider connection configuration.

    Credentials and environment are read from the central provider settings.
    Credential-free providers (Binance Spot, Dukascopy, Yahoo) skip credential
    resolution. Every resolved environment is enforced to be non-production.

    Args:
        broker_id: Canonical broker/provider identifier or its string value.
        settings: Optional pre-resolved provider settings; loaded when ``None``.
        connect_timeout_sec: Connect timeout in seconds.
        request_timeout_sec: Operation request timeout in seconds.
        transport_reconnect_max_attempts: Maximum reconnect attempts.
        stream_buffer_size: Maximum event queue size for streams.
        circuit_failure_threshold: Circuit breaker failure threshold.
        circuit_recovery_timeout_sec: Circuit breaker recovery delay in seconds.
        circuit_half_open_max_calls: Circuit breaker half-open max calls.

    Returns:
        Resolved immutable provider connection configuration.

    Raises:
        ValueError: If the provider is disabled, credentials are missing, the
            environment is live, or the broker identifier is unsupported.
    """
    resolved = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    provider_settings = _require_provider_settings(
        settings if settings is not None else load_broker_provider_settings()
    )
    transport = _TransportParams(
        connect_timeout_sec=connect_timeout_sec,
        request_timeout_sec=request_timeout_sec,
        transport_reconnect_max_attempts=transport_reconnect_max_attempts,
        stream_buffer_size=stream_buffer_size,
        circuit_failure_threshold=circuit_failure_threshold,
        circuit_recovery_timeout_sec=circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=circuit_half_open_max_calls,
    )
    if resolved is BrokerId.MT5:
        return _mt5_config(provider_settings, transport)
    if resolved is BrokerId.CTRADER:
        return _ctrader_config(provider_settings, transport)
    if resolved in {BrokerId.BINANCE_SPOT, BrokerId.DUKASCOPY, BrokerId.YAHOO}:
        return _credential_free_config(str(resolved), provider_settings, transport)
    message = f"{resolved} has no approved standalone provider session"
    raise ValueError(message)


async def create_connected_broker(
    broker_id: BrokerId | str,
    *,
    settings: object | None = None,
    connect: bool = True,
) -> BrokerAdapter:
    """Create one provider adapter from settings and optionally connect it.

    Credential resolution and environment enforcement are owned here so callers
    select a route only. When ``connect`` is ``True`` (the default) the adapter is
    connected and returned ready for use; loop-bound callers pass ``connect=False``
    to defer connection onto their own event loop.

    Args:
        broker_id: Canonical broker/provider identifier or its string value.
        settings: Optional pre-resolved provider settings; loaded when ``None``.
        connect: When ``True``, connect the adapter before returning it.

    Returns:
        The created (and when requested connected) broker adapter.

    Raises:
        ValueError: If the provider is disabled, credentials are missing, the
            environment is live, or construction fails.
    """
    config = resolve_provider_connection_config(broker_id, settings=settings)
    created = create_broker_adapter(config.broker_id, config)
    if created.error is not None or created.data is None:
        raise ValueError("broker adapter construction failed")
    adapter = created.data
    if connect:
        connect_result = await connect_broker(adapter)
        if connect_result.error is not None:
            logger.warning("Standalone provider connection failed")
            raise ValueError("broker adapter connection failed")
    return cast("BrokerAdapter", adapter)
