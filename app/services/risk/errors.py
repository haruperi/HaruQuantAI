"""Deterministic error-code mapping for the risk service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.exceptions`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Risk, and provides a single redacted mapping
helper for official Risk tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


RISK_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "PERMISSION_DENIED",
        "UNKNOWN_ERROR",
        # Custom Risk Codes
        "INVALID_PORTFOLIO_STATE",
        "INVALID_RISK_CONFIG",
        "MISSING_EVIDENCE",
        "STALE_EVIDENCE",
        "LIMIT_FAILED",
        "POLICY_BLOCKED",
        "APPROVAL_REQUIRED",
        "APPROVAL_TOKEN_INVALID",
        "APPROVAL_TOKEN_EXPIRED",
        "APPROVAL_TOKEN_REVOKED",
        "APPROVAL_TOKEN_CONSUMED",
        "CONFIG_VERSION_MISMATCH",
        "CONFIG_COMPATIBILITY_NOT_APPROVED",
        "PARAMETRIC_VAR_GAUSSIAN_WARNING",
        "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED",
        "PAYLOAD_TOO_LARGE",
        "MISSING_STOP_LOSS",
        "INSUFFICIENT_VOLATILITY_EVIDENCE",
        "INSUFFICIENT_K_EVIDENCE",
        "LIVE_STATE_STALE",
        "IN_FLIGHT_TOLERANCE_EXCEEDED",
        "CALCULATION_FAILED",
        "SNAPSHOT_BUILD_FAILED",
        "REPORT_GENERATION_FAILED",
        "STORAGE_ERROR",
    }
)
"""Deterministic codes expected at the Risk official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "INVALID_PORTFOLIO_STATE": "Portfolio state validation failed.",
    "INVALID_RISK_CONFIG": "Risk configuration validation failed.",
    "MISSING_EVIDENCE": "Required evidence is missing.",
    "STALE_EVIDENCE": "Required evidence is stale.",
    "LIMIT_FAILED": "Risk limit check failed.",
    "POLICY_BLOCKED": "Action is blocked by risk policy.",
    "APPROVAL_REQUIRED": "Action requires an approval token.",
    "APPROVAL_TOKEN_INVALID": "Approval token is invalid.",
    "APPROVAL_TOKEN_EXPIRED": "Approval token is expired.",
    "APPROVAL_TOKEN_REVOKED": "Approval token has been revoked.",
    "APPROVAL_TOKEN_CONSUMED": "Approval token has already been consumed.",
    "CONFIG_VERSION_MISMATCH": "Stored config version or hash mismatch.",
    "CONFIG_COMPATIBILITY_NOT_APPROVED": "Config hash compatibility was not approved.",
    "PARAMETRIC_VAR_GAUSSIAN_WARNING": "Parametric VaR calculation used Gaussian assumption.",
    "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED": "Pre-trade request blocked due to potential double spend.",
    "PAYLOAD_TOO_LARGE": "Payload exceeds maximum allowed size or nesting depth.",
    "MISSING_STOP_LOSS": "Required stop loss is missing.",
    "INSUFFICIENT_VOLATILITY_EVIDENCE": "Insufficient ATR or volatility evidence.",
    "INSUFFICIENT_K_EVIDENCE": "Insufficient trade samples for Kelly sizing.",
    "LIVE_STATE_STALE": "Live portfolio state freshness checks failed.",
    "IN_FLIGHT_TOLERANCE_EXCEEDED": "In-flight order reconciliation tolerance exceeded.",
    "CALCULATION_FAILED": "A specific risk calculation failed.",
    "SNAPSHOT_BUILD_FAILED": "Building portfolio risk snapshot failed.",
    "REPORT_GENERATION_FAILED": "Risk report generation failed.",
    "STORAGE_ERROR": "Risk audit storage or token state persistence failed.",
}


def to_risk_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Risk error payload.

    Use this at the risk tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Risk functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code if isinstance(raw_code, str) and raw_code.strip() else "LIMIT_FAILED"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Risk service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}


