"""Standalone public adapter operations and DTO builders for the Brokers domain."""

# ruff: noqa: TC001
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerResubmissionPolicy,
    BrokerUncertainty,
)
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerConnectionConfig,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerError,
    BrokerFeatureFlags,
    BrokerFeeEstimate,
    BrokerMarginRequest,
    BrokerMarketStatus,
    BrokerOrder,
    BrokerOrderBook,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderProtectionRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerPositionReductionRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerServerTime,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)
from app.services.brokers.contracts.protocols import (
    BrokerAdapter,
    BrokerSubscription,
)
from app.services.brokers.contracts.responses import StandardResponse

_BROKER_VALUE_TYPES: Mapping[str, type[object]] = {
    "account_info": BrokerAccountInfo,
    "account_transaction": BrokerAccountTransaction,
    "asset_info": BrokerAssetInfo,
    "balance": BrokerBalance,
    "bar": BrokerBar,
    "connection_config": BrokerConnectionConfig,
    "connection_status": BrokerConnectionStatus,
    "deal": BrokerDeal,
    "error": BrokerError,
    "feature_flags": BrokerFeatureFlags,
    "fee_estimate": BrokerFeeEstimate,
    "margin_request": BrokerMarginRequest,
    "market_status": BrokerMarketStatus,
    "order": BrokerOrder,
    "order_book": BrokerOrderBook,
    "order_check": BrokerOrderCheck,
    "order_filter": BrokerOrderFilter,
    "order_modification_request": BrokerOrderModificationRequest,
    "order_request": BrokerOrderRequest,
    "order_result": BrokerOrderResult,
    "page": BrokerPage,
    "permissions": BrokerPermissions,
    "platform_info": BrokerPlatformInfo,
    "position": BrokerPosition,
    "position_close_request": BrokerPositionCloseRequest,
    "position_filter": BrokerPositionFilter,
    "position_modification_request": BrokerPositionModificationRequest,
    "profit_request": BrokerProfitRequest,
    "quote": BrokerQuote,
    "subscription_info": BrokerSubscriptionInfo,
    "symbol_info": BrokerSymbolInfo,
    "tick": BrokerTick,
    "trading_session": BrokerTradingSession,
}

# --- DTO Builder Functions ---


def build_broker_value(value_type: str, /, **fields: object) -> object:
    """Build one documented opaque Broker contract value.

    Args:
        value_type: Registered lower-snake-case contract value name.
        **fields: Exact constructor fields for that contract value.

    Returns:
        A Broker-owned opaque value.

    Raises:
        ValueError: If ``value_type`` is not a documented contract value.
        TypeError: If the supplied fields do not satisfy its invariant.
    """
    target = _BROKER_VALUE_TYPES.get(value_type)
    if target is None:
        message = f"Unsupported Broker value type: {value_type}"
        raise ValueError(message)
    return target(**fields)


def get_broker_value_field(value: object, field_name: str) -> object:
    """Return one non-private field from an opaque Broker-owned value.

    Args:
        value: Value returned by a Broker root function.
        field_name: Documented non-private field to read.

    Returns:
        The requested field value.

    Raises:
        ValueError: If a private field name is requested.
        TypeError: If the value does not expose the requested field.
    """
    if field_name.startswith("_"):
        raise ValueError("Broker value fields must be public")
    try:
        return getattr(value, field_name)
    except AttributeError as error:
        message = f"Broker value does not expose {field_name!r}"
        raise TypeError(message) from error


def set_fake_broker_error(
    adapter: object,
    capability_id: str,
    error_code: str | None = None,
    message: str = "bounded fake-adapter error",
) -> StandardResponse[None]:
    """Set or clear one deterministic fake-adapter error fixture.

    Args:
        adapter: Opaque fake adapter created through the package root.
        capability_id: Capability identifier whose result is controlled.
        error_code: Canonical error code, or ``None`` to clear the fixture.
        message: Bounded non-sensitive error message.

    Returns:
        Canonical fixture-update result.

    Raises:
        TypeError: If ``adapter`` is not a package-root fake adapter value.
    """
    from app.services.brokers.testing.fake import FakeBrokerAdapter

    if not isinstance(adapter, FakeBrokerAdapter):
        raise TypeError("adapter must be a fake broker adapter")
    error = (
        None
        if error_code is None
        else BrokerError(code=BrokerErrorCode(error_code), message=message)
    )
    return adapter.inject_error(BrokerCapabilityId(capability_id), error)


