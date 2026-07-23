"""Explicit lazy broker adapter construction."""

import importlib
import importlib.metadata
import importlib.util
from dataclasses import dataclass
from typing import cast

from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerResult,
)
from app.utils import generate_id, logger, utc_now


@dataclass(frozen=True, slots=True)
class _ProviderRegistration:
    """Immutable adapter and dependency declaration."""

    module: str
    adapter_class: str
    import_package: str | None
    distribution: str | None
    constraint: str | None
    installation_extra: str


_FACTORIES = {
    BrokerId.MT5: _ProviderRegistration(
        "app.services.brokers.mt5_account",
        "MT5BrokerAdapter",
        "MetaTrader5",
        "MetaTrader5",
        None,
        "brokers",
    ),
    BrokerId.CTRADER: _ProviderRegistration(
        "app.services.brokers.ctrader_session",
        "CTraderBrokerAdapter",
        "ctrader_open_api",
        "ctrader-open-api",
        ">=0.9.2",
        "brokers",
    ),
    BrokerId.BINANCE_SPOT: _ProviderRegistration(
        "app.services.brokers.binance_session",
        "BinanceBrokerAdapter",
        "binance",
        "python-binance",
        ">=1.0.37",
        "brokers",
    ),
    BrokerId.BINANCE_USD_M_FUTURES: _ProviderRegistration(
        "app.services.brokers.binance_session",
        "BinanceBrokerAdapter",
        "binance",
        "python-binance",
        ">=1.0.37",
        "brokers",
    ),
    BrokerId.BINANCE_COIN_M_FUTURES: _ProviderRegistration(
        "app.services.brokers.binance_session",
        "BinanceBrokerAdapter",
        "binance",
        "python-binance",
        ">=1.0.37",
        "brokers",
    ),
    BrokerId.DUKASCOPY: _ProviderRegistration(
        "app.services.brokers.dukascopy_ticks",
        "DukascopyBrokerAdapter",
        None,
        None,
        None,
        "brokers",
    ),
    BrokerId.YAHOO: _ProviderRegistration(
        "app.services.brokers.yahoo_history",
        "YahooBrokerAdapter",
        "yfinance",
        "yfinance",
        ">=1.4.1",
        "brokers",
    ),
}


def get_registered_brokers() -> tuple[BrokerId, ...]:
    """List every profile without importing provider implementations or SDKs.

    Returns:
        Every registered broker identifier in stable enumeration order.
    """
    return tuple(BrokerId)


def _is_registered_broker(value: object) -> bool:
    """Return whether a runtime value is an exact registered broker identifier.

    Args:
        value: Potential broker identifier from a typed or untyped caller.

    Returns:
        Whether the value is a supported ``BrokerId`` member.
    """
    logger.debug("Validating explicit broker registry identifier")
    return isinstance(value, BrokerId)


def _require_dependency(registration: _ProviderRegistration) -> None:
    """Verify an optional provider dependency without importing its SDK.

    Args:
        registration: Provider declaration to inspect.

    Raises:
        ModuleNotFoundError: If the declared import package is unavailable.
    """
    if (
        registration.import_package is not None
        and importlib.util.find_spec(registration.import_package) is None
    ):
        raise ModuleNotFoundError(
            name=registration.import_package,
            path=registration.import_package,
        )


def create_broker_adapter(
    broker_id: BrokerId, config: BrokerConnectionConfig
) -> BrokerResult[BrokerAdapter]:
    """Create one exact disconnected adapter without selection or fallback.

    Args:
        broker_id: Exact registered broker identifier.
        config: Validated broker connection configuration.

    Returns:
        The disconnected adapter or a canonical structured factory error.
    """
    request_id = generate_id("req")
    if not _is_registered_broker(broker_id):
        return _factory_error(
            broker=config.broker_id,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_UNKNOWN,
            message="Broker profile is not registered",
            provider_metadata={"requested_broker": str(broker_id)},
        )
    if config.broker_id != broker_id or not config.provider_enabled:
        return _factory_error(
            broker=broker_id,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
            message="Broker config does not match or provider is disabled",
        )
    registration = _FACTORIES[broker_id]
    try:
        _require_dependency(registration)
        module = importlib.import_module(registration.module)
        adapter_type = getattr(module, registration.adapter_class)
        adapter = adapter_type(config)
    except ModuleNotFoundError as error:
        metadata: dict[str, object] = {
            "package": registration.distribution or error.name or registration.module,
            "missing_import": error.name,
            "required_version": registration.constraint,
            "installed_version": _installed_version(registration.distribution),
            "installation_extra": registration.installation_extra,
        }
        return _factory_error(
            broker=broker_id,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_DEPENDENCY_MISSING,
            message="Required broker dependency is missing",
            provider_metadata=metadata,
        )
    except ValueError:
        return _factory_error(
            broker=broker_id,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
            message="Broker profile configuration is invalid",
        )
    logger.bind(
        broker=broker_id.value,
        environment=config.environment.value,
        operation=BrokerCapabilityId.CONNECT.value,
        request_id=request_id,
        result="success",
    ).info("Created disconnected broker adapter")
    return BrokerResult(
        status="success",
        broker=broker_id,
        operation=BrokerCapabilityId.CONNECT,
        request_id=request_id,
        timestamp=utc_now(),
        environment=config.environment,
        adapter_version="1.0.0",
        data=cast("BrokerAdapter", adapter),
    )


def _factory_error(
    *,
    broker: BrokerId,
    config: BrokerConnectionConfig,
    request_id: str,
    code: BrokerErrorCode,
    message: str,
    provider_metadata: dict[str, object] | None = None,
) -> BrokerResult[BrokerAdapter]:
    """Handle factory error.

    Args:
        broker: Value supplied to the operation.
        config: Value supplied to the operation.
        request_id: Value supplied to the operation.
        code: Value supplied to the operation.
        message: Value supplied to the operation.
        provider_metadata: Value supplied to the operation.

    Returns:
        The operation result.
    """
    logger.bind(
        broker=broker.value,
        environment=config.environment.value,
        operation=BrokerCapabilityId.CONNECT.value,
        request_id=request_id,
        result="error",
        provider_code=code.value,
    ).warning("Broker adapter creation failed: %s", message)
    return BrokerResult(
        status="error",
        broker=broker,
        operation=BrokerCapabilityId.CONNECT,
        request_id=request_id,
        timestamp=utc_now(),
        environment=config.environment,
        adapter_version="1.0.0",
        error=BrokerError(code=code, message=message),
        provider_metadata=provider_metadata or {},
    )


def _installed_version(distribution: str | None) -> str | None:
    """Return the installed distribution version when present.

    Args:
        distribution: Declared project distribution name.

    Returns:
        Installed version, or ``None`` when absent/not applicable.
    """
    if distribution is None:
        return None
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
