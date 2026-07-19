"""Finite Trading error taxonomy, mapping, and redaction boundary."""

import re
from collections.abc import Mapping

from pydantic import ValidationError as PydanticValidationError

from app.services.trading.contracts.models import (
    EnvelopeStatus,
    JsonValue,
    StandardTradingEnvelope,
)
from app.utils import (
    ExternalServiceError,
    HaruQuantError,
    logger,
    redact_mapping_value,
    redact_text_value,
    to_json_safe,
)
from app.utils import (
    ValidationError as UtilsValidationError,
)

_SAFE_DETAIL = re.compile(r"[^A-Z0-9_]+")
_TRADING_ERROR_CODES = frozenset(
    {
        "ADAPTER_INCOMPATIBLE",
        "AUDIT_FAILED",
        "BUDGET_BLOCKED",
        "CONFIGURATION_INVALID",
        "CONTRACT_CATALOG_CONFLICT",
        "GATE_BLOCKED",
        "IDEMPOTENCY_CONFLICT",
        "INVALID_DECIMAL",
        "INVALID_DRAFT",
        "INVALID_ENVELOPE",
        "INVALID_REBALANCE_REQUEST",
        "INVALID_REQUEST",
        "INVALID_ROUTE",
        "INVALID_TIME",
        "KILL_SWITCH_ACTIVE",
        "KILL_SWITCH_STALE",
        "KILL_SWITCH_UNKNOWN",
        "MALFORMED_RECEIPT",
        "PAYLOAD_NOT_JSON_SAFE",
        "PERMISSION_DENIED",
        "PERSISTENCE_FAILED",
        "PROVIDER_ERROR",
        "RECONCILIATION_REQUIRED",
        "SCOPE_MISMATCH",
        "SERVICE_UNAVAILABLE",
        "SIZE_MISMATCH",
        "STALE_EVIDENCE",
        "TIMEOUT",
        "TRADING_CONCURRENCY_CONFLICT",
        "UNKNOWN_ERROR",
        "UNKNOWN_OUTCOME",
        "VALIDATION_FAILED",
        "VERSION_CONFLICT",
        "WORKFLOW_TIMEOUT",
    }
)


def _safe_detail_token(details: str) -> str:
    """Convert redacted diagnostic text to a safe exception token.

    Args:
        details: Redacted diagnostic text.

    Returns:
        Uppercase symbolic detail accepted by ``HaruQuantError``.
    """
    logger.debug("Creating a bounded Trading error detail token")
    token = _SAFE_DETAIL.sub("_", details.upper()).strip("_")
    return f"DETAIL_{token}"[:128] if token else "TRADING_DOMAIN_ERROR"


def redact_trading_payload(payload: JsonValue) -> JsonValue:
    """Recursively redact a JSON-safe Trading boundary payload.

    Args:
        payload: JSON-safe payload to protect.

    Returns:
        Redacted JSON-safe payload without mutating the input.

    Raises:
        TradingError: If the payload cannot be represented safely.
    """
    logger.debug("Redacting a Trading boundary payload")
    try:
        safe = to_json_safe(payload)
        result = redact_mapping_value({"value": safe}).value
    except (TypeError, ValueError, UtilsValidationError) as error:
        logger.warning("Rejecting a non-JSON-safe Trading payload")
        raise TradingError(
            "PAYLOAD_NOT_JSON_SAFE",
            "Trading payload failed JSON-safe redaction",
        ) from error
    if not isinstance(result, dict):
        raise TradingError(
            "PAYLOAD_NOT_JSON_SAFE",
            "Trading payload redaction returned invalid evidence",
        )
    return to_json_safe(result["value"])