def create_configured_fake_broker_adapter(
    config: object, fixtures: Mapping[str, object] | None = None
) -> object:
    """Create an opaque deterministic fake adapter from root-built values.

    Args:
        config: Opaque Broker connection configuration.
        fixtures: Optional capability-ID to opaque fixture-value mapping.

    Returns:
        Opaque deterministic fake adapter.

    Raises:
        TypeError: If config is not a Broker connection configuration.
    """
    from app.services.brokers.testing.fake import FakeBrokerAdapter

    if not isinstance(config, BrokerConnectionConfig):
        raise TypeError("config must be a Broker connection configuration")
    mutations = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
        BrokerCapabilityId.ATTACH_PROTECTION,
        BrokerCapabilityId.REDUCE_POSITION,
    }
    capabilities = {
        capability: BrokerCapability(
            capability=capability,
            implementation_status="IMPLEMENTED",
            availability="UNAVAILABLE" if capability in mutations else "AVAILABLE",
            access_mode="WRITE" if capability in mutations else "READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for capability in BrokerCapabilityId
    }
    mapped_fixtures = {
        BrokerCapabilityId(capability): fixture
        for capability, fixture in (fixtures or {}).items()
    }
    return FakeBrokerAdapter(config, capabilities, fixtures=mapped_fixtures)


def get_broker_id(value: str) -> object:
    """Return one opaque validated Broker provider identifier.

    Args:
        value: Canonical provider identifier.

    Returns:
        Broker-owned validated provider identifier.
    """
    return BrokerId(value)


def get_broker_environment(value: str) -> object:
    """Return one opaque validated Broker environment identifier.

    Args:
        value: Canonical environment identifier.

    Returns:
        Broker-owned validated environment identifier.
    """
    return BrokerEnvironment(value)


def get_broker_capability_id(value: str) -> object:
    """Return one opaque validated Broker capability identifier.

    Args:
        value: Canonical capability identifier.

    Returns:
        Broker-owned validated capability identifier.
    """
    return BrokerCapabilityId(value)


def get_broker_error_code(value: str) -> object:
    """Return one opaque validated canonical Broker error code.

    Args:
        value: Canonical error-code identifier.

    Returns:
        Broker-owned validated error code.
    """
    return BrokerErrorCode(value)


def build_broker_connection_config(
    broker_id: BrokerId | str,
    environment: BrokerEnvironment | str,
    account_reference: str | None = None,
    credentials: Mapping[str, Any] | None = None,
    provider_enabled: bool = True,
    probe_symbol: str | None = None,
    connect_timeout_sec: float = 5.0,
    request_timeout_sec: float = 10.0,
    transport_reconnect_max_attempts: int = 3,
    stream_buffer_size: int = 1000,
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout_sec: float = 30.0,
    circuit_half_open_max_calls: int = 3,
    auto_connect: bool = False,
) -> BrokerConnectionConfig:
    """Build a BrokerConnectionConfig immutable instance.

    Args:
        broker_id: Broker or profile identifier.
        environment: Broker environment (e.g. demo, live).
        account_reference: Optional account reference.
        credentials: Optional resolved credentials mapping.
        provider_enabled: Whether the provider is enabled.
        probe_symbol: Optional verification probe symbol.
        connect_timeout_sec: Connect timeout in seconds.
        request_timeout_sec: Operation request timeout in seconds.
        transport_reconnect_max_attempts: Maximum reconnect attempts.
        stream_buffer_size: Maximum event queue size for streams.
        circuit_failure_threshold: Circuit breaker failure threshold.
        circuit_recovery_timeout_sec: Circuit recovery delay in seconds.
        circuit_half_open_max_calls: Circuit half-open max calls.
        auto_connect: Whether to auto-connect on operation.

    Returns:
        Configured BrokerConnectionConfig instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    env = (
        BrokerEnvironment(environment) if isinstance(environment, str) else environment
    )
    return BrokerConnectionConfig(
        broker_id=bid,
        environment=env,
        account_reference=account_reference,
        credentials=credentials,
        provider_enabled=provider_enabled,
        probe_symbol=probe_symbol,
        connect_timeout_sec=connect_timeout_sec,
        request_timeout_sec=request_timeout_sec,
        transport_reconnect_max_attempts=transport_reconnect_max_attempts,
        stream_buffer_size=stream_buffer_size,
        circuit_failure_threshold=circuit_failure_threshold,
        circuit_recovery_timeout_sec=circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=circuit_half_open_max_calls,
        auto_connect=auto_connect,
    )


def build_broker_order_request(
    symbol: str,
    side: Literal["BUY", "SELL"],
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
    quantity: Decimal | float | str,
    quantity_unit: str,
    environment: BrokerEnvironment | str,
    account_reference: str | None = None,
    limit_price: Decimal | float | str | None = None,
    stop_price: Decimal | float | str | None = None,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None,
    expiration: datetime | None = None,
    client_order_id: str | None = None,
) -> BrokerOrderRequest:
    """Build a BrokerOrderRequest instance.

    Args:
        symbol: Instrument symbol.
        side: Order side (buy, sell).
        order_type: Order type (market, limit, stop).
        quantity: Order quantity.
        quantity_unit: Provider quantity unit.
        environment: Target broker environment.
        account_reference: Optional account reference.
        limit_price: Optional limit price.
        stop_price: Optional stop price.
        stop_loss: Optional stop loss price.
        take_profit: Optional take profit price.
        time_in_force: Time in force policy.
        expiration: Optional GTD expiration.
        client_order_id: Optional client-side order identifier.

    Returns:
        Configured BrokerOrderRequest instance.
    """
    env = (
        BrokerEnvironment(environment) if isinstance(environment, str) else environment
    )
    return BrokerOrderRequest(
        symbol=symbol,
        order_type=order_type,
        side=side,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
        environment=env,
        account_reference=account_reference,
        limit_price=Decimal(str(limit_price)) if limit_price is not None else None,
        stop_price=Decimal(str(stop_price)) if stop_price is not None else None,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        time_in_force=time_in_force,
        expiration=expiration,
        client_order_id=client_order_id,
    )


def build_broker_order_modification_request(
    order_id: str,
    limit_price: Decimal | float | str | None = None,
    stop_price: Decimal | float | str | None = None,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    quantity: Decimal | float | str | None = None,
) -> BrokerOrderModificationRequest:
    """Build a BrokerOrderModificationRequest instance.

    Args:
        order_id: Order identifier.
        limit_price: Optional new limit price.
        stop_price: Optional new stop price.
        stop_loss: Optional new stop loss.
        take_profit: Optional new take profit.
        quantity: Optional new quantity.

    Returns:
        Configured BrokerOrderModificationRequest instance.
    """
    return BrokerOrderModificationRequest(
        order_id=order_id,
        limit_price=Decimal(str(limit_price)) if limit_price is not None else None,
        stop_price=Decimal(str(stop_price)) if stop_price is not None else None,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        quantity=Decimal(str(quantity)) if quantity is not None else None,
    )


def build_broker_position_close_request(
    position_id: str,
    quantity: Decimal | float | str,
    quantity_unit: str,
) -> BrokerPositionCloseRequest:
    """Build a BrokerPositionCloseRequest instance.

    Args:
        position_id: Position identifier.
        quantity: Exact close quantity.
        quantity_unit: Provider quantity unit.

    Returns:
        Configured BrokerPositionCloseRequest instance.
    """
    return BrokerPositionCloseRequest(
        position_id=position_id,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
    )


def build_broker_position_modification_request(
    position_id: str,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
) -> BrokerPositionModificationRequest:
    """Build a BrokerPositionModificationRequest instance.

    Args:
        position_id: Position identifier.
        stop_loss: Optional stop loss price.
        take_profit: Optional take profit price.

    Returns:
        Configured BrokerPositionModificationRequest instance.
    """
    return BrokerPositionModificationRequest(
        position_id=position_id,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
    )


def build_broker_margin_request(
    symbol: str,
    side: Literal["BUY", "SELL"],
    quantity: Decimal | float | str,
    quantity_unit: str,
    product_profile: str,
    price: Decimal | float | str | None = None,
) -> BrokerMarginRequest:
    """Build a BrokerMarginRequest instance.

    Args:
        symbol: Instrument symbol.
        side: Trade side.
        quantity: Order quantity.
        quantity_unit: Provider quantity unit.
        product_profile: Provider product profile.
        price: Optional reference price.

    Returns:
        Configured BrokerMarginRequest instance.
    """
    return BrokerMarginRequest(
        symbol=symbol,
        side=side,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
        product_profile=product_profile,
        price=Decimal(str(price)) if price is not None else None,
    )


def build_broker_profit_request(
    symbol: str,
    side: Literal["BUY", "SELL"],
    quantity: Decimal | float | str,
    quantity_unit: str,
    open_price: Decimal | float | str,
    close_price: Decimal | float | str,
    product_profile: str,
) -> BrokerProfitRequest:
    """Build a BrokerProfitRequest instance.

    Args:
        symbol: Instrument symbol.
        side: Position side.
        quantity: Quantity.
        quantity_unit: Provider quantity unit.
        open_price: Opening price.
        close_price: Closing price.
        product_profile: Provider product profile.

    Returns:
        Configured BrokerProfitRequest instance.
    """
    return BrokerProfitRequest(
        symbol=symbol,
        side=side,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
        open_price=Decimal(str(open_price)),
        close_price=Decimal(str(close_price)),
        product_profile=product_profile,
    )


def build_broker_order_filter(
    symbol: str | None = None,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> BrokerOrderFilter:
    """Build a BrokerOrderFilter instance.

    Args:
        symbol: Optional symbol filter.
        status: Optional status filter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.

    Returns:
        Configured BrokerOrderFilter instance.
    """
    return BrokerOrderFilter(
        symbol=symbol,
        status=status,
        start=start_time,
        end=end_time,
    )


def build_broker_position_filter(
    symbol: str | None = None,
) -> BrokerPositionFilter:
    """Build a BrokerPositionFilter instance.

    Args:
        symbol: Optional symbol filter.

    Returns:
        Configured BrokerPositionFilter instance.
    """
    return BrokerPositionFilter(symbol=symbol)


def get_broker_connection_id(connection: object) -> str:
    """Return the configured provider identifier from opaque connection material.

    Args:
        connection: Broker-owned connection configuration.

    Returns:
        Canonical provider identifier.

    Raises:
        TypeError: If the supplied value is not Broker connection configuration.
    """
    if not isinstance(connection, BrokerConnectionConfig):
        raise TypeError("connection must be BrokerConnectionConfig")
    return connection.broker_id.value


def get_broker_connection_environment(connection: object) -> str:
    """Return the configured environment from opaque connection material.

    Args:
        connection: Broker-owned connection configuration.

    Returns:
        Canonical environment identifier.

    Raises:
        TypeError: If the supplied value is not Broker connection configuration.
    """
    if not isinstance(connection, BrokerConnectionConfig):
        raise TypeError("connection must be BrokerConnectionConfig")
    return connection.environment.value


def get_broker_connection_account_reference(connection: object) -> str | None:
    """Return the account reference from opaque connection material.

    Args:
        connection: Broker-owned connection configuration.

    Returns:
        The configured account reference, if present.

    Raises:
        TypeError: If the supplied value is not Broker connection configuration.
    """
    if not isinstance(connection, BrokerConnectionConfig):
        raise TypeError("connection must be BrokerConnectionConfig")
    return connection.account_reference


def is_broker_connection_enabled(connection: object) -> bool:
    """Return whether opaque connection material permits provider use.

    Args:
        connection: Broker-owned connection configuration.

    Returns:
        Whether the provider is explicitly enabled.

    Raises:
        TypeError: If the supplied value is not Broker connection configuration.
    """
    if not isinstance(connection, BrokerConnectionConfig):
        raise TypeError("connection must be BrokerConnectionConfig")
    return connection.provider_enabled


def get_broker_adapter_contract_version(adapter: object) -> str:
    """Return the protocol version from an opaque Broker adapter.

    Args:
        adapter: Broker-owned adapter implementation.

    Returns:
        Declared adapter contract version.

    Raises:
        TypeError: If the adapter does not satisfy the Broker protocol.
    """
    contract_version = getattr(adapter, "contract_version", None)
    if not isinstance(contract_version, str):
        raise TypeError("adapter must expose a string contract_version")
    return contract_version


def get_broker_adapter_schema_id(adapter: object) -> str:
    """Return the schema identifier from an opaque Broker adapter.

    Args:
        adapter: Broker-owned adapter implementation.

    Returns:
        Declared adapter schema identifier.

    Raises:
        TypeError: If the adapter does not satisfy the Broker protocol.
    """
    schema_id = getattr(adapter, "schema_id", None)
    if not isinstance(schema_id, str):
        raise TypeError("adapter must expose a string schema_id")
    return schema_id


def get_broker_feature_flag_id(feature_flags: object) -> str:
    """Return the provider identifier from opaque feature-flag evidence.

    Args:
        feature_flags: Broker-owned feature-flag evidence.

    Returns:
        Canonical provider identifier.

    Raises:
        TypeError: If the supplied value is not feature-flag evidence.
    """
    broker_id = getattr(feature_flags, "broker_id", None)
    value = getattr(broker_id, "value", broker_id)
    if not isinstance(value, str):
        raise TypeError("feature_flags must expose a string broker_id")
    return value


def get_broker_feature_flag_environment(feature_flags: object) -> str:
    """Return the environment from opaque feature-flag evidence.

    Args:
        feature_flags: Broker-owned feature-flag evidence.

    Returns:
        Canonical environment identifier.

    Raises:
        TypeError: If the supplied value is not feature-flag evidence.
    """
    environment = getattr(feature_flags, "environment", None)
    value = getattr(environment, "value", environment)
    if not isinstance(value, str):
        raise TypeError("feature_flags must expose a string environment")
    return value


# --- Standalone Adapter Operation Delegate Functions ---


async def connect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Connect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing connection status.
    """
    return await adapter.connect()


async def disconnect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[None]:
    """Disconnect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response confirming disconnection.
    """
    return await adapter.disconnect()


async def reconnect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Reconnect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing connection status.
    """
    return await adapter.reconnect()


async def is_broker_connected(adapter: BrokerAdapter) -> StandardResponse[bool]:
    """Check if the broker adapter session is currently connected.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing the verified connectivity state.
    """
    return await adapter.is_connected()


async def get_broker_connection_status(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Get connection status of the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response with detailed connection status.
    """
    return await adapter.get_connection_status()


async def ping_broker(adapter: BrokerAdapter) -> StandardResponse[None]:
    """Ping the broker provider transport.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response confirming ping success.
    """
    return await adapter.ping()


async def get_broker_last_error(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerError | None]:
    """Get last error reported by the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing last BrokerError or None.
    """
    return await adapter.get_last_error()


async def get_broker_feature_flags(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerFeatureFlags]:
    """Get runtime feature flags for the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing feature flags.
    """
    return await adapter.get_feature_flags()


async def supports_broker_capability(
    adapter: BrokerAdapter,
    capability_id: BrokerCapabilityId | str,
) -> StandardResponse[bool]:
    """Check if the broker adapter supports a given capability.

    Args:
        adapter: Targeted broker adapter.
        capability_id: Capability identifier to check.

    Returns:
        True if supported and available, False otherwise.
    """
    capability = (
        BrokerCapabilityId(capability_id)
        if isinstance(capability_id, str)
        else capability_id
    )
    return await adapter.supports(capability)


async def get_broker_platform_info(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerPlatformInfo]:
    """Get platform info from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing platform info.
    """
    return await adapter.get_platform_info()


async def get_broker_balances(
    adapter: BrokerAdapter,
) -> StandardResponse[tuple[BrokerBalance, ...]]:
    """Get account balances from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing tuple of balances.
    """
    return await adapter.get_balances()


async def get_broker_permissions(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerPermissions]:
    """Get account permissions from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing permissions.
    """
    return await adapter.get_permissions()


async def get_broker_account_info(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerAccountInfo]:
    """Get account details from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing account info.
    """
    return await adapter.get_account_info()


async def get_broker_symbols(
    adapter: BrokerAdapter,
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerSymbolInfo]]:
    """Get page of symbols from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        query: Optional symbol query.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of symbol info.
    """
    return await adapter.get_symbols(query=query, cursor=cursor, limit=limit)


