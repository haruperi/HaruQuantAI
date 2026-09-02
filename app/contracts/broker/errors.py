"""Broker domain errors and failure models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

type BrokerFailureCode = Literal[
    "BROKER_VALIDATION_FAILED",
    "BROKER_PROFILE_UNSUPPORTED",
    "BROKER_ENVIRONMENT_MISMATCH",
    "BROKER_SESSION_NOT_READY",
    "BROKER_OPERATION_REJECTED",
    "BROKER_OUTCOME_UNKNOWN",
    "BROKER_PAGINATION_INVALID",
    "CREDENTIALS_MISSING",
    "CAPABILITY_UNAVAILABLE",
]


class BrokerErrorCode(StrEnum):
    """Standardized broker operational error codes."""

    BROKER_CONNECTION_FAILED = "BROKER_CONNECTION_FAILED"
    BROKER_ACCOUNT_NOT_FOUND = "BROKER_ACCOUNT_NOT_FOUND"
    BROKER_OK = "BROKER_OK"
    BROKER_NOT_CONNECTED = "BROKER_NOT_CONNECTED"
    BROKER_REQUEST_INVALID = "BROKER_REQUEST_INVALID"
    BROKER_RESPONSE_INVALID = "BROKER_RESPONSE_INVALID"
    BROKER_CAPABILITY_UNSUPPORTED = "BROKER_CAPABILITY_UNSUPPORTED"
    BROKER_ORDER_NOT_FOUND = "BROKER_ORDER_NOT_FOUND"
    BROKER_SYMBOL_NOT_FOUND = "BROKER_SYMBOL_NOT_FOUND"
    BROKER_POSITION_NOT_FOUND = "BROKER_POSITION_NOT_FOUND"
    BROKER_DEAL_NOT_FOUND = "BROKER_DEAL_NOT_FOUND"
    BROKER_TRADE_DISABLED = "BROKER_TRADE_DISABLED"
    BROKER_TIMEOUT = "BROKER_TIMEOUT"
    BROKER_AUTHENTICATION_FAILED = "BROKER_AUTHENTICATION_FAILED"
    BROKER_MARKET_CLOSED = "BROKER_MARKET_CLOSED"
    BROKER_INSUFFICIENT_FUNDS = "BROKER_INSUFFICIENT_FUNDS"
    BROKER_INSUFFICIENT_MARGIN = "BROKER_INSUFFICIENT_MARGIN"
    BROKER_REQUEST_REJECTED = "BROKER_REQUEST_REJECTED"
    BROKER_INVALID_VOLUME = "BROKER_INVALID_VOLUME"
    BROKER_INVALID_PRICE = "BROKER_INVALID_PRICE"
    BROKER_INVALID_STOPS = "BROKER_INVALID_STOPS"
    BROKER_UNSUPPORTED_FILL_MODE = "BROKER_UNSUPPORTED_FILL_MODE"
    BROKER_ORDER_REJECTED = "BROKER_ORDER_REJECTED"
    BROKER_ORDER_CANCELLED = "BROKER_ORDER_CANCELLED"
    BROKER_NETWORK_ERROR = "BROKER_NETWORK_ERROR"
    BROKER_PROVIDER_ERROR = "BROKER_PROVIDER_ERROR"
    BROKER_CONFIGURATION_ERROR = "BROKER_CONFIGURATION_ERROR"
    BROKER_RESOURCE_EXHAUSTED = "BROKER_RESOURCE_EXHAUSTED"
    BROKER_INTERNAL_ERROR = "BROKER_INTERNAL_ERROR"
    BROKER_CIRCUIT_OPEN = "BROKER_CIRCUIT_OPEN"
    BROKER_RATE_LIMIT_EXCEEDED = "BROKER_RATE_LIMIT_EXCEEDED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


@dataclass(slots=True, frozen=True)
class BrokerError:
    """Structured error object for broker operations."""

    code: BrokerErrorCode | str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    capability: Any = None


class BrokerFailure(WireModel):
    """Structured failure envelope shared by every broker capability."""

    request_id: Uuid7
    code: BrokerFailureCode
    problem: ProblemDetails
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "BrokerFailure": BrokerFailure,
}


class _ProviderResponseError(Exception):
    pass


class _RequestValidationError(Exception):
    pass


class _ProviderUnavailableError(Exception):
    pass
