"""Authoritative immutable Brokers error catalogue."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.services.brokers.contracts.enums import BrokerErrorCode


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable broker-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


_ERROR_DEFINITIONS = (
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_UNKNOWN.value,
        domain="brokers",
        description="Explicit broker or profile identifier is not registered",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Select a registered broker profile",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_CONFIGURATION_INVALID.value,
        domain="brokers",
        description="Broker connection configuration is invalid or inconsistent",
        category="configuration",
        severity="error",
        retryable=False,
        operator_action="Correct the broker profile and connection configuration",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_AUTHENTICATION_FAILED.value,
        domain="brokers",
        description="Provider authentication or credential verification failed",
        category="authentication",
        severity="error",
        retryable=False,
        operator_action="Verify provider credentials and authentication readiness",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_AUTHORIZATION_FAILED.value,
        domain="brokers",
        description="Authenticated broker session lacks a required permission",
        category="authorization",
        severity="error",
        retryable=False,
        operator_action="Verify provider account permissions",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_NOT_CONNECTED.value,
        domain="brokers",
        description="A session-required operation was requested while disconnected",
        category="connection",
        severity="error",
        retryable=False,
        operator_action="Establish and verify the broker session",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_CONNECTION_FAILED.value,
        domain="brokers",
        description="Broker transport or provider session could not be established",
        category="connection",
        severity="error",
        retryable=False,
        operator_action="Inspect provider connectivity and session readiness",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_CONNECTION_LOST.value,
        domain="brokers",
        description="An established broker transport connection was lost",
        category="connection",
        severity="error",
        retryable=False,
        operator_action="Re-establish the session before another operation",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_TIMEOUT.value,
        domain="brokers",
        description="A bounded broker operation exceeded its timeout",
        category="timeout",
        severity="error",
        retryable=False,
        operator_action="Inspect provider latency and configured timeout bounds",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_RATE_LIMITED.value,
        domain="brokers",
        description="The provider explicitly rate limited the operation",
        category="rate_limit",
        severity="error",
        retryable=False,
        operator_action="Observe provider rate-limit evidence before another request",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_BACKPRESSURE.value,
        domain="brokers",
        description="A bounded broker request or event queue reached capacity",
        category="capacity",
        severity="error",
        retryable=False,
        operator_action="Resynchronize the affected stream or reduce request pressure",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_CIRCUIT_OPEN.value,
        domain="brokers",
        description="The broker transport circuit is open",
        category="circuit",
        severity="error",
        retryable=False,
        operator_action="Wait for deterministic circuit recovery readiness",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED.value,
        domain="brokers",
        description="The requested broker capability is unavailable",
        category="capability",
        severity="error",
        retryable=False,
        operator_action="Use a capability declared available for the selected profile",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND.value,
        domain="brokers",
        description="The provider did not find the requested symbol",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Verify the provider-native symbol identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND.value,
        domain="brokers",
        description="The provider did not find the requested account",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Verify the provider account identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_ORDER_NOT_FOUND.value,
        domain="brokers",
        description="The provider did not find the requested order",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Reconcile and verify the provider order identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_POSITION_NOT_FOUND.value,
        domain="brokers",
        description="The provider did not find the requested position",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Reconcile and verify the provider position identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_DEAL_NOT_FOUND.value,
        domain="brokers",
        description="The provider did not find the requested deal",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Reconcile and verify the provider deal identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_REQUEST_INVALID.value,
        domain="brokers",
        description="The canonical broker request is structurally invalid",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Correct the request before transmission",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_REQUEST_REJECTED.value,
        domain="brokers",
        description="The provider explicitly rejected a transmitted request",
        category="rejection",
        severity="error",
        retryable=False,
        operator_action="Inspect redacted provider rejection evidence",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_MARKET_CLOSED.value,
        domain="brokers",
        description="The provider reports the relevant market or session closed",
        category="market_state",
        severity="error",
        retryable=False,
        operator_action="Wait for provider-reported market availability",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN.value,
        domain="brokers",
        description="The provider reports insufficient margin",
        category="funds",
        severity="error",
        retryable=False,
        operator_action="Reduce exposure or restore sufficient margin",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_INSUFFICIENT_FUNDS.value,
        domain="brokers",
        description="The provider reports insufficient funds or balance",
        category="funds",
        severity="error",
        retryable=False,
        operator_action="Reduce the request or restore sufficient funds",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_UNKNOWN_OUTCOME.value,
        domain="brokers",
        description=(
            "A broker mutation may have occurred without reliable acknowledgement"
        ),
        category="unknown_outcome",
        severity="critical",
        retryable=False,
        operator_action="Reconcile provider state before any further mutation",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_PROVIDER_ERROR.value,
        domain="brokers",
        description="The provider reported an unclassified operational error",
        category="provider",
        severity="error",
        retryable=False,
        operator_action="Inspect redacted provider evidence",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_RESPONSE_INVALID.value,
        domain="brokers",
        description="The provider response is malformed or cannot be mapped safely",
        category="provider_response",
        severity="error",
        retryable=False,
        operator_action="Inspect the provider contract and redacted response evidence",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_SUBSCRIPTION_FAILED.value,
        domain="brokers",
        description="A supported provider subscription could not be established",
        category="subscription",
        severity="error",
        retryable=False,
        operator_action="Inspect provider subscription readiness",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_MAINTENANCE_MODE.value,
        domain="brokers",
        description="Provider maintenance prevents the requested operation",
        category="maintenance",
        severity="error",
        retryable=False,
        operator_action="Wait for provider maintenance to end",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_SUBSCRIPTION_RESYNC_REQUIRED.value,
        domain="brokers",
        description="Lossless subscription continuation requires resynchronization",
        category="subscription",
        severity="error",
        retryable=False,
        operator_action="Create a fresh provider snapshot and subscription",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND.value,
        domain="brokers",
        description="The adapter does not own the requested subscription",
        category="not_found",
        severity="error",
        retryable=False,
        operator_action="Verify the adapter-scoped subscription identifier",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_DEPENDENCY_MISSING.value,
        domain="brokers",
        description="A selected broker provider dependency is unavailable",
        category="dependency",
        severity="error",
        retryable=False,
        operator_action="Install the declared provider dependency and version",
    ),
    ErrorDefinition(
        code=BrokerErrorCode.BROKER_SESSION_CHANGED.value,
        domain="brokers",
        description="Provider evidence belongs to an earlier broker session generation",
        category="session",
        severity="error",
        retryable=False,
        operator_action="Discard stale evidence and resynchronize the active session",
    ),
)

BROKER_ERROR_CATALOG = MappingProxyType(
    {definition.code: definition for definition in _ERROR_DEFINITIONS}
)


def get_broker_error_catalog() -> MappingProxyType[str, ErrorDefinition]:
    """Return the authoritative immutable Brokers error catalogue."""
    return BROKER_ERROR_CATALOG


__all__ = ["BROKER_ERROR_CATALOG", "get_broker_error_catalog"]
