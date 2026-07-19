"""Fail-closed authority capability validation for Trading dispatch."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from app.services.trading.contracts import OrderIntent, TradingError
from app.services.trading.contracts.models import JsonValue
from app.utils import logger

BROKER_OPERATION_TIMEOUT_SECONDS = Decimal(10)


def _require_text(capability: Mapping[str, JsonValue], field: str) -> str:
    """Read one required trimmed capability declaration.

    Args:
        capability: Authority capability evidence.
        field: Required declaration name.

    Returns:
        Validated declaration text.

    Raises:
        TradingError: If the declaration is absent or malformed.
    """
    logger.debug("Validating Trading authority capability field %s", field)
    value = capability.get(field)
    if not isinstance(value, str) or not value or value != value.strip():
        raise TradingError("ADAPTER_INCOMPATIBLE", "Authority capability is incomplete")
    return value


def _require_string_list(
    capability: Mapping[str, JsonValue],
    field: str,
) -> list[str]:
    """Read one required non-empty string-list declaration.

    Args:
        capability: Authority capability evidence.
        field: Required declaration name.

    Returns:
        Validated list declaration.

    Raises:
        TradingError: If the declaration is absent or malformed.
    """
    logger.debug("Validating Trading authority capability list %s", field)
    value = capability.get(field)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise TradingError("ADAPTER_INCOMPATIBLE", "Authority capability is incomplete")
    return [item for item in value if isinstance(item, str)]


def _validate_timeout(
    capability: Mapping[str, JsonValue],
    operation_timeout_seconds: Decimal,
) -> None:
    """Validate the ratified broker operation timeout declaration.

    Args:
        capability: Authority capability evidence.
        operation_timeout_seconds: Validated injected runtime timeout.

    Raises:
        TradingError: If timeout evidence is absent, unsafe, or unapproved.
    """
    logger.debug("Validating Trading broker operation timeout declaration")
    raw_timeout = capability.get("operation_timeout_seconds")
    if isinstance(raw_timeout, bool | float) or not isinstance(raw_timeout, int | str):
        raise TradingError("ADAPTER_INCOMPATIBLE", "Authority timeout is invalid")
    try:
        timeout = Decimal(raw_timeout)
    except InvalidOperation as error:
        raise TradingError(
            "ADAPTER_INCOMPATIBLE",
            "Authority timeout is invalid",
        ) from error
    if (
        not isinstance(operation_timeout_seconds, Decimal)
        or not operation_timeout_seconds.is_finite()
        or operation_timeout_seconds <= 0
        or timeout != operation_timeout_seconds
    ):
        raise TradingError("ADAPTER_INCOMPATIBLE", "Authority timeout is not approved")


def validate_adapter_capability(
    intent: OrderIntent,
    capability: Mapping[str, JsonValue],
    *,
    operation_timeout_seconds: Decimal,
) -> None:
    """Validate every mandatory authority declaration before mutation.

    Args:
        intent: Complete deterministic executable intent.
        capability: Approved Broker feature and adapter policy evidence.
        operation_timeout_seconds: Validated exact runtime timeout.

    Raises:
        TradingError: If any provider, schema, action, order-type, security,
            timeout, malformed-response, rate-limit, retry, or redaction
            declaration is absent or incompatible.
    """
    logger.info("Validating adapter capability for intent %s", intent.client_order_id)
    provider_id = _require_text(capability, "provider_id")
    if intent.provider_id is None or provider_id != intent.provider_id:
        raise TradingError("ADAPTER_INCOMPATIBLE", "Provider is not approved")
    if _require_text(capability, "contract_version") != "v1":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter contract is incompatible")
    if _require_text(capability, "schema_id") != "brokers.adapter.v1":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter schema is incompatible")
    _require_text(capability, "provider_api_version")
    if intent.action not in _require_string_list(capability, "supported_actions"):
        raise TradingError("ADAPTER_INCOMPATIBLE", "Trading action is unsupported")
    if intent.order_type not in _require_string_list(
        capability,
        "supported_order_types",
    ):
        raise TradingError("ADAPTER_INCOMPATIBLE", "Intent order type is unsupported")
    if _require_text(capability, "security_profile") != "approved":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Security profile is not approved")
    _validate_timeout(capability, operation_timeout_seconds)
    if _require_text(capability, "malformed_response_policy") != "unknown_outcome":
        raise TradingError(
            "ADAPTER_INCOMPATIBLE",
            "Malformed-response policy is unsafe",
        )
    _require_text(capability, "rate_limit_policy")
    if _require_text(capability, "mutation_retry_policy") != "reconcile_before_retry":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Mutation retry policy is unsafe")
    if capability.get("redaction_applied") is not True:
        raise TradingError("ADAPTER_INCOMPATIBLE", "Redaction evidence is required")


__all__ = ["BROKER_OPERATION_TIMEOUT_SECONDS", "validate_adapter_capability"]
