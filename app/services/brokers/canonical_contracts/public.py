"""Public construction and inspection operations for canonical Broker contracts."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from app.services.brokers.canonical_contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerResubmissionPolicy,
    BrokerUncertainty,
)
from app.services.brokers.canonical_contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
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
    BrokerOrderRequest,
    BrokerOrderRequestV2,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)

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
    "order_request_v2": BrokerOrderRequestV2,
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


def build_broker_order_request_v2(
    *, provider_specification: object, **fields: object
) -> object:
    """Build one exact provider-bound Broker order request v2.

    Args:
        provider_specification: Opaque Brokers-owned specification snapshot.
        **fields: Complete v2 order fields including independent policies.

    Returns:
        Immutable opaque Broker order request v2.

    Raises:
        TypeError: If revision evidence has an invalid type.
        ValueError: If a policy is unsupported by the bound revision.
    """
    from app.services.brokers.metatrader.specifications import (
        get_provider_specification_snapshot_field,
    )

    fill_policy = fields.get("fill_policy")
    time_policy = fields.get("time_policy")
    filling_modes = get_provider_specification_snapshot_field(
        provider_specification, "filling_modes"
    )
    expiration_modes = get_provider_specification_snapshot_field(
        provider_specification, "expiration_modes"
    )
    if not isinstance(filling_modes, (tuple, list)) or fill_policy not in filling_modes:
        raise ValueError("fill_policy is unsupported by provider specification")
    if (
        not isinstance(expiration_modes, (tuple, list))
        or time_policy not in expiration_modes
    ):
        raise ValueError("time_policy is unsupported by provider specification")
    checksum = get_provider_specification_snapshot_field(
        provider_specification, "checksum"
    )
    if not isinstance(checksum, str):
        raise TypeError("provider specification checksum is invalid")
    return BrokerOrderRequestV2(
        **fields,  # type: ignore[arg-type]
        provider_specification_checksum=checksum,
    )


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
    position_id: str, quantity: Decimal | float | str, quantity_unit: str
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
        symbol=symbol, status=status, start=start_time, end=end_time
    )


def build_broker_position_filter(symbol: str | None = None) -> BrokerPositionFilter:
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
