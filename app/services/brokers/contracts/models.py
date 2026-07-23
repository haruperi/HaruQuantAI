"""Immutable canonical broker inputs, outputs, results, and events."""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import ClassVar, Literal, cast

from pydantic import SecretStr

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.utils import (
    ValidationError as UtilsValidationError,
)
from app.utils import (
    format_utc_timestamp,
    redact_mapping_value,
    redact_text_value,
    validate_id,
)


def _text(value: str, name: str) -> None:
    """Handle text.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if not value.strip():
        message = f"{name} must not be empty"
        raise ValueError(message)


def _utc(value: datetime | None, name: str) -> None:
    """Handle utc.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if value is None:
        return
    try:
        format_utc_timestamp(value)
    except UtilsValidationError as error:
        message = f"{name} must be UTC-aware"
        raise ValueError(message) from error


def _finite(value: Decimal | None, name: str) -> None:
    """Handle finite.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if value is not None and not value.is_finite():
        message = f"{name} must be finite"
        raise ValueError(message)


def _positive(value: Decimal, name: str) -> None:
    """Handle positive.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    _finite(value, name)
    if value <= 0:
        message = f"{name} must be positive"
        raise ValueError(message)


def _non_negative(value: Decimal | None, name: str) -> None:
    """Handle non negative.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    _finite(value, name)
    if value is not None and value < 0:
        message = f"{name} must not be negative"
        raise ValueError(message)


def _optional_text(value: str | None, name: str) -> None:
    """Handle optional text.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.
    """
    if value is not None:
        _text(value, name)


def _choice(value: str, allowed: set[str], name: str) -> None:
    """Handle choice.

    Args:
        value: Value supplied to the operation.
        allowed: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if value not in allowed:
        message = f"unknown {name}"
        raise ValueError(message)


def _non_negative_float(value: float | None, name: str) -> None:
    """Handle non negative float.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if value is not None and (not math.isfinite(value) or value < 0):
        message = f"{name} must be finite and non-negative"
        raise ValueError(message)


def _request_id(value: str | None, name: str) -> None:
    """Handle request id.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    if value is None:
        return
    _text(value, name)
    try:
        validate_id(value, expected_prefix="req")
    except UtilsValidationError as error:
        message = f"{name} must be a valid req identifier"
        raise ValueError(message) from error


def _frozen[K, V](value: Mapping[K, V]) -> Mapping[K, V]:
    """Handle frozen.

    Args:
        value: Value supplied to the operation.

    Returns:
        The operation result.
    """
    return MappingProxyType(dict(value))


def _freeze_value(value: object) -> object:
    """Handle freeze value.

    Args:
        value: Value supplied to the operation.

    Returns:
        The operation result.
    """
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _redacted(value: Mapping[str, object], name: str) -> Mapping[str, object]:
    """Handle redacted.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Returns:
        The operation result.

    Raises:
        ValueError: If the documented operation cannot complete.
    """
    try:
        result = redact_mapping_value(value)
    except UtilsValidationError as error:
        message = f"{name} must be a bounded JSON-safe mapping"
        raise ValueError(message) from error
    if result.truncated_paths:
        message = f"{name} must not exceed redaction bounds"
        raise ValueError(message)
    frozen = _freeze_value(result.value)
    return cast("Mapping[str, object]", frozen)