async def get_broker_symbol_info(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerSymbolInfo]:
    """Get symbol info from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing symbol info.
    """
    return await adapter.get_symbol_info(symbol)


async def select_broker_symbol(
    adapter: BrokerAdapter,
    symbol: str,
    enabled: bool = True,
) -> StandardResponse[None]:
    """Select or subscribe symbol on the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        enabled: Enable or disable selection.

    Returns:
        Standard response confirming selection outcome.
    """
    return await adapter.select_symbol(symbol, enabled=enabled)


async def get_broker_market_status(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerMarketStatus]:
    """Get market status for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing market status.
    """
    return await adapter.get_market_status(symbol)


async def get_broker_trading_sessions(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[tuple[BrokerTradingSession, ...]]:
    """Get trading sessions for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing trading sessions tuple.
    """
    return await adapter.get_trading_sessions(symbol)


async def get_broker_quote(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerQuote]:
    """Get current quote for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing latest quote.
    """
    return await adapter.get_quote(symbol)


async def get_broker_spread(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[Decimal]:
    """Get current spread for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing spread value.
    """
    return await adapter.get_spread(symbol)


async def get_broker_ticks(
    adapter: BrokerAdapter,
    symbol: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerTick]]:
    """Get historical ticks for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        limit: Optional record count limit.

    Returns:
        Standard response containing ticks tuple.
    """
    return await adapter.get_ticks(symbol, start=start_time, end=end_time, limit=limit)


async def get_broker_historical_bars(
    adapter: BrokerAdapter,
    symbol: str,
    timeframe: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerBar]]:
    """Get historical bars for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        limit: Optional bar count limit.

    Returns:
        Standard response containing bars tuple.
    """
    return await adapter.get_historical_bars(
        symbol,
        timeframe,
        start=start_time,
        end=end_time,
        limit=limit,
    )