class RiskError(Exception):
    """Base error type for all risk calculations and registry operations.

    Ensures that custom risk error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class RiskValidationError(RiskError):
    """Raised when validation of config or state inputs fails."""

    code = "VALIDATION_FAILED"


class RiskDataError(RiskError):
    """Raised when data storage or retrieval operations fail."""

    code = "DATA_NOT_FOUND"


class InvalidPortfolioStateError(RiskError):
    """Raised when portfolio state has invalid structure or parameters."""

    code = "INVALID_PORTFOLIO_STATE"


class InvalidRiskConfigError(RiskError):
    """Raised when risk configuration is missing or invalid."""

    code = "INVALID_RISK_CONFIG"


class MissingEvidenceError(RiskError):
    """Raised when required evidence is missing."""

    code = "MISSING_EVIDENCE"


class StaleEvidenceError(RiskError):
    """Raised when required evidence is stale."""

    code = "STALE_EVIDENCE"


class LimitFailedError(RiskError):
    """Raised when risk limit check fails."""

    code = "LIMIT_FAILED"


class PolicyBlockedError(RiskError):
    """Raised when trade/allocation is blocked by deterministic policy."""

    code = "POLICY_BLOCKED"


class ApprovalRequiredError(RiskError):
    """Raised when action requires approval token."""

    code = "APPROVAL_REQUIRED"


class ApprovalTokenInvalidError(RiskError):
    """Raised when approval token is invalid."""

    code = "APPROVAL_TOKEN_INVALID"


class ApprovalTokenExpiredError(RiskError):
    """Raised when approval token has expired."""

    code = "APPROVAL_TOKEN_EXPIRED"


class ApprovalTokenRevokedError(RiskError):
    """Raised when approval token was revoked."""

    code = "APPROVAL_TOKEN_REVOKED"


class ApprovalTokenConsumedError(RiskError):
    """Raised when approval token was already consumed."""

    code = "APPROVAL_TOKEN_CONSUMED"


class ConfigVersionMismatchError(RiskError):
    """Raised when config version or hash mismatch occurs."""

    code = "CONFIG_VERSION_MISMATCH"


class ConfigCompatibilityNotApprovedError(RiskError):
    """Raised when config compatibility is not approved."""

    code = "CONFIG_COMPATIBILITY_NOT_APPROVED"


class ParametricVarGaussianWarningError(RiskError):
    """Warning/error when Gaussian assumptions are used for parametric VaR."""

    code = "PARAMETRIC_VAR_GAUSSIAN_WARNING"


class PendingApprovalDoubleSpendBlockedError(RiskError):
    """Raised when concurrent proposals risk double spending."""

    code = "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"


class PayloadTooLargeError(RiskError):
    """Raised when request payload is too large or nested too deeply."""

    code = "PAYLOAD_TOO_LARGE"


class MissingStopLossError(RiskError):
    """Raised when stop loss is missing for stop-dependent sizing."""

    code = "MISSING_STOP_LOSS"


class InsufficientVolatilityEvidenceError(RiskError):
    """Raised when volatility evidence is insufficient for calculation."""

    code = "INSUFFICIENT_VOLATILITY_EVIDENCE"


class InsufficientKEvidenceError(RiskError):
    """Raised when Kelly trade sample evidence is insufficient (< 30)."""

    code = "INSUFFICIENT_K_EVIDENCE"


class LiveStateStaleError(RiskError):
    """Raised when live state is stale."""

    code = "LIVE_STATE_STALE"


class InFlightToleranceExceededError(RiskError):
    """Raised when in-flight order tolerance buffer is exceeded."""

    code = "IN_FLIGHT_TOLERANCE_EXCEEDED"


class CalculationFailedError(RiskError):
    """Raised when a specific risk calculation fails."""

    code = "CALCULATION_FAILED"


class SnapshotBuildFailedError(RiskError):
    """Raised when snapshot building fails."""

    code = "SNAPSHOT_BUILD_FAILED"


class ReportGenerationFailedError(RiskError):
    """Raised when report generation fails."""

    code = "REPORT_GENERATION_FAILED"


class StorageError(RiskError):
    """Raised when risk storage or audit persistence operations fail."""

    code = "STORAGE_ERROR"