def _redacted_envelope_data(
    data: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Redact and narrow envelope data to a mutable mapping.

    Args:
        data: JSON-safe envelope material immediately before emission.

    Returns:
        Recursively redacted mapping.

    Raises:
        TradingError: If redaction does not produce a mapping.
    """
    logger.debug("Redacting Trading envelope data immediately before emission")
    result = redact_trading_payload(dict(data))
    if not isinstance(result, dict):
        raise TradingError(
            "PAYLOAD_NOT_JSON_SAFE",
            "Trading envelope data must remain a mapping after redaction",
        )
    return result


class TradingError(HaruQuantError):
    """Trading failure carrying a registered code and redacted trace context.

    Attributes:
        trading_code: Stable registered Trading error code.
        details: Redacted bounded diagnostic text.
        trace_context: Recursively redacted trace evidence.
    """

    def __init__(
        self,
        code: str,
        details: str,
        *,
        trace_context: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a finite redacted Trading failure.

        Args:
            code: Registered Trading error code.
            details: Human-readable diagnostic to redact and bound.
            trace_context: Optional JSON-safe trace evidence.

        Raises:
            ValueError: If ``code`` is not registered.
            TradingError: If trace context is not JSON-safe.
        """
        logger.error("Creating a redacted Trading failure: %s", code)
        if code not in _TRADING_ERROR_CODES:
            raise ValueError("code must be a registered Trading error code")
        redacted_details = str(redact_text_value(details).value)
        safe_context = redact_trading_payload(dict(trace_context or {}))
        if not isinstance(safe_context, dict):
            raise TradingError(
                "PAYLOAD_NOT_JSON_SAFE",
                "Trading trace context must be a mapping",
            )
        self.trading_code = code
        self.details = redacted_details
        self.trace_context = safe_context
        super().__init__(code, _safe_detail_token(redacted_details))


def _classify_error(error: Exception) -> tuple[str, str, bool, EnvelopeStatus]:
    """Classify an exception without exposing its raw message.

    Args:
        error: Exception crossing the Trading boundary.

    Returns:
        Error code, safe message, retry flag, and envelope status.
    """
    logger.debug("Classifying a Trading boundary failure")
    status: EnvelopeStatus
    if isinstance(error, TradingError):
        code = error.trading_code
        message = error.details
        retryable = False
        status = "unknown_outcome" if code == "UNKNOWN_OUTCOME" else "error"
    elif isinstance(error, PydanticValidationError | ValueError | TypeError):
        code = "VALIDATION_FAILED"
        message = "Trading input validation failed"
        retryable = False
        status = "error"
    elif isinstance(error, PermissionError):
        code = "PERMISSION_DENIED"
        message = "Trading permission was denied"
        retryable = False
        status = "error"
    elif isinstance(error, TimeoutError):
        code = "TIMEOUT"
        message = "Trading authority timed out"
        retryable = False
        status = "unknown_outcome"
    elif isinstance(error, ExternalServiceError | ConnectionError):
        code = "PROVIDER_ERROR"
        message = "Trading provider failed"
        retryable = False
        status = "unknown_outcome"
    elif isinstance(error, OSError):
        code = "PERSISTENCE_FAILED"
        message = "Trading persistence failed"
        retryable = False
        status = "error"
    else:
        code = "UNKNOWN_ERROR"
        message = "Trading failed safely"
        retryable = False
        status = "error"
    return code, message, retryable, status


def map_trading_error(
    error: Exception,
    context: Mapping[str, JsonValue],
) -> StandardTradingEnvelope:
    """Map a failure to the canonical envelope without raw exceptions.

    Args:
        error: Failure crossing a Trading boundary.
        context: Operation and trace evidence for the failure.

    Returns:
        Canonical redacted failure envelope.
    """
    logger.warning("Mapping a Trading failure to its canonical envelope")
    safe_context = redact_trading_payload(dict(context))
    if not isinstance(safe_context, dict):
        safe_context = {}
    code, message, retryable, status = _classify_error(error)
    error_row: dict[str, JsonValue] = {
        "code": code,
        "message": message,
        "field_path": safe_context.get("field_path"),
        "severity": "error",
        "retryable": retryable,
        "route": safe_context.get("route"),
        "provider_id": safe_context.get("provider_id"),
        "request_id": safe_context.get("request_id"),
        "correlation_id": safe_context.get("correlation_id"),
    }
    audit_metadata: dict[str, JsonValue] = {
        "operation": safe_context.get("operation", "unknown"),
        "request_id": safe_context.get("request_id"),
        "correlation_id": safe_context.get("correlation_id"),
        "route": safe_context.get("route"),
        "provider_id": safe_context.get("provider_id"),
        "redaction_applied": True,
    }
    return StandardTradingEnvelope(
        status=status,
        message=message,
        data=None,
        errors=(error_row,),
        warnings=(),
        audit_metadata=audit_metadata,
    )


__all__ = ["TradingError", "map_trading_error", "redact_trading_payload"]
