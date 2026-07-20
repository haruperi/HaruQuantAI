"""Deterministic error-code mapping for the trading service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.exceptions`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Trading, and provides a single redacted mapping
helper for official Trading tool boundaries.
"""

from collections.abc import Mapping
from random import random
from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class TradingError(Exception):
    """Base error for deterministic trading execution failures."""

    code = "BROKER_UNAVAILABLE"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class TradingValidationError(TradingError):
    """Validation failure in trading domain."""

    code = "VALIDATION_FAILED"


class TradingExternalServiceError(TradingError):
    """External service failure in trading domain."""

    code = "SERVICE_UNAVAILABLE"


TRADING_ERROR_CODES: frozenset[str] = frozenset(
    {
        "BROKER_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "AUTHENTICATION_FAILED",
        "CREDENTIALS_MISSING",
        "NETWORK_ERROR",
        "TIMEOUT",
        "PERMISSION_DENIED",
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNKNOWN_ERROR",
        # Custom Trading Runtime Gate Codes
        "TRADING_POLICY_UNDEFINED",
        "DEADLINE_EXCEEDED",
        "QUOTE_STALE",
        # Custom Trading Runtime Execution Coordinator Codes
        "OCO_UNSUPPORTED",
        "LIVE_PROTECTIVE_MODIFY_FAILED",
        "LIVE_NON_ATOMIC_MODIFY_ESCALATED",
        "LIVE_MULTI_LEG_ROLLBACK_TRIGGERED",
        # Custom Trading Runtime State Store Codes
        "LIVE_STATE_VERSION_CONFLICT",
        # Custom Trading Runtime Dispatch Codes
        "LIVE_BROKER_REJECTED",
        # Custom Live Runtime Codes
        "LIVE_DISABLED",
        "LIVE_GATE_FAILED",
        "LIVE_APPROVAL_REQUIRED",
        "LIVE_KILL_SWITCH_ACTIVE",
        "LIVE_STALE_CONTEXT",
        "LIVE_RECONCILIATION_REQUIRED",
        "LIVE_UNKNOWN_OUTCOME",
        "LIVE_IDEMPOTENCY_CONFLICT",
        "LIVE_SESSION_INACTIVE",
        "LIVE_BROKER_READINESS_FAILED",
        "LIVE_AUDIT_WRITE_FAILED",
        "LIVE_COST_BUDGET_EXCEEDED",
        "WORKFLOW_TIMEOUT",
        "RETRY_AFTER_RECONCILIATION",
    }
)
"""Deterministic codes expected at the Trading official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "LIVE_DISABLED": "Live trading is disabled. Enable live mode in configuration.",
    "LIVE_GATE_FAILED": "A mandatory live gate failed; the action is blocked.",
    "LIVE_POLICY_UNDEFINED": "No live action policy entry exists for the requested action.",
    "LIVE_APPROVAL_REQUIRED": "Explicit approval context is required for this live action.",
    "LIVE_KILL_SWITCH_ACTIVE": "Active kill switch blocks all live trading requests.",
    "LIVE_STALE_CONTEXT": "Live context is stale and cannot be used for broker mutation.",
    "LIVE_RECONCILIATION_REQUIRED": "Broker reconciliation must complete before live mutation.",  # noqa: E501
    "LIVE_UNKNOWN_OUTCOME": "The broker outcome is unknown; reconciliation required.",
    "LIVE_IDEMPOTENCY_CONFLICT": "A duplicate idempotency key was detected for a different request.",  # noqa: E501
    "LIVE_SESSION_INACTIVE": "No active live session; start a session before trading.",
    "LIVE_BROKER_READINESS_FAILED": "Broker readiness check failed; live mutation is blocked.",  # noqa: E501
    "LIVE_AUDIT_WRITE_FAILED": "Audit pre-event write failed; broker mutation is blocked.",  # noqa: E501
    "LIVE_COST_BUDGET_EXCEEDED": "Live cost budget exceeded; broker mutation is blocked.",  # noqa: E501
    "WORKFLOW_TIMEOUT": "Live workflow exceeded configured timeout limit.",
    "RETRY_AFTER_RECONCILIATION": "Retry is not safe until broker reconciliation resolves the outcome.",  # noqa: E501
    "TRADING_POLICY_UNDEFINED": "No policy matrix entry is defined for this action.",
    "DEADLINE_EXCEEDED": "The gate pipeline exceeded its configured deadline.",
    "QUOTE_STALE": "The mandatory quote snapshot aged beyond its freshness TTL.",
    "OCO_UNSUPPORTED": "Broker adapter lacks native OCO support and synthetic emulation is disabled.",  # noqa: E501
    "LIVE_PROTECTIVE_MODIFY_FAILED": "Position opened but the protective SL/TP modify failed; critical incident.",  # noqa: E501
    "LIVE_NON_ATOMIC_MODIFY_ESCALATED": "Non-atomic modify replace step failed after cancellation; critical incident.",  # noqa: E501
    "LIVE_MULTI_LEG_ROLLBACK_TRIGGERED": "A multi-leg execution leg failed or breached fill tolerance; rollback triggered.",  # noqa: E501
    "LIVE_STATE_VERSION_CONFLICT": "The state projection was modified concurrently; the expected version is stale.",  # noqa: E501
    "LIVE_BROKER_REJECTED": "The broker rejected the trade request.",
}


def to_trading_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Trading error payload.

    Use this at the trading tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Trading functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "BROKER_UNAVAILABLE"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Trading service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}


# --- Trading exceptions ---


class TradingTimeoutError(TradingError):
    """Raised when broker execution exceeds the configured timeout."""

    code = "TIMEOUT"


class UnknownOutcomeError(TradingError):
    """Raised when broker execution outcome cannot be determined safely."""

    code = "CIRCUIT_OPEN"


TRADING_RETCODE_ERROR_MAP: dict[int, str] = {
    10004: "TIMEOUT",  # TRADE_RETCODE_REQUOTE
    10006: "BROKER_UNAVAILABLE",  # TRADE_RETCODE_REJECT
    10014: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_VOLUME
    10015: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_PRICE
    10016: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_STOPS
    10017: "CIRCUIT_OPEN",  # TRADE_RETCODE_TRADE_DISABLED / freeze-like block
    10019: "VALIDATION_FAILED",  # TRADE_RETCODE_NO_MONEY
    10031: "DATA_NOT_FOUND",  # order not found in simulator compatibility layer
    10032: "DATA_NOT_FOUND",  # position not found in simulator compatibility layer
}

TRANSIENT_TRADING_RETCODES = frozenset({10004, 10005, 10006, 10012, 10020, 10021})


def classify_broker_error(raw_error: Exception | object) -> dict[str, object]:
    """Classify broker errors into deterministic internal error metadata.

    Args:
        raw_error: Exception or broker response object with an optional
            ``retcode`` attribute.

    Returns:
        A mapping containing ``code``, ``classification``, ``retcode``, and
        redacted ``details``.
    """
    from app.utils.security import redact_text

    retcode = getattr(raw_error, "retcode", None)
    if isinstance(raw_error, Mapping):
        retcode = raw_error.get("retcode", retcode)
    try:
        normalized_retcode = int(retcode) if retcode is not None else None
    except (TypeError, ValueError):
        normalized_retcode = None

    code = "UNKNOWN_ERROR"
    if normalized_retcode is not None:
        if normalized_retcode in TRADING_RETCODE_ERROR_MAP:
            code = TRADING_RETCODE_ERROR_MAP[normalized_retcode]
    else:
        raw_code = getattr(raw_error, "code", None)
        code = (
            raw_code
            if isinstance(raw_code, str) and raw_code.strip()
            else "UNKNOWN_ERROR"
        )

    classification = (
        "transient"
        if normalized_retcode in TRANSIENT_TRADING_RETCODES
        or code in {"TIMEOUT", "NETWORK_ERROR", "BROKER_UNAVAILABLE"}
        else "permanent"
    )
    return {
        "code": code.upper().strip(),
        "classification": classification,
        "retcode": normalized_retcode,
        "details": redact_text(str(raw_error)),
    }


def trading_retry_delay(
    attempt: int,
    *,
    base_seconds: float = 0.25,
    max_seconds: float = 5.0,
    jitter_ratio: float = 0.2,
) -> float:
    """Compute exponential backoff with randomized jitter for idempotent retries.

    Args:
        attempt: Zero-based retry attempt number.
        base_seconds: Initial delay before exponential growth.
        max_seconds: Maximum returned delay.
        jitter_ratio: Fractional jitter applied to the capped delay.

    Returns:
        Delay in seconds.

    Raises:
        ValidationError: If retry parameters are invalid.
    """
    if attempt < 0:
        raise TradingValidationError("attempt must be non-negative.")
    if base_seconds <= 0.0 or max_seconds <= 0.0:
        raise TradingValidationError("retry delays must be positive.")
    if jitter_ratio < 0.0:
        raise TradingValidationError("jitter_ratio must be non-negative.")

    delay_val = base_seconds * (2**attempt)
    delay = float(max_seconds) if delay_val > max_seconds else float(delay_val)
    jitter = float(delay * jitter_ratio * random())
    total_delay = delay + jitter
    return float(max_seconds) if total_delay > max_seconds else float(total_delay)
