"""Conservative normalization of external authority mutation responses."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.services.trading.contracts import ExecutionReceipt, TradingError
from app.services.trading.contracts.models import JsonValue
from app.utils import logger

_RECEIPT_TEXT_FIELDS = (
    "receipt_id",
    "intent_id",
    "client_order_id",
    "route",
    "authority",
    "request_id",
    "correlation_id",
    "authority_timestamp",
    "received_at",
)


def _require_mapping(raw: JsonValue) -> Mapping[str, JsonValue]:
    """Require a mapping response that can carry trace evidence.

    Args:
        raw: JSON-safe authority response.

    Returns:
        Response mapping.

    Raises:
        TradingError: If the response has no representable structure.
    """
    logger.debug("Validating authority response structure")
    if not isinstance(raw, dict):
        raise TradingError(
            "MALFORMED_RECEIPT", "Authority response is not representable"
        )
    return raw


def _require_text(raw: Mapping[str, JsonValue], field: str) -> str:
    """Read one required response identity field.

    Args:
        raw: Authority response mapping.
        field: Required response field.

    Returns:
        Validated response text.

    Raises:
        TradingError: If identity evidence is absent or malformed.
    """
    logger.debug("Reading authority response identity %s", field)
    value = raw.get(field)
    if not isinstance(value, str) or not value or value != value.strip():
        raise TradingError(
            "MALFORMED_RECEIPT", "Authority response identity is missing"
        )
    return value


def _optional_text(raw: Mapping[str, JsonValue], field: str) -> str | None:
    """Read one optional response text field.

    Args:
        raw: Authority response mapping.
        field: Optional response field.

    Returns:
        Validated text or ``None``.

    Raises:
        TradingError: If supplied text is malformed.
    """
    logger.debug("Reading optional authority response field %s", field)
    value = raw.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value or value != value.strip():
        raise TradingError("MALFORMED_RECEIPT", "Authority response text is malformed")
    return value


def _decimal(
    raw: Mapping[str, JsonValue],
    field: str,
    *,
    required: bool,
) -> Decimal | None:
    """Read an exact non-negative response Decimal.

    Args:
        raw: Authority response mapping.
        field: Numeric response field.
        required: Whether absence is unrepresentable.

    Returns:
        Exact Decimal or ``None``.

    Raises:
        TradingError: If numeric evidence is absent, unsafe, or invalid.
    """
    logger.debug("Reading exact authority response Decimal %s", field)
    value = raw.get(field)
    if value is None:
        if required:
            raise TradingError("MALFORMED_RECEIPT", "Authority quantity is missing")
        return None
    if isinstance(value, bool | float) or not isinstance(value, int | str):
        raise TradingError("MALFORMED_RECEIPT", "Authority numeric value is unsafe")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise TradingError(
            "MALFORMED_RECEIPT",
            "Authority numeric value is invalid",
        ) from error
    if not result.is_finite() or result < 0:
        raise TradingError("MALFORMED_RECEIPT", "Authority numeric value is invalid")
    return result


def _timestamp(raw: Mapping[str, JsonValue], field: str) -> datetime:
    """Read one timezone-aware UTC response timestamp.

    Args:
        raw: Authority response mapping.
        field: Timestamp response field.

    Returns:
        Parsed UTC timestamp.

    Raises:
        TradingError: If the timestamp is missing, invalid, or not UTC.
    """
    logger.debug("Reading authority response timestamp %s", field)
    value = _require_text(raw, field)
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise TradingError(
            "MALFORMED_RECEIPT",
            "Authority timestamp is invalid",
        ) from error
    offset = result.utcoffset()
    if result.tzinfo is None or offset is None:
        raise TradingError("MALFORMED_RECEIPT", "Authority timestamp is not UTC")
    if offset.total_seconds() != 0:
        raise TradingError("MALFORMED_RECEIPT", "Authority timestamp is not UTC")
    return result


def _deal_ids(raw: Mapping[str, JsonValue]) -> tuple[str, ...]:
    """Read bounded provider deal identifiers.

    Args:
        raw: Authority response mapping.

    Returns:
        Validated provider deal identifiers.

    Raises:
        TradingError: If identifiers are malformed.
    """
    logger.debug("Reading authority provider deal identifiers")
    value = raw.get("provider_deal_ids", [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise TradingError("MALFORMED_RECEIPT", "Authority deal identities are invalid")
    return tuple(item for item in value if isinstance(item, str))


def _classify_status(
    raw: Mapping[str, JsonValue],
    provider_order_id: str | None,
) -> tuple[str, str, bool]:
    """Classify explicit and ambiguous authority outcomes.

    Args:
        raw: Authority response mapping.
        provider_order_id: Optional proven provider order identity.

    Returns:
        Receipt status, response classification, and reconciliation requirement.
    """
    logger.debug("Classifying finite authority mutation outcome")
    if any(
        raw.get(flag) is True for flag in ("timed_out", "ambiguous", "rate_limited")
    ):
        classification = "ambiguous"
        if raw.get("rate_limited") is True:
            classification = "rate_limited"
        elif raw.get("timed_out") is True:
            classification = "timeout"
        return "unknown_outcome", classification, True
    outcome = raw.get("status")
    if outcome == "success":
        if provider_order_id is None:
            return "unknown_outcome", "malformed_success", True
        return "accepted", "confirmed", False
    if outcome in {
        "accepted",
        "rejected",
        "partial",
        "filled",
        "cancelled",
        "unknown_outcome",
    }:
        reconciliation_required = outcome == "unknown_outcome"
        return str(outcome), "confirmed", reconciliation_required
    return "unknown_outcome", "malformed_response", True


def classify_authority_response(
    raw: JsonValue,
    capability: Mapping[str, JsonValue],
) -> ExecutionReceipt:
    """Return a conservative immutable receipt for one authority response.

    Args:
        raw: JSON-safe normalized authority response with required trace context.
        capability: Validated authority response and retry-policy declarations.

    Returns:
        Immutable finite execution receipt.

    Raises:
        TradingError: If the response lacks enough evidence to be represented.
    """
    logger.info("Classifying Trading authority response")
    response = _require_mapping(raw)
    for field in _RECEIPT_TEXT_FIELDS:
        _require_text(response, field)
    if capability.get("malformed_response_policy") != "unknown_outcome":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Response policy is unsafe")
    if capability.get("mutation_retry_policy") != "reconcile_before_retry":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Mutation retry policy is unsafe")
    provider_order_id = _optional_text(response, "provider_order_id")
    status, classification, reconciliation_required = _classify_status(
        response,
        provider_order_id,
    )
    requested_quantity = _decimal(response, "requested_quantity", required=True)
    filled_quantity = _decimal(response, "filled_quantity", required=False)
    if requested_quantity is None:
        raise TradingError("MALFORMED_RECEIPT", "Requested quantity is missing")
    return ExecutionReceipt(
        receipt_id=_require_text(response, "receipt_id"),
        intent_id=_require_text(response, "intent_id"),
        client_order_id=_require_text(response, "client_order_id"),
        route=_require_text(response, "route"),  # type: ignore[arg-type]
        authority=_require_text(response, "authority"),
        provider_order_id=provider_order_id,
        provider_deal_ids=_deal_ids(response),
        status=status,  # type: ignore[arg-type]
        requested_quantity=requested_quantity,
        filled_quantity=filled_quantity or Decimal(0),
        average_price=_decimal(response, "average_price", required=False),
        authority_timestamp=_timestamp(response, "authority_timestamp"),
        received_at=_timestamp(response, "received_at"),
        response_classification=classification,
        retry_safe=False,
        reconciliation_required=reconciliation_required,
        request_id=_require_text(response, "request_id"),
        correlation_id=_require_text(response, "correlation_id"),
    )


__all__ = ["classify_authority_response"]