async def get_broker_order_book(
    adapter: BrokerAdapter,
    symbol: str,
    depth: int | None = None,
) -> StandardResponse[BrokerOrderBook]:
    """Get order book for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        depth: Optional order book depth limit.

    Returns:
        Standard response containing order book.
    """
    return await adapter.get_order_book(symbol, depth=depth)


async def subscribe_broker_quotes(
    adapter: BrokerAdapter,
    symbol: str | tuple[str, ...],
) -> StandardResponse[BrokerSubscription[BrokerQuote]]:
    """Subscribe to quote updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_quotes(symbols)


async def subscribe_broker_bars(
    adapter: BrokerAdapter,
    symbol: str | tuple[str, ...],
    timeframe: str,
) -> StandardResponse[BrokerSubscription[BrokerBar]]:
    """Subscribe to bar updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        timeframe: Bar timeframe string.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_bars(symbols, timeframe)


async def subscribe_broker_order_book(
    adapter: BrokerAdapter,
    symbol: str | tuple[str, ...],
    depth: int | None = None,
) -> StandardResponse[BrokerSubscription[BrokerOrderBook]]:
    """Subscribe to order book updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        depth: Optional order book depth limit.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_order_book(symbols, depth=depth)


async def unsubscribe_broker(
    subscription: BrokerSubscription[Any],
) -> StandardResponse[None]:
    """Unsubscribe an active subscription handle.

    Args:
        subscription: Active broker subscription handle.

    Returns:
        Standard response confirming unsubscribe outcome.
    """
    return await subscription.unsubscribe()


async def list_broker_subscriptions(
    adapter: BrokerAdapter,
) -> StandardResponse[tuple[BrokerSubscriptionInfo, ...]]:
    """List active subscriptions on the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing tuple of subscription info.
    """
    return await adapter.list_subscriptions()


async def get_broker_positions(
    adapter: BrokerAdapter,
    filter_spec: BrokerPositionFilter | None = None,
    limit: int = 1000,
) -> StandardResponse[BrokerPage[BrokerPosition]]:
    """Get open positions from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional position filter.
        limit: Maximum items to return.

    Returns:
        Standard response containing positions tuple.
    """
    return await adapter.get_positions(filter=filter_spec, limit=limit)


async def get_broker_position(
    adapter: BrokerAdapter,
    position_id: str,
) -> StandardResponse[BrokerPosition]:
    """Get position details by position ID.

    Args:
        adapter: Targeted broker adapter.
        position_id: Position identifier.

    Returns:
        Standard response containing position details.
    """
    return await adapter.get_position(position_id)


async def get_broker_orders(
    adapter: BrokerAdapter,
    filter_spec: BrokerOrderFilter | None = None,
    limit: int = 1000,
) -> StandardResponse[BrokerPage[BrokerOrder]]:
    """Get active orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional order filter.
        limit: Maximum items to return.

    Returns:
        Standard response containing orders tuple.
    """
    return await adapter.get_orders(filter=filter_spec, limit=limit)


async def get_broker_order(
    adapter: BrokerAdapter,
    order_id: str,
) -> StandardResponse[BrokerOrder]:
    """Get order details by order ID.

    Args:
        adapter: Targeted broker adapter.
        order_id: Order identifier.

    Returns:
        Standard response containing order details.
    """
    return await adapter.get_order(order_id)


async def list_broker_order_history(
    adapter: BrokerAdapter,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    symbol: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerOrder]]:
    """List historical orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        start_time: Inclusive history start timestamp.
        end_time: Exclusive history end timestamp.
        symbol: Optional exact provider symbol.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of orders.
    """
    return await adapter.list_order_history(
        start=start_time,
        end=end_time,
        symbol=symbol,
        cursor=cursor,
        limit=limit,
    )


async def list_broker_deal_history(
    adapter: BrokerAdapter,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerDeal]]:
    """List historical deals/fills from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of deals.
    """
    return await adapter.list_deal_history(
        start=start_time, end=end_time, cursor=cursor, limit=limit
    )


async def get_broker_deal(
    adapter: BrokerAdapter,
    deal_id: str,
) -> StandardResponse[BrokerDeal]:
    """Get deal/fill details by deal ID.

    Args:
        adapter: Targeted broker adapter.
        deal_id: Deal identifier.

    Returns:
        Standard response containing deal details.
    """
    return await adapter.get_deal(deal_id)


async def list_broker_account_transactions(
    adapter: BrokerAdapter,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerAccountTransaction]]:
    """List account transactions (deposits, withdrawals, fees).

    Args:
        adapter: Targeted broker adapter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of transactions.
    """
    return await adapter.list_account_transactions(
        start=start_time, end=end_time, cursor=cursor, limit=limit
    )


async def check_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderRequest,
) -> StandardResponse[BrokerOrderCheck]:
    """Pre-validate order request on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order request.

    Returns:
        Standard response containing check result.
    """
    return await adapter.check_order(request)


async def place_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Place new order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order request.

    Returns:
        Standard response containing order execution result.
    """
    return await adapter.place_order(request)


