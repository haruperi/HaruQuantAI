"""Explicit lazy broker adapter construction."""

import importlib
import importlib.metadata
from datetime import UTC, datetime
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
from app.services.brokers.registry.catalogue import (
    get_broker_capability_catalogue,
)
from app.utils import logger

_FACTORIES = {
    BrokerId.MT5: ("app.services.brokers.mt5", "MT5BrokerAdapter", "MetaTrader5"),
    BrokerId.CTRADER: (
        "app.services.brokers.ctrader",
        "CTraderBrokerAdapter",
        "ctrader-open-api",
    ),
    BrokerId.BINANCE_SPOT: (
        "app.services.brokers.binance",
        "BinanceBrokerAdapter",
        "python-binance",
    ),
    BrokerId.BINANCE_USD_M_FUTURES: (
        "app.services.brokers.binance",
        "BinanceBrokerAdapter",
        "python-binance",
    ),
    BrokerId.BINANCE_COIN_M_FUTURES: (
        "app.services.brokers.binance",
        "BinanceBrokerAdapter",
        "python-binance",
    ),
    BrokerId.DUKASCOPY: (
        "app.services.brokers.dukascopy",
        "DukascopyBrokerAdapter",
        None,
    ),
    BrokerId.YAHOO: (
        "app.services.brokers.yahoo",
        "YahooBrokerAdapter",
        "yfinance",
    ),
}


def get_registered_brokers() -> tuple[BrokerId, ...]:
    """List every profile without importing provider implementations or SDKs."""
    return tuple(BrokerId)


def create_broker_adapter(
    broker_id: BrokerId, config: BrokerConnectionConfig
) -> BrokerResult[BrokerAdapter]:
    """Create one exact disconnected adapter without selection or fallback."""
    request_id = f"create-{getattr(broker_id, 'value', str(broker_id))}"
    if not isinstance(broker_id, BrokerId):
        return _factory_error(
            broker=BrokerId.MT5,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_UNKNOWN,
            message="Broker profile is not registered",
        )
    if config.broker_id != broker_id or not config.provider_enabled:
        return _factory_error(
            broker=broker_id,
            config=config,
            request_id=request_id,
            code=BrokerErrorCode.BROKER_CONFIGURATION_INVALID,
            message="Broker config does not match or provider is disabled",
        )
    module_name, class_name, package = _FACTORIES[broker_id]
    try:
        module = importlib.import_module(module_name)
        adapter_type = getattr(module, class_name)
        catalogue = get_broker_capability_catalogue()[broker_id]
        capabilities = {item.capability: item for item in catalogue}
        adapter = adapter_type(config, capabilities)
    except ModuleNotFoundError as error:
        metadata: dict[str, object] = {
            "package": package or error.name or "unknown",
            "required_version": _required_version(package),
            "installed_version": None,
            "installation_extra": "brokers",
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
        timestamp=datetime.now(UTC),
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
        timestamp=datetime.now(UTC),
        environment=config.environment,
        adapter_version="1.0.0",
        error=BrokerError(code=code, message=message),
        provider_metadata=provider_metadata or {},
    )


def _required_version(package: str | None) -> str | None:
    if package is None:
        return None
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None