class _Schema:
    """Stable schema metadata shared by all broker models."""

    CONTRACT_VERSION: ClassVar[str] = "v1"
    SCHEMA_ID: ClassVar[str]

    @property
    def contract_version(self) -> str:
        """Return compatibility version."""
        return self.CONTRACT_VERSION

    @property
    def schema_id(self) -> str:
        """Return namespaced schema identifier."""
        return self.SCHEMA_ID


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerConnectionConfig(_Schema):
    """Resolved configuration for one independent adapter."""

    SCHEMA_ID: ClassVar[str] = "brokers.connection_config.v1"
    broker_id: BrokerId
    environment: BrokerEnvironment
    provider_enabled: bool
    connect_timeout_sec: float
    request_timeout_sec: float
    transport_reconnect_max_attempts: int
    stream_buffer_size: int
    circuit_failure_threshold: int
    circuit_recovery_timeout_sec: float
    circuit_half_open_max_calls: int
    account_reference: str | None = None
    credentials: Mapping[str, SecretStr] | None = None
    endpoint: str | None = None
    auto_connect: bool = False
    probe_symbol: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerConnectionConfig invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        positive = (
            self.connect_timeout_sec,
            self.request_timeout_sec,
            self.stream_buffer_size,
            self.circuit_failure_threshold,
            self.circuit_recovery_timeout_sec,
            self.circuit_half_open_max_calls,
        )
        if any(not math.isfinite(value) or value <= 0 for value in positive):
            raise ValueError("timeouts, buffers, and circuit bounds must be positive")
        if self.transport_reconnect_max_attempts < 0:
            raise ValueError("reconnect attempts must not be negative")
        if self.credentials is not None:
            if any(
                not key.strip()
                or not isinstance(value, SecretStr)
                or not value.get_secret_value()
                for key, value in self.credentials.items()
            ):
                raise ValueError("credentials require named non-empty SecretStr values")
            object.__setattr__(self, "credentials", _frozen(self.credentials))
        _optional_text(self.account_reference, "account_reference")
        _optional_text(self.probe_symbol, "probe_symbol")
        _optional_text(self.endpoint, "endpoint")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerError(_Schema):
    """Canonical operational failure with redacted evidence."""

    SCHEMA_ID: ClassVar[str] = "brokers.error.v1"
    code: BrokerErrorCode
    message: str
    retryable: bool = False
    provider_code: str | None = None
    provider_message: str | None = None
    capability: BrokerCapabilityId | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerError invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.message, "message")
        _optional_text(self.provider_code, "provider_code")
        _optional_text(self.provider_message, "provider_message")
        for name in ("message", "provider_code", "provider_message"):
            value = getattr(self, name)
            if value is None:
                continue
            result = redact_text_value(value)
            if result.truncated_paths:
                message = f"{name} must not exceed redaction bounds"
                raise ValueError(message)
            object.__setattr__(self, name, cast("str", result.value))
        object.__setattr__(self, "details", _redacted(self.details, "details"))


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerResult[T](_Schema):
    """Truth-preserving canonical success/error envelope."""

    SCHEMA_ID: ClassVar[str] = "brokers.result.v1"
    status: Literal["success", "error"]
    broker: BrokerId
    operation: BrokerCapabilityId
    request_id: str
    timestamp: datetime
    environment: BrokerEnvironment
    adapter_version: str
    data: T | None = None
    error: BrokerError | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)
    latency_ms: float = 0.0
    provider_latency_ms: float | None = None
    adapter_overhead_ms: float = 0.0
    provider_api_version: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerResult invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.request_id, "request_id")
        _request_id(self.request_id, "request_id")
        _utc(self.timestamp, "timestamp")
        if self.status == "success" and self.error is not None:
            raise ValueError("success cannot contain an error")
        if self.status == "error" and (self.error is None or self.data is not None):
            raise ValueError("error status requires an error and null data")
        if self.status not in {"success", "error"}:
            raise ValueError("unknown result status")
        _non_negative_float(self.latency_ms, "latency_ms")
        _non_negative_float(self.provider_latency_ms, "provider_latency_ms")
        _non_negative_float(self.adapter_overhead_ms, "adapter_overhead_ms")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )

    @property
    def is_success(self) -> bool:
        """Return whether this result represents success."""
        return self.status == "success"


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPage[T](_Schema):
    """Bounded provider-native page."""

    SCHEMA_ID: ClassVar[str] = "brokers.page.v1"
    items: tuple[T, ...]
    limit: int
    next_cursor: str | None = None
    returned_count: int | None = None
    truncated: bool = False
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPage invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        count = len(self.items) if self.returned_count is None else self.returned_count
        if self.limit <= 0 or count != len(self.items) or count > self.limit:
            raise ValueError("page bounds are inconsistent")
        if self.next_cursor is not None and not self.truncated:
            raise ValueError("next cursor requires truncation")
        object.__setattr__(self, "returned_count", count)
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerCapability(_Schema):
    """Declared implementation and release state for one operation."""

    SCHEMA_ID: ClassVar[str] = "brokers.capability.v1"
    capability: BrokerCapabilityId
    implementation_status: Literal["IMPLEMENTED", "NOT_IMPLEMENTED"]
    availability: Literal["AVAILABLE", "UNAVAILABLE", "DEGRADED"]
    access_mode: Literal["READ", "WRITE", "READ_WRITE"]
    requirement: Literal["NONE", "AUTHENTICATION", "CONFIGURATION", "PERMISSION"]
    verification_status: Literal["TESTED_SANDBOX", "TESTED_LIVE", "NOT_TESTED"]
    execution_model: str
    verification_evidence: tuple[str, ...] = ()
    release_approval_reference: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerCapability invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _choice(
            self.implementation_status,
            {"IMPLEMENTED", "NOT_IMPLEMENTED"},
            "implementation_status",
        )
        _choice(
            self.availability,
            {"AVAILABLE", "UNAVAILABLE", "DEGRADED"},
            "availability",
        )
        _choice(self.access_mode, {"READ", "WRITE", "READ_WRITE"}, "access_mode")
        mutation_capabilities = {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
            BrokerCapabilityId.REPLACE_ORDER,
        }
        if self.capability in mutation_capabilities and self.access_mode != "WRITE":
            raise ValueError("mutation capability must use WRITE access mode")
        if self.capability not in mutation_capabilities and self.access_mode == "WRITE":
            raise ValueError("non-mutation capability cannot use WRITE access mode")
        _choice(
            self.requirement,
            {"NONE", "AUTHENTICATION", "CONFIGURATION", "PERMISSION"},
            "requirement",
        )
        _choice(
            self.verification_status,
            {"TESTED_SANDBOX", "TESTED_LIVE", "NOT_TESTED"},
            "verification_status",
        )
        _text(self.execution_model, "execution_model")
        for evidence in self.verification_evidence:
            _text(evidence, "verification_evidence")
        _optional_text(self.release_approval_reference, "release_approval_reference")
        _optional_text(self.reason, "reason")
        if (
            self.implementation_status == "NOT_IMPLEMENTED"
            and self.availability != "UNAVAILABLE"
        ):
            raise ValueError("unimplemented capability must be unavailable")
        # `WRITE` denotes an order mutation and carries the FR-BRK-010 release
        # gate. `READ_WRITE` denotes provider watch-list or subscription session
        # mutation, which places no order and is not subject to that gate.
        if (
            self.access_mode == "WRITE"
            and self.availability == "AVAILABLE"
            and (
                not self.verification_evidence
                or not self.release_approval_reference
                or self.verification_status == "NOT_TESTED"
            )
        ):
            raise ValueError("available writes require evidence and approval")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerFeatureFlags(_Schema):
    """Complete capability report for one profile/account."""

    SCHEMA_ID: ClassVar[str] = "brokers.feature_flags.v1"
    broker_id: BrokerId
    environment: BrokerEnvironment
    generated_at: datetime
    capabilities: Mapping[BrokerCapabilityId, BrokerCapability]
    adapter_version: str
    account_reference_redacted: str | None = None
    provider_api_version: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerFeatureFlags invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _utc(self.generated_at, "generated_at")
        _text(self.adapter_version, "adapter_version")
        _optional_text(self.account_reference_redacted, "account_reference_redacted")
        _optional_text(self.provider_api_version, "provider_api_version")
        if set(self.capabilities) != set(BrokerCapabilityId):
            raise ValueError("feature flags must include every capability")
        if any(key != value.capability for key, value in self.capabilities.items()):
            raise ValueError("capability keys must match declared capability values")
        object.__setattr__(self, "capabilities", _frozen(self.capabilities))


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerConnectionStatus(_Schema):
    """Detailed provider session state."""

    SCHEMA_ID: ClassVar[str] = "brokers.connection_status.v1"
    state: BrokerConnectionState
    transport_connected: bool
    environment: BrokerEnvironment
    session_generation: int
    observed_at: datetime
    application_authenticated: bool | None = None
    account_authenticated: bool | None = None
    trading_permitted: bool | None = None
    subscriptions_ready: bool | None = None
    maintenance: bool = False
    account_reference_redacted: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerConnectionStatus invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _utc(self.observed_at, "observed_at")
        if self.session_generation < 0:
            raise ValueError("session generation must not be negative")
        if self.state == BrokerConnectionState.READY and not self.transport_connected:
            raise ValueError("ready state requires verified transport")
        if not self.transport_connected and any(
            value is True
            for value in (
                self.application_authenticated,
                self.account_authenticated,
                self.trading_permitted,
                self.subscriptions_ready,
            )
        ):
            raise ValueError(
                "disconnected transport cannot report verified session state"
            )
        _optional_text(self.account_reference_redacted, "account_reference_redacted")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerConnectionEvent(_Schema):
    """One validated lifecycle transition."""

    SCHEMA_ID: ClassVar[str] = "brokers.connection_event.v1"
    previous_state: BrokerConnectionState
    new_state: BrokerConnectionState
    timestamp: datetime
    session_generation: int
    reason: str | None = None
    reconnect_attempt: int | None = None
    resynchronization_required: bool = False

    def __post_init__(self) -> None:
        """Validate the immutable BrokerConnectionEvent invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _utc(self.timestamp, "timestamp")
        if self.previous_state == self.new_state:
            raise ValueError("event must record a real transition")
        if self.session_generation < 0:
            raise ValueError("session generation must not be negative")
        if self.reconnect_attempt is not None and self.reconnect_attempt < 0:
            raise ValueError("reconnect attempt must not be negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPlatformInfo(_Schema):
    """Redacted provider platform information."""

    SCHEMA_ID: ClassVar[str] = "brokers.platform_info.v1"
    broker_id: BrokerId
    provider_name: str
    product_profile: str
    environment: BrokerEnvironment
    observed_at: datetime
    api_or_terminal_version: str | None = None
    endpoint_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPlatformInfo invariants."""
        _text(self.provider_name, "provider_name")
        _text(self.product_profile, "product_profile")
        _optional_text(self.api_or_terminal_version, "api_or_terminal_version")
        _utc(self.observed_at, "observed_at")
        object.__setattr__(
            self,
            "endpoint_metadata",
            _redacted(self.endpoint_metadata, "endpoint_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPermissions(_Schema):
    """Provider-reported permissions preserving unknown state."""

    SCHEMA_ID: ClassVar[str] = "brokers.permissions.v1"
    observed_at: datetime
    market_data_read: bool | None = None
    account_read: bool | None = None
    trade_write: bool | None = None
    subscription: bool | None = None
    provider_permissions: Mapping[str, bool | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPermissions invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _utc(self.observed_at, "observed_at")
        if any(not key.strip() for key in self.provider_permissions):
            raise ValueError("provider permission names must not be empty")
        object.__setattr__(
            self, "provider_permissions", _frozen(self.provider_permissions)
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerAccountInfo(_Schema):
    """Direct provider account information."""

    SCHEMA_ID: ClassVar[str] = "brokers.account_info.v1"
    account_id: str
    retrieved_at: datetime
    account_reference_redacted: str | None = None
    currency: str | None = None
    balance: Decimal | None = None
    equity: Decimal | None = None
    margin: Decimal | None = None
    free_margin: Decimal | None = None
    status: str | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerAccountInfo invariants."""
        _text(self.account_id, "account_id")
        _optional_text(self.account_reference_redacted, "account_reference_redacted")
        _optional_text(self.currency, "currency")
        _optional_text(self.status, "status")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        for name in ("balance", "equity", "margin", "free_margin"):
            _finite(getattr(self, name), name)


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerBalance(_Schema):
    """Provider-reported balance with explicit unit."""

    SCHEMA_ID: ClassVar[str] = "brokers.balance.v1"
    asset: str
    unit: str
    retrieved_at: datetime
    total: Decimal | None = None
    available: Decimal | None = None
    locked: Decimal | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerBalance invariants."""
        _text(self.asset, "asset")
        _text(self.unit, "unit")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        for name in ("total", "available", "locked"):
            _finite(getattr(self, name), name)


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerAssetInfo(_Schema):
    """Provider-native asset metadata."""

    SCHEMA_ID: ClassVar[str] = "brokers.asset_info.v1"
    asset_id: str
    provider_name: str | None = None
    precision: int | None = None
    unit: str | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerAssetInfo invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.asset_id, "asset_id")
        _optional_text(self.provider_name, "provider_name")
        _optional_text(self.unit, "unit")
        if self.precision is not None and self.precision < 0:
            raise ValueError("precision must not be negative")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerSymbolInfo(_Schema):
    """Exact provider-native symbol metadata without aliases."""

    SCHEMA_ID: ClassVar[str] = "brokers.symbol_info.v1"
    provider_symbol: str
    product_profile: str
    price_unit: str
    quantity_unit: str
    base_asset: str | None = None
    quote_asset: str | None = None
    price_precision: int | None = None
    quantity_precision: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    price_step: Decimal | None = None
    min_quantity: Decimal | None = None
    max_quantity: Decimal | None = None
    quantity_step: Decimal | None = None
    trading_flags: Mapping[str, bool | None] = field(default_factory=dict)
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerSymbolInfo invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        for name in (
            "provider_symbol",
            "product_profile",
            "price_unit",
            "quantity_unit",
        ):
            _text(getattr(self, name), name)
        _optional_text(self.base_asset, "base_asset")
        _optional_text(self.quote_asset, "quote_asset")
        for name in ("price_precision", "quantity_precision"):
            value = getattr(self, name)
            if value is not None and value < 0:
                message = f"{name} must not be negative"
                raise ValueError(message)
        for name in (
            "min_price",
            "max_price",
            "price_step",
            "min_quantity",
            "max_quantity",
            "quantity_step",
        ):
            _non_negative(getattr(self, name), name)
        if self.price_step == 0 or self.quantity_step == 0:
            raise ValueError("price and quantity steps must be positive when supplied")
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("minimum price exceeds maximum price")
        if (
            self.min_quantity is not None
            and self.max_quantity is not None
            and self.min_quantity > self.max_quantity
        ):
            raise ValueError("minimum quantity exceeds maximum quantity")
        if any(not key.strip() for key in self.trading_flags):
            raise ValueError("trading flag names must not be empty")
        object.__setattr__(self, "trading_flags", _frozen(self.trading_flags))
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerMarketStatus(_Schema):
    """Provider-reported market status."""

    SCHEMA_ID: ClassVar[str] = "brokers.market_status.v1"
    symbol: str
    status: Literal["OPEN", "CLOSED", "HALTED", "UNKNOWN"]
    retrieved_at: datetime
    provider_timestamp: datetime | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerMarketStatus invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.symbol, "symbol")
        if self.status not in {"OPEN", "CLOSED", "HALTED", "UNKNOWN"}:
            raise ValueError("unknown market status")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        _optional_text(self.reason, "reason")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerTradingSession(_Schema):
    """Provider-supplied trading window."""

    SCHEMA_ID: ClassVar[str] = "brokers.trading_session.v1"
    symbol: str
    opens_at: datetime
    closes_at: datetime
    provider_timezone: str | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerTradingSession invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.symbol, "symbol")
        _utc(self.opens_at, "opens_at")
        _utc(self.closes_at, "closes_at")
        if self.opens_at >= self.closes_at:
            raise ValueError("trading session must close after it opens")
        _optional_text(self.provider_timezone, "provider_timezone")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerQuote(_Schema):
    """Latest genuine provider quote."""

    SCHEMA_ID: ClassVar[str] = "brokers.quote.v1"
    symbol: str
    price_unit: str
    quantity_unit: str
    retrieved_at: datetime
    bid: Decimal | None = None
    ask: Decimal | None = None
    last_price: Decimal | None = None
    bid_quantity: Decimal | None = None
    ask_quantity: Decimal | None = None
    provider_sequence_id: str | int | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerQuote invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.symbol, "symbol")
        _text(self.price_unit, "price_unit")
        _text(self.quantity_unit, "quantity_unit")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        for name in ("bid", "ask", "last_price"):
            _finite(getattr(self, name), name)
        for name in ("bid_quantity", "ask_quantity"):
            _non_negative(getattr(self, name), name)
        if self.bid is None and self.ask is None and self.last_price is None:
            raise ValueError("quote requires at least one genuine price")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("quote bid must not exceed ask")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerTick(_Schema):
    """One genuine provider tick."""

    SCHEMA_ID: ClassVar[str] = "brokers.tick.v1"
    symbol: str
    event_timestamp: datetime
    provider_receipt_timestamp: datetime
    price_unit: str
    quantity_unit: str
    tick_type: Literal["TRADE", "QUOTE", "BLOCK", "UNKNOWN"] = "UNKNOWN"
    provider_sequence_id: str | int | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    last_price: Decimal | None = None
    bid_quantity: Decimal | None = None
    ask_quantity: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerTick invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.symbol, "symbol")
        _text(self.price_unit, "price_unit")
        _text(self.quantity_unit, "quantity_unit")
        _utc(self.event_timestamp, "event_timestamp")
        _utc(self.provider_receipt_timestamp, "provider_receipt_timestamp")
        if self.tick_type not in {"TRADE", "QUOTE", "BLOCK", "UNKNOWN"}:
            raise ValueError("unknown tick type")
        for name in ("bid", "ask", "last_price"):
            _finite(getattr(self, name), name)
        for name in ("bid_quantity", "ask_quantity"):
            _non_negative(getattr(self, name), name)
        if self.bid is None and self.ask is None and self.last_price is None:
            raise ValueError("tick requires at least one genuine price")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("tick bid must not exceed ask")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerBar(_Schema):
    """One genuine provider OHLC bar with optional spread evidence."""

    SCHEMA_ID: ClassVar[str] = "brokers.bar.v1"
    symbol: str
    opening_timestamp: datetime
    closing_timestamp: datetime
    is_closed: bool
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    provider_timeframe: str
    requested_timeframe: str
    price_unit: str
    quantity_unit: str
    trade_volume: Decimal | None = None
    tick_volume: Decimal | None = None
    spread: Decimal | None = None
    spread_unit: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerBar invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        for name in (
            "symbol",
            "provider_timeframe",
            "requested_timeframe",
            "price_unit",
            "quantity_unit",
        ):
            _text(getattr(self, name), name)
        _utc(self.opening_timestamp, "opening_timestamp")
        _utc(self.closing_timestamp, "closing_timestamp")
        if self.opening_timestamp >= self.closing_timestamp:
            raise ValueError("bar must close after it opens")
        for name in ("open", "high", "low", "close"):
            _finite(getattr(self, name), name)
        if self.high < max(self.open, self.low, self.close):
            raise ValueError("bar high is inconsistent")
        if self.low > min(self.open, self.high, self.close):
            raise ValueError("bar low is inconsistent")
        _non_negative(self.trade_volume, "trade_volume")
        _non_negative(self.tick_volume, "tick_volume")
        _non_negative(self.spread, "spread")
        _optional_text(self.spread_unit, "spread_unit")
        if (self.spread is None) != (self.spread_unit is None):
            raise ValueError("spread and spread_unit must be provided together")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderBook(_Schema):
    """Provider order-book snapshot or delta."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_book.v1"
    symbol: str
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]
    is_snapshot: bool
    resnapshot_required: bool
    event_timestamp: datetime
    price_unit: str
    quantity_unit: str
    first_sequence_id: int | None = None
    last_sequence_id: int | None = None
    checksum: str | None = None
    depth_truncation: int | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrderBook invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.symbol, "symbol")
        _text(self.price_unit, "price_unit")
        _text(self.quantity_unit, "quantity_unit")
        _utc(self.event_timestamp, "event_timestamp")
        for side_name, levels in (("bids", self.bids), ("asks", self.asks)):
            for price, quantity in levels:
                _finite(price, f"{side_name} price")
                _positive(quantity, f"{side_name} quantity")
        if (
            self.first_sequence_id is not None
            and self.last_sequence_id is not None
            and self.first_sequence_id > self.last_sequence_id
        ):
            raise ValueError("order-book sequence range is inconsistent")
        if self.depth_truncation is not None and self.depth_truncation <= 0:
            raise ValueError("depth_truncation must be positive")
        _optional_text(self.checksum, "checksum")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerSubscriptionInfo(_Schema):
    """Immutable adapter-owned subscription metadata."""

    SCHEMA_ID: ClassVar[str] = "brokers.subscription_info.v1"
    subscription_id: str
    capability: BrokerCapabilityId
    symbols: tuple[str, ...]
    created_at: datetime
    buffer_size: int
    delivery_sequence: int = 0
    resynchronization_required: bool = False
    active: bool = True

    def __post_init__(self) -> None:
        """Validate the immutable BrokerSubscriptionInfo invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.subscription_id, "subscription_id")
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("subscription symbols must be non-empty and unique")
        for symbol in self.symbols:
            _text(symbol, "symbol")
        _utc(self.created_at, "created_at")
        if self.buffer_size <= 0:
            raise ValueError("buffer_size must be positive")
        if self.delivery_sequence < 0:
            raise ValueError("delivery_sequence must not be negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPosition(_Schema):
    """Direct provider position state."""

    SCHEMA_ID: ClassVar[str] = "brokers.position.v1"
    position_id: str
    symbol: str
    side: Literal["LONG", "SHORT", "UNKNOWN"]
    quantity: Decimal
    quantity_unit: str
    retrieved_at: datetime
    state: Literal["OPEN", "CLOSED", "UNKNOWN"] = "UNKNOWN"
    open_price: Decimal | None = None
    current_price: Decimal | None = None
    profit: Decimal | None = None
    swap: Decimal | None = None
    currency: str | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPosition invariants."""
        _choice(self.side, {"LONG", "SHORT", "UNKNOWN"}, "position side")
        _choice(self.state, {"OPEN", "CLOSED", "UNKNOWN"}, "position state")
        _text(self.position_id, "position_id")
        _text(self.symbol, "symbol")
        _text(self.quantity_unit, "quantity_unit")
        _non_negative(self.quantity, "quantity")
        for name in (
            "open_price",
            "current_price",
            "profit",
            "swap",
            "stop_loss",
            "take_profit",
        ):
            _finite(getattr(self, name), name)
        _optional_text(self.currency, "currency")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderFilter(_Schema):
    """Structural order filter without selection policy."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_filter.v1"
    symbol: str | None = None
    status: str | None = None
    side: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    account_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrderFilter invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        for name in ("symbol", "status", "side", "account_reference"):
            _optional_text(getattr(self, name), name)
        _utc(self.start, "start")
        _utc(self.end, "end")
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("filter start must not follow end")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPositionFilter(_Schema):
    """Structural position filter."""

    SCHEMA_ID: ClassVar[str] = "brokers.position_filter.v1"
    symbol: str | None = None
    side: str | None = None
    account_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPositionFilter invariants."""
        for name in ("symbol", "side", "account_reference"):
            _optional_text(getattr(self, name), name)


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrder(_Schema):
    """Direct provider order state."""

    SCHEMA_ID: ClassVar[str] = "brokers.order.v1"
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL", "UNKNOWN"]
    order_type: str
    state: str
    quantity: Decimal
    filled: Decimal
    remaining: Decimal
    quantity_unit: str
    retrieved_at: datetime
    client_request_id: str | None = None
    client_order_id: str | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str | None = None
    product_profile: str | None = None
    provider_timestamp: datetime | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrder invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _choice(self.side, {"BUY", "SELL", "UNKNOWN"}, "order side")
        _choice(
            self.order_type,
            {"MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP", "UNKNOWN"},
            "order type",
        )
        _choice(
            self.state,
            {
                "PENDING",
                "ACCEPTED",
                "PARTIALLY_FILLED",
                "FILLED",
                "CANCELLED",
                "REJECTED",
                "EXPIRED",
                "UNKNOWN",
            },
            "order state",
        )
        for name in (
            "order_id",
            "symbol",
            "order_type",
            "state",
            "quantity_unit",
        ):
            _text(getattr(self, name), name)
        _request_id(self.client_request_id, "client_request_id")
        for name in (
            "client_order_id",
            "time_in_force",
            "product_profile",
        ):
            _optional_text(getattr(self, name), name)
        for name in ("quantity", "filled", "remaining"):
            _non_negative(getattr(self, name), name)
        for name in ("price", "stop_price"):
            _finite(getattr(self, name), name)
        if self.filled > self.quantity or self.remaining > self.quantity:
            raise ValueError("order quantities exceed requested quantity")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerDeal(_Schema):
    """Direct provider deal/fill."""

    SCHEMA_ID: ClassVar[str] = "brokers.deal.v1"
    deal_id: str
    symbol: str
    side: Literal["BUY", "SELL", "UNKNOWN"]
    quantity: Decimal
    quantity_unit: str
    price: Decimal
    partial: bool
    retrieved_at: datetime
    order_id: str | None = None
    position_id: str | None = None
    fee: Decimal | None = None
    fee_currency: str | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerDeal invariants."""
        _choice(self.side, {"BUY", "SELL", "UNKNOWN"}, "deal side")
        _text(self.deal_id, "deal_id")
        _text(self.symbol, "symbol")
        _text(self.quantity_unit, "quantity_unit")
        _optional_text(self.order_id, "order_id")
        _optional_text(self.position_id, "position_id")
        _optional_text(self.fee_currency, "fee_currency")
        _positive(self.quantity, "quantity")
        _finite(self.price, "price")
        _finite(self.fee, "fee")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerAccountTransaction(_Schema):
    """Provider-reported account transaction."""

    SCHEMA_ID: ClassVar[str] = "brokers.account_transaction.v1"
    transaction_id: str
    transaction_type: str
    asset: str
    currency: str
    amount: Decimal
    provider_timestamp: datetime
    retrieved_at: datetime
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerAccountTransaction invariants."""
        _choice(
            self.transaction_type,
            {
                "DEPOSIT",
                "WITHDRAWAL",
                "FEE",
                "COMMISSION",
                "SWAP",
                "INTEREST",
                "TRANSFER",
                "ADJUSTMENT",
                "UNKNOWN",
            },
            "transaction type",
        )
        for name in ("transaction_id", "transaction_type", "asset", "currency"):
            _text(getattr(self, name), name)
        _finite(self.amount, "amount")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderRequest(_Schema):
    """Complete caller-defined single-order request."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_request.v1"
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]
    quantity: Decimal
    quantity_unit: str
    environment: BrokerEnvironment
    account_reference: str | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    expiration: datetime | None = None
    deviation_points: int | None = None
    client_request_id: str | None = None
    client_order_id: str | None = None
    label: str | None = None
    magic: int | None = None
    comment: str | None = None

    def __post_init__(self) -> None:  # noqa: C901, PLR0912
        """Validate the immutable BrokerOrderRequest invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _choice(self.side, {"BUY", "SELL"}, "order side")
        _choice(
            self.order_type,
            {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"},
            "order_type",
        )
        if self.time_in_force is not None:
            _choice(
                self.time_in_force,
                {"GTC", "IOC", "FOK", "GTD", "DAY"},
                "time_in_force",
            )
        _text(self.symbol, "symbol")
        _text(self.quantity_unit, "quantity_unit")
        _positive(self.quantity, "quantity")
        for name in ("limit_price", "stop_price", "stop_loss", "take_profit"):
            _finite(getattr(self, name), name)
        _utc(self.expiration, "expiration")
        # Cross-field order type & price validation (REV-BRK-005)
        if self.order_type == "MARKET":
            if self.limit_price is not None or self.stop_price is not None:
                raise ValueError(
                    "MARKET order must not specify limit_price or stop_price"
                )
        elif self.order_type == "LIMIT":
            if self.limit_price is None:
                raise ValueError("LIMIT order requires limit_price")
            if self.stop_price is not None:
                raise ValueError("LIMIT order must not specify stop_price")
            _positive(self.limit_price, "limit_price")
        elif self.order_type == "STOP":
            if self.stop_price is None:
                raise ValueError("STOP order requires stop_price")
            if self.limit_price is not None:
                raise ValueError("STOP order must not specify limit_price")
            _positive(self.stop_price, "stop_price")
        elif self.order_type == "STOP_LIMIT":
            if self.limit_price is None or self.stop_price is None:
                raise ValueError(
                    "STOP_LIMIT order requires both limit_price and stop_price"
                )
            _positive(self.limit_price, "limit_price")
            _positive(self.stop_price, "stop_price")

        # Time-in-force vs expiration matrix (REV-BRK-005)
        if self.time_in_force == "GTD":
            if self.expiration is None:
                raise ValueError("GTD order requires expiration datetime")
        elif self.expiration is not None:
            raise ValueError("Only GTD orders may specify expiration datetime")

        if self.deviation_points is not None and self.deviation_points < 0:
            raise ValueError("deviation_points must not be negative")
        if self.magic is not None and self.magic < 0:
            raise ValueError("magic must not be negative")
        _request_id(self.client_request_id, "client_request_id")
        for name in (
            "account_reference",
            "client_order_id",
            "label",
            "comment",
        ):
            _optional_text(getattr(self, name), name)


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderModificationRequest(_Schema):
    """Caller changes for exactly one provider order."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_modification_request.v1"
    order_id: str
    client_request_id: str | None = None
    quantity: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    time_in_force: Literal["GTC", "IOC", "FOK", "GTD", "DAY"] | None = None
    expiration: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrderModificationRequest invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.order_id, "order_id")
        _request_id(self.client_request_id, "client_request_id")
        modifications = (
            self.quantity,
            self.limit_price,
            self.stop_price,
            self.stop_loss,
            self.take_profit,
            self.time_in_force,
            self.expiration,
        )
        if all(value is None for value in modifications):
            raise ValueError("order modification requires at least one supplied field")
        if self.quantity is not None:
            _positive(self.quantity, "quantity")
        for name in ("limit_price", "stop_price", "stop_loss", "take_profit"):
            _finite(getattr(self, name), name)
        if self.time_in_force is not None:
            _choice(
                self.time_in_force,
                {"GTC", "IOC", "FOK", "GTD", "DAY"},
                "time_in_force",
            )
        _utc(self.expiration, "expiration")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderCheck(_Schema):
    """Provider validation that is never final acceptance."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_check.v1"
    accepted_for_submission: bool
    is_final_acceptance: Literal[False] = False
    provider_code: str | None = None
    provider_message: str | None = None
    estimated_margin: Decimal | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrderCheck invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if self.is_final_acceptance is not False:
            raise ValueError("order check cannot be final acceptance")
        _optional_text(self.provider_code, "provider_code")
        _optional_text(self.provider_message, "provider_message")
        _finite(self.estimated_margin, "estimated_margin")
        for warning in self.warnings:
            _text(warning, "warning")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerOrderResult(_Schema):
    """Explicit provider mutation outcome."""

    SCHEMA_ID: ClassVar[str] = "brokers.order_result.v1"
    acknowledged: bool
    outcome: Literal["ACCEPTED", "REJECTED", "UNKNOWN", "PARTIAL"]
    retrieved_at: datetime
    order_id: str | None = None
    deal_ids: tuple[str, ...] = ()
    filled_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    average_price: Decimal | None = None
    provider_code: str | None = None
    provider_message: str | None = None
    provider_timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerOrderResult invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if self.outcome not in {"ACCEPTED", "REJECTED", "UNKNOWN", "PARTIAL"}:
            raise ValueError("unknown order outcome")
        if self.acknowledged != (self.outcome != "UNKNOWN"):
            raise ValueError("acknowledgement conflicts with order outcome")
        if self.outcome in {"ACCEPTED", "PARTIAL"} and self.order_id is None:
            raise ValueError("accepted outcome requires provider order identifier")
        _optional_text(self.order_id, "order_id")
        for deal_id in self.deal_ids:
            _text(deal_id, "deal_id")
        for name in ("filled_quantity", "remaining_quantity"):
            _non_negative(getattr(self, name), name)
        _finite(self.average_price, "average_price")
        _optional_text(self.provider_code, "provider_code")
        _optional_text(self.provider_message, "provider_message")
        _utc(self.provider_timestamp, "provider_timestamp")
        _utc(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPositionModificationRequest(_Schema):
    """Stop/take-profit changes for one position."""

    SCHEMA_ID: ClassVar[str] = "brokers.position_modification_request.v1"
    position_id: str
    client_request_id: str | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPositionModificationRequest invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _text(self.position_id, "position_id")
        _request_id(self.client_request_id, "client_request_id")
        if self.stop_loss is None and self.take_profit is None:
            raise ValueError("position modification requires stop loss or take profit")
        _finite(self.stop_loss, "stop_loss")
        _finite(self.take_profit, "take_profit")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerPositionCloseRequest(_Schema):
    """Exact close/reduction request for one position."""

    SCHEMA_ID: ClassVar[str] = "brokers.position_close_request.v1"
    position_id: str
    quantity: Decimal
    quantity_unit: str
    client_request_id: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerPositionCloseRequest invariants."""
        _text(self.position_id, "position_id")
        _text(self.quantity_unit, "quantity_unit")
        _positive(self.quantity, "quantity")
        _request_id(self.client_request_id, "client_request_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerMarginRequest(_Schema):
    """Provider-native margin request."""

    SCHEMA_ID: ClassVar[str] = "brokers.margin_request.v1"
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: Decimal
    quantity_unit: str
    product_profile: str
    price: Decimal | None = None
    account_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerMarginRequest invariants."""
        _choice(self.side, {"BUY", "SELL"}, "margin side")
        for name in ("symbol", "quantity_unit", "product_profile"):
            _text(getattr(self, name), name)
        _positive(self.quantity, "quantity")
        _finite(self.price, "price")
        _optional_text(self.account_reference, "account_reference")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerProfitRequest(_Schema):
    """Provider-native profit request."""

    SCHEMA_ID: ClassVar[str] = "brokers.profit_request.v1"
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: Decimal
    quantity_unit: str
    open_price: Decimal
    close_price: Decimal
    product_profile: str
    account_reference: str | None = None

    def __post_init__(self) -> None:
        """Validate the immutable BrokerProfitRequest invariants."""
        _choice(self.side, {"BUY", "SELL"}, "profit side")
        for name in ("symbol", "quantity_unit", "product_profile"):
            _text(getattr(self, name), name)
        _positive(self.quantity, "quantity")
        _finite(self.open_price, "open_price")
        _finite(self.close_price, "close_price")
        _optional_text(self.account_reference, "account_reference")


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerFeeEstimate(_Schema):
    """Provider-native fee estimate."""

    SCHEMA_ID: ClassVar[str] = "brokers.fee_estimate.v1"
    amount: Decimal
    currency_or_unit: str
    provider_code: str | None = None
    provider_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the immutable BrokerFeeEstimate invariants."""
        _finite(self.amount, "amount")
        _text(self.currency_or_unit, "currency_or_unit")
        _optional_text(self.provider_code, "provider_code")
        object.__setattr__(
            self,
            "provider_metadata",
            _redacted(self.provider_metadata, "provider_metadata"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BrokerServerTime(_Schema):
    """Provider clock and local timing evidence."""

    SCHEMA_ID: ClassVar[str] = "brokers.server_time.v1"
    provider_time: datetime
    local_send_time: datetime
    local_receive_time: datetime
    estimated_clock_offset_ms: float
    round_trip_latency_ms: float

    def __post_init__(self) -> None:
        """Validate the immutable BrokerServerTime invariants.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        _utc(self.provider_time, "provider_time")
        _utc(self.local_send_time, "local_send_time")
        _utc(self.local_receive_time, "local_receive_time")
        if self.local_send_time > self.local_receive_time:
            raise ValueError("local receive time must not precede send time")
        if not math.isfinite(self.estimated_clock_offset_ms):
            raise ValueError("estimated clock offset must be finite")
        _non_negative_float(self.round_trip_latency_ms, "round_trip_latency_ms")
