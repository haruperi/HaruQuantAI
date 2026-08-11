"""Finite Trading error taxonomy, mapping, and redaction boundary."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal

from pydantic import ValidationError as PydanticValidationError

from app.services.trading.contracts.responses import (
    error_trading_response,
    success_trading_response,
)

if TYPE_CHECKING:
    from app.services.trading.contracts.models import JsonValue
from app.utils import (
    get_logger,
    redact_mapping_value,
    redact_text_value,
    to_json_safe,
)

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]


class HaruQuantError(Exception):
    """Local safe Trading error base."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize a local safe Trading error.

        Args:
            code: Error code string.
            detail: Diagnostic detail message.
        """
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


class ExternalServiceError(HaruQuantError):
    """Trading-owned external-service error."""


logger = get_logger(__name__)

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


def _redact_trading_payload_value(payload: JsonValue) -> JsonValue:
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
    except (TypeError, ValueError, Exception) as error:
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


def redact_trading_payload(payload: JsonValue) -> StandardResponse[JsonValue]:
    """Redact one Trading payload and return it in ``StandardResponse.data``.

    Args:
        payload: JSON-safe payload to protect.

    Returns:
        Standard response containing the redacted raw payload.
    """
    safe = _redact_trading_payload_value(payload)
    return success_trading_response(
        safe,
        operation="trading.redact_trading_payload",
        message="Trading payload redacted",
        risk_level="low",
        read_only=True,
    )


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
    result = _redact_trading_payload_value(dict(data))
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
        safe_context = _redact_trading_payload_value(dict(trace_context or {}))
        if not isinstance(safe_context, dict):
            raise TradingError(
                "PAYLOAD_NOT_JSON_SAFE",
                "Trading trace context must be a mapping",
            )
        self.trading_code = code
        self.details = redacted_details
        self.trace_context = safe_context
        super().__init__(code, _safe_detail_token(redacted_details))


def _classify_error(error: Exception) -> tuple[str, str]:
    """Classify an exception without exposing its raw message.

    Args:
        error: Exception crossing the Trading boundary.

    Returns:
        Error code and safe message.
    """
    logger.debug("Classifying a Trading boundary failure")
    if isinstance(error, TradingError):
        code = error.trading_code
        message = error.details
    elif isinstance(error, PydanticValidationError | ValueError | TypeError):
        code = "VALIDATION_FAILED"
        message = "Trading input validation failed"
    elif isinstance(error, PermissionError):
        code = "PERMISSION_DENIED"
        message = "Trading permission was denied"
    elif isinstance(error, TimeoutError):
        code = "UNKNOWN_OUTCOME"
        message = "Trading authority timed out"
    elif isinstance(error, ExternalServiceError | ConnectionError):
        code = "UNKNOWN_OUTCOME"
        message = "Trading provider failed"
    elif isinstance(error, OSError):
        code = "PERSISTENCE_FAILED"
        message = "Trading persistence failed"
    else:
        code = "UNKNOWN_ERROR"
        message = "Trading failed safely"
    return code, message


def map_trading_error[T](
    error: Exception,
    context: Mapping[str, JsonValue],
) -> StandardResponse[T]:
    """Map a failure to a redacted standard Trading response.

    Args:
        error: Failure crossing a Trading boundary.
        context: Operation and trace evidence for the failure.

    Returns:
        Canonical redacted failure response.
    """
    logger.warning("Mapping a Trading failure to its canonical envelope")
    safe_context = _redact_trading_payload_value(dict(context))
    if not isinstance(safe_context, dict):
        safe_context = {}
    code, message = _classify_error(error)
    details: dict[str, JsonValue] = dict(safe_context)
    if isinstance(error, TradingError):
        details["detail"] = error.details
        details.update(error.trace_context)
    request_id = safe_context.get("request_id")
    correlation_id = safe_context.get("correlation_id")
    return error_trading_response(
        code=code,
        details=details,
        operation=str(safe_context.get("operation", "trading.map_trading_error")),
        message=message,
        risk_level="high",
        request_id=request_id if isinstance(request_id, str) else None,
        correlation_id=(correlation_id if isinstance(correlation_id, str) else None),
        read_only=True,
        legacy_status="unknown_outcome" if code == "UNKNOWN_OUTCOME" else None,
    )


__all__ = ["TradingError", "map_trading_error", "redact_trading_payload"]
