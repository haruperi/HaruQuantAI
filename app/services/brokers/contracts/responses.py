"""Brokers-specific construction of canonical standard responses."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal, cast

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.contracts.error_catalog import BROKER_ERROR_CATALOG
from app.services.brokers.contracts.models import BrokerError  # noqa: TC001
from app.utils import (
    build_response_metadata,
    error_response,
    format_utc_timestamp,
    get_execution_ms,
    success_response,
    to_json_safe,
)

type JsonValue = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

_TRADE_OPERATIONS = frozenset(
    {
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
        BrokerCapabilityId.REPLACE_ORDER,
    }
)
_STATE_MUTATION_OPERATIONS = frozenset(
    {
        BrokerCapabilityId.CONNECT,
        BrokerCapabilityId.DISCONNECT,
        BrokerCapabilityId.RECONNECT,
        BrokerCapabilityId.REFRESH_SESSION,
        BrokerCapabilityId.SELECT_SYMBOL,
        BrokerCapabilityId.SELECT_ACCOUNT,
        BrokerCapabilityId.SUBSCRIBE_QUOTES,
        BrokerCapabilityId.SUBSCRIBE_BARS,
        BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
        BrokerCapabilityId.UNSUBSCRIBE,
        *_TRADE_OPERATIONS,
    }
)
_LOCAL_READ_OPERATIONS = frozenset(
    {
        BrokerCapabilityId.GET_CONNECTION_STATUS,
        BrokerCapabilityId.GET_LAST_ERROR,
        BrokerCapabilityId.LIST_SUBSCRIPTIONS,
        BrokerCapabilityId.SUPPORTS,
    }
)
_NETWORK_OPERATIONS = frozenset(BrokerCapabilityId) - {
    BrokerCapabilityId.CONNECTION_EVENTS,
    BrokerCapabilityId.GET_CONNECTION_STATUS,
    BrokerCapabilityId.GET_LAST_ERROR,
    BrokerCapabilityId.LIST_SUBSCRIPTIONS,
    BrokerCapabilityId.SUPPORTS,
}


def _risk_level(operation: BrokerCapabilityId) -> RiskLevel:
    """Return static invocation risk for one broker operation.

    Args:
        operation: Canonical broker capability.

    Returns:
        Static invocation-risk classification.
    """
    if operation in _TRADE_OPERATIONS:
        return "critical"
    if operation is BrokerCapabilityId.CHECK_ORDER:
        return "medium"
    if operation in _LOCAL_READ_OPERATIONS:
        return "none"
    return "low"


def _error_details(error: BrokerError) -> Mapping[str, JsonValue]:
    """Preserve the complete former BrokerError evidence.

    Args:
        error: Canonical Brokers failure.

    Returns:
        JSON-safe structured error details.
    """
    return {
        "retryable": error.retryable,
        "provider_code": error.provider_code,
        "provider_message": error.provider_message,
        "capability": (None if error.capability is None else error.capability.value),
        "legacy_details": {
            str(key): cast("JsonValue", to_json_safe(value))
            for key, value in error.details.items()
        },
    }


def build_broker_response[T](
    *,
    broker: BrokerId,
    operation: BrokerCapabilityId,
    request_id: str,
    timestamp: datetime,
    environment: BrokerEnvironment,
    adapter_version: str,
    start_time: int,
    data: T | None = None,
    error: BrokerError | None = None,
    provider_metadata: Mapping[str, object] | None = None,
    provider_latency_ms: float | None = None,
    provider_api_version: str | None = None,
    name: str | None = None,
    risk_level: RiskLevel | None = None,
    read_only: bool | None = None,
    requires_network: bool | None = None,
) -> StandardResponse[T]:
    """Build one lossless standard Brokers operation response.

    Args:
        broker: Exact provider/profile identifier.
        operation: Canonical operation identifier.
        request_id: Canonical request trace identity.
        timestamp: UTC completion timestamp retained from the former envelope.
        environment: Exact configured provider environment.
        adapter_version: Adapter implementation version.
        start_time: Starting ``time.perf_counter_ns`` value.
        data: Raw successful result.
        error: Canonical Brokers failure.
        provider_metadata: Redacted provider-specific evidence.
        provider_latency_ms: Measured provider-call duration.
        provider_api_version: Provider API or terminal version.
        name: Optional stable operation-name override.
        risk_level: Optional static risk override.
        read_only: Optional read-only override.
        requires_network: Optional network-trait override.

    Returns:
        Validated standard response retaining all former envelope evidence.
    """
    execution_ms = get_execution_ms(start_time)
    bounded_provider_latency = provider_latency_ms
    if bounded_provider_latency is not None:
        bounded_provider_latency = min(
            round(max(bounded_provider_latency, 0.0), 3),
            execution_ms,
        )
    adapter_overhead_ms = round(
        execution_ms - (bounded_provider_latency or 0.0),
        3,
    )
    extensions: Mapping[str, JsonValue] = {
        "broker": broker.value,
        "operation": operation.value,
        "timestamp": format_utc_timestamp(timestamp),
        "environment": environment.value,
        "adapter_version": adapter_version,
        "provider_metadata": {
            str(key): cast("JsonValue", to_json_safe(value))
            for key, value in (provider_metadata or {}).items()
        },
        "latency_ms": execution_ms,
        "provider_latency_ms": bounded_provider_latency,
        "adapter_overhead_ms": adapter_overhead_ms,
        "provider_api_version": provider_api_version,
        "legacy_contract_version": "v1",
        "legacy_schema_id": "brokers.result.v1",
    }
    metadata = build_response_metadata(
        name=name or f"brokers.adapter.{operation.value}",
        domain="brokers",
        risk_level=risk_level or _risk_level(operation),
        request_id=request_id,
        start_time=start_time,
        read_only=(
            operation not in _STATE_MUTATION_OPERATIONS
            if read_only is None
            else read_only
        ),
        writes_file=False,
        modifies_database=False,
        places_trade=operation in _TRADE_OPERATIONS,
        requires_network=(
            operation in _NETWORK_OPERATIONS
            if requires_network is None
            else requires_network
        ),
        extensions=extensions,
    )
    if error is None:
        return success_response(
            data,
            message=f"Broker {operation.value} completed",
            metadata=metadata,
        )
    return error_response(
        code=error.code.value,
        details=_error_details(error),
        message=error.message,
        metadata=metadata,
        catalog=BROKER_ERROR_CATALOG,
    )


def broker_start_time() -> int:
    """Return a monotonic start value for a Brokers public operation.

    Returns:
        Current ``time.perf_counter_ns`` value.
    """
    return time.perf_counter_ns()


__all__ = ["BROKER_ERROR_CATALOG", "broker_start_time", "build_broker_response"]