async def modify_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderModificationRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Modify open order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order modification request.

    Returns:
        Standard response containing modification result.
    """
    return await adapter.modify_order(request)


async def cancel_broker_order(
    adapter: BrokerAdapter,
    order_id: str,
    client_request_id: str | None = None,
) -> StandardResponse[BrokerOrderResult]:
    """Cancel open order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        order_id: Target order ID.
        client_request_id: Optional caller idempotency identifier.

    Returns:
        Standard response containing cancellation result.
    """
    return await adapter.cancel_order(order_id, client_request_id=client_request_id)


async def modify_broker_position(
    adapter: BrokerAdapter,
    request: BrokerPositionModificationRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Modify position stop loss / take profit on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Position modification request.

    Returns:
        Standard response containing modification result.
    """
    return await adapter.modify_position(request)


async def close_broker_position(
    adapter: BrokerAdapter,
    request: BrokerPositionCloseRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Close position on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Position close request.

    Returns:
        Standard response containing close result.
    """
    return await adapter.close_position(request)


async def calculate_broker_margin(
    adapter: BrokerAdapter,
    request: BrokerMarginRequest,
) -> StandardResponse[Decimal]:
    """Calculate required margin for potential trade.

    Args:
        adapter: Targeted broker adapter.
        request: Margin calculation request.

    Returns:
        Standard response containing required margin amount.
    """
    return await adapter.calculate_margin(request)


async def calculate_broker_profit(
    adapter: BrokerAdapter,
    request: BrokerProfitRequest,
) -> StandardResponse[Decimal]:
    """Calculate projected profit/loss for trade parameters.

    Args:
        adapter: Targeted broker adapter.
        request: Profit calculation request.

    Returns:
        Standard response containing calculated profit amount.
    """
    return await adapter.calculate_profit(request)


async def refresh_broker_session(adapter: BrokerAdapter) -> StandardResponse[None]:
    """Refresh one Broker session through its opaque adapter.

    Returns:
        The canonical refresh result.
    """
    return await adapter.refresh_session()


async def get_broker_server_time(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerServerTime]:
    """Get provider-reported server time through the root boundary.

    Returns:
        The canonical server-time result.
    """
    return await adapter.get_server_time()


def get_broker_connection_events(adapter: BrokerAdapter) -> object:
    """Return the opaque asynchronous connection-event stream."""
    return adapter.connection_events()


async def list_broker_accounts(
    adapter: BrokerAdapter, cursor: str | None = None, limit: int | None = None
) -> StandardResponse[BrokerPage[BrokerAccountInfo]]:
    """List provider-visible accounts through the root boundary.

    Returns:
        The canonical bounded account page.
    """
    return await adapter.list_accounts(cursor=cursor, limit=limit)


async def select_broker_account(
    adapter: BrokerAdapter, account_id: str
) -> StandardResponse[None]:
    """Select one provider account through the root boundary.

    Returns:
        The canonical selection result.
    """
    return await adapter.select_account(account_id)


async def list_broker_assets(
    adapter: BrokerAdapter, cursor: str | None = None, limit: int | None = None
) -> StandardResponse[BrokerPage[BrokerAssetInfo]]:
    """List provider-visible assets through the root boundary.

    Returns:
        The canonical bounded asset page.
    """
    return await adapter.list_assets(cursor=cursor, limit=limit)


async def get_broker_asset_info(
    adapter: BrokerAdapter, asset: str
) -> StandardResponse[BrokerAssetInfo]:
    """Get one provider asset through the root boundary.

    Returns:
        The canonical asset result.
    """
    return await adapter.get_asset_info(asset)


async def get_broker_commission_estimate(
    adapter: BrokerAdapter, request: BrokerOrderRequest
) -> StandardResponse[BrokerFeeEstimate]:
    """Get one provider commission estimate through the root boundary.

    Returns:
        The canonical commission-estimate result.
    """
    return await adapter.get_commission_estimate(request)


async def replace_broker_order(
    adapter: BrokerAdapter, request: BrokerOrderModificationRequest
) -> StandardResponse[BrokerOrderResult]:
    """Replace one provider order through the root boundary.

    Returns:
        The canonical replacement result.
    """
    return await adapter.replace_order(request)


# --- application Phase 0 contract transport and safe-order extensions ---


def build_broker_order_protection_request(
    order_id: str,
    idempotency_key: str,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    trailing_distance: Decimal | float | str | None = None,
    client_request_id: str | None = None,
) -> BrokerOrderProtectionRequest:
    """Build a BrokerOrderProtectionRequest instance (``feature``).

    Args:
        order_id: Target order identifier.
        idempotency_key: Explicit adapter-boundary idempotency key.
        stop_loss: Optional stop-loss price.
        take_profit: Optional take-profit price.
        trailing_distance: Optional trailing-stop distance.
        client_request_id: Optional caller request identifier.

    Returns:
        Configured BrokerOrderProtectionRequest instance.
    """
    return BrokerOrderProtectionRequest(
        order_id=order_id,
        idempotency_key=idempotency_key,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        trailing_distance=(
            Decimal(str(trailing_distance)) if trailing_distance is not None else None
        ),
        client_request_id=client_request_id,
    )


def build_broker_position_reduce_request(
    position_id: str,
    quantity: Decimal | float | str,
    quantity_unit: str,
    idempotency_key: str,
    client_request_id: str | None = None,
) -> BrokerPositionReductionRequest:
    """Build a BrokerPositionReductionRequest instance (``feature``).

    Args:
        position_id: Target position identifier.
        quantity: Quantity to reduce.
        quantity_unit: Provider quantity unit.
        idempotency_key: Explicit adapter-boundary idempotency key.
        client_request_id: Optional caller request identifier.

    Returns:
        Configured BrokerPositionReductionRequest instance.
    """
    return BrokerPositionReductionRequest(
        position_id=position_id,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
        idempotency_key=idempotency_key,
        client_request_id=client_request_id,
    )


async def attach_broker_protection(
    adapter: BrokerAdapter, request: BrokerOrderProtectionRequest
) -> StandardResponse[BrokerOrderResult]:
    """Attach bracketing protection to one order through the root boundary.

    Args:
        adapter: Targeted broker adapter.
        request: Order protection request.

    Returns:
        Standard response containing the protection attachment result.
    """
    return await adapter.attach_protection(request)


async def reduce_broker_position(
    adapter: BrokerAdapter, request: BrokerPositionReductionRequest
) -> StandardResponse[BrokerOrderResult]:
    """Reduce one open position by an explicit quantity through the root boundary.

    Args:
        adapter: Targeted broker adapter.
        request: Position reduction request.

    Returns:
        Standard response containing the reduction result.
    """
    return await adapter.reduce_position(request)


def get_broker_uncertainty(value: str) -> BrokerUncertainty:
    """Return the canonical BrokerUncertainty enum value.

    Args:
        value: Candidate uncertainty value.

    Returns:
        Validated BrokerUncertainty.
    """
    return BrokerUncertainty(value)


def get_broker_resubmission_policy(value: str) -> BrokerResubmissionPolicy:
    """Return the canonical BrokerResubmissionPolicy enum value.

    Args:
        value: Candidate policy value.

    Returns:
        Validated BrokerResubmissionPolicy.
    """
    return BrokerResubmissionPolicy(value)


# --- application Phase 0 contract-transport aliases (FEAT-BRK-16) ---
#
# The route-discipline feature owns the canonical ``build_route_plan``/
# ``parse_route_plan`` and ``build_failover_decision``/``parse_failover_decision``
# implementations. The package-root public API exposes them under the
# ``build_broker_*`` naming convention so the entire Brokers public surface
# shares one prefix while the function-only rule is preserved.


def build_broker_route_plan(
    *,
    plan_id: str,
    primary_broker: BrokerId | str,
    primary_environment: BrokerEnvironment | str,
    primary_readiness: str,
    backup_broker: BrokerId | str | None,
    backup_environment: BrokerEnvironment | str | None,
    backup_readiness: str | None,
    selected_route: str | None,
    route_state: str,
    write_failover_policy: str,
    created_at: datetime,
) -> dict[str, object]:
    """Build and hash a redacted RoutePlan v1 mapping (``feature``).

    Args:
        plan_id: Caller-owned plan identifier.
        primary_broker: Primary broker identifier.
        primary_environment: Primary broker environment.
        primary_readiness: Primary route health readiness.
        backup_broker: Optional backup broker identifier.
        backup_environment: Optional backup broker environment.
        backup_readiness: Optional backup route health readiness.
        selected_route: Selected route identifier, or ``None`` when unavailable.
        route_state: Aggregate route state verdict.
        write_failover_policy: Write failover policy.
        created_at: Aware UTC plan creation instant.

    Returns:
        RoutePlan v1 mapping.
    """
    from app.services.brokers.route_discipline.plans import build_route_plan

    return build_route_plan(
        plan_id=plan_id,
        primary_broker=primary_broker,
        primary_environment=primary_environment,
        primary_readiness=primary_readiness,
        backup_broker=backup_broker,
        backup_environment=backup_environment,
        backup_readiness=backup_readiness,
        selected_route=selected_route,
        route_state=route_state,
        write_failover_policy=write_failover_policy,
        created_at=created_at,
    )


def parse_broker_route_plan(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a RoutePlan v1 mapping and integrity hash (``feature``).

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached route plan.
    """
    from app.services.brokers.route_discipline.plans import parse_route_plan

    return parse_route_plan(value)


def build_broker_failover_decision(
    *,
    decision_id: str,
    plan_id: str,
    decision: str,
    active_broker: BrokerId | str | None,
    active_environment: BrokerEnvironment | str | None,
    write_permitted: bool,
    read_permitted: bool,
    reason: str,
    decided_at: datetime,
) -> dict[str, object]:
    """Build and hash a redacted FailoverDecision v1 mapping (``feature``).

    Args:
        decision_id: Caller-owned decision identifier.
        plan_id: Originating route plan identifier.
        decision: Deterministic failover decision.
        active_broker: Active broker after the decision, or ``None`` when blocked.
        active_environment: Active broker environment, or ``None`` when blocked.
        write_permitted: Whether the active route may submit new writes.
        read_permitted: Whether the active route may be read.
        reason: Short deterministic reason label.
        decided_at: Aware UTC decision instant.

    Returns:
        FailoverDecision v1 mapping.
    """
    from app.services.brokers.route_discipline.failover import build_failover_decision

    return build_failover_decision(
        decision_id=decision_id,
        plan_id=plan_id,
        decision=decision,
        active_broker=active_broker,
        active_environment=active_environment,
        write_permitted=write_permitted,
        read_permitted=read_permitted,
        reason=reason,
        decided_at=decided_at,
    )


def parse_broker_failover_decision(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a FailoverDecision v1 mapping and integrity hash (``feature``).

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached failover decision.
    """
    from app.services.brokers.route_discipline.failover import parse_failover_decision

    return parse_failover_decision(value)
