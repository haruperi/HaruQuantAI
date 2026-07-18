"""Deterministic error-code mapping for the strategy service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.exceptions`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Strategy, and provides a single redacted mapping
helper for official Strategy tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


STRATEGY_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "UNKNOWN_ERROR",
        # Custom Strategy Codes
        "STRATEGY_INVALID_CONFIG",
        "STRATEGY_NOT_FOUND",
        "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE",
        "STRATEGY_DEPRECATED",
        "STRATEGY_UNAPPROVED_MODULE",
        "STRATEGY_SCHEMA_VALIDATION_FAILED",
        "STRATEGY_UNSUPPORTED_TIMING_POLICY",
        "STRATEGY_LOOKAHEAD_DETECTED",
        "SIM_ARBITRARY_CODE_REJECTED",
        "STRATEGY_INTERNAL_ERROR",
        "STRATEGY_LIFECYCLE_NOT_APPROVED",
        "STRATEGY_ENVIRONMENT_NOT_PERMITTED",
        "STRATEGY_ARTIFACT_HASH_MISMATCH",
        "STRATEGY_DEPENDENCY_HASH_MISMATCH",
        "INDICATOR_MODULE_ERROR",
        "STRATEGY_CHECKPOINT_INVALID",
        "STRATEGY_CHECKPOINT_INCOMPATIBLE",
        "STRATEGY_DATA_NOT_READY",
        "STRATEGY_INDICATOR_NOT_READY",
        "STRATEGY_MISSING_REQUIRED_DATA",
        "STRATEGY_STALE_DATA",
        "STRATEGY_DUPLICATE_INTENT",
        "STRATEGY_RESOURCE_LIMIT_EXCEEDED",
        "STRATEGY_TIMEOUT",
        "STRATEGY_VALIDATION_ARTIFACT_REQUIRED",
        "STRATEGY_RISK_PROFILE_REQUIRED",
        "STRATEGY_CIRCUIT_BREAKER_TRIGGERED",
        "STRATEGY_POSITION_LIMIT_EXCEEDED",
        "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED",
        "STRATEGY_DATA_QUALITY_GATE_FAILED",
        "STRATEGY_PERFORMANCE_DEGRADED",
        "STRATEGY_DRIFT_DETECTED",
        "STRATEGY_REGULATORY_LIMIT_BREACHED",
        "STRATEGY_MARKET_ACCESS_REVOKED",
        "STRATEGY_HARD_KILLED",
    }
)
"""Deterministic codes expected at the Strategy official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "STRATEGY_INVALID_CONFIG": "Strategy configuration failed schema validation.",
    "STRATEGY_NOT_FOUND": "Unrecognized strategy ID requested.",
    "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE": "No matching version fits the constraint.",
    "STRATEGY_DEPRECATED": "Strategy is deprecated and cannot be run.",
    "STRATEGY_UNAPPROVED_MODULE": "Module resolution pointed to an unapproved file path.",
    "STRATEGY_SCHEMA_VALIDATION_FAILED": "Config JSON schema failed validation.",
    "STRATEGY_UNSUPPORTED_TIMING_POLICY": "Timing policy is unsupported.",
    "STRATEGY_LOOKAHEAD_DETECTED": "Lookahead risk or future data access detected.",
    "SIM_ARBITRARY_CODE_REJECTED": "Arbitrary user Python code execution rejected.",
    "STRATEGY_INTERNAL_ERROR": "Internal strategy computations failed.",
    "STRATEGY_LIFECYCLE_NOT_APPROVED": "Strategy environment exceeds lifecycle approval state.",
    "STRATEGY_ENVIRONMENT_NOT_PERMITTED": "Target environment not declared in registry.",
    "STRATEGY_ARTIFACT_HASH_MISMATCH": "Package artifact hash does not match registry.",
    "STRATEGY_DEPENDENCY_HASH_MISMATCH": "Lockfile hash mismatch detected.",
    "INDICATOR_MODULE_ERROR": "Underlying indicator module call failed.",
    "STRATEGY_CHECKPOINT_INVALID": "Checkpoint data shape is invalid.",
    "STRATEGY_CHECKPOINT_INCOMPATIBLE": "Restored checkpoint settings mismatch.",
    "STRATEGY_DATA_NOT_READY": "Input data is missing or not ready.",
    "STRATEGY_INDICATOR_NOT_READY": "Required indicators are warmup incomplete.",
    "STRATEGY_MISSING_REQUIRED_DATA": "Data query yielded missing fields.",
    "STRATEGY_STALE_DATA": "Data arrival exceeded latency threshold.",
    "STRATEGY_DUPLICATE_INTENT": "Idempotency or sequence keys collided.",
    "STRATEGY_RESOURCE_LIMIT_EXCEEDED": "CPU time or memory allocations exceeded limit.",
    "STRATEGY_TIMEOUT": "Strategy hook timing exceeded budget limit.",
    "STRATEGY_VALIDATION_ARTIFACT_REQUIRED": "Promotion failed due to missing evidence.",
    "STRATEGY_RISK_PROFILE_REQUIRED": "Strategy registry has no declared risk profile.",
    "STRATEGY_CIRCUIT_BREAKER_TRIGGERED": "Circuit breaker stopped intent generation.",
    "STRATEGY_POSITION_LIMIT_EXCEEDED": "Intent exceeded local position sizing caps.",
    "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED": "Volume size exceeded visible participation limit.",
    "STRATEGY_DATA_QUALITY_GATE_FAILED": "Timezone normalization or gaps rejected tick inputs.",
    "STRATEGY_PERFORMANCE_DEGRADED": "Analytics flagged degraded returns.",
    "STRATEGY_DRIFT_DETECTED": "Model inputs drifted statistical limits.",
    "STRATEGY_REGULATORY_LIMIT_BREACHED": "Local validation hit regulatory caps.",
    "STRATEGY_MARKET_ACCESS_REVOKED": "Broker reported login or venue suspension.",
    "STRATEGY_HARD_KILLED": "Emergency hard kill signal received.",
}


def to_strategy_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Strategy error payload.

    Use this at the strategy tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Strategy functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "STRATEGY_INTERNAL_ERROR"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Strategy service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}


# --- Strategies Domain Exceptions ---


class StrategyError(Exception):
    """Base error type for all strategy calculations and registry operations.

    Ensures that custom STRATEGY_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class StrategyConfigError(StrategyError):
    """Raised when strategy configuration fails schema validation."""

    code = "STRATEGY_INVALID_CONFIG"


class StrategyNotFoundError(StrategyError):
    """Raised when an unrecognized strategy ID is requested."""

    code = "STRATEGY_NOT_FOUND"


class StrategyVersionConstraintUnsatisfiableError(StrategyError):
    """Raised when no matching version fits the constraint."""

    code = "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE"


class StrategyDeprecatedError(StrategyError):
    """Raised when strategy is deprecated and cannot be run."""

    code = "STRATEGY_DEPRECATED"


class StrategyUnapprovedModuleError(StrategyError):
    """Raised when module resolution points to an unapproved file path."""

    code = "STRATEGY_UNAPPROVED_MODULE"


class StrategySchemaValidationFailedError(StrategyError):
    """Raised when config JSON schema fails validation."""

    code = "STRATEGY_SCHEMA_VALIDATION_FAILED"


class StrategyUnsupportedTimingPolicyError(StrategyError):
    """Raised when timing policy is unsupported."""

    code = "STRATEGY_UNSUPPORTED_TIMING_POLICY"


class StrategyLookaheadDetectedError(StrategyError):
    """Raised when lookahead risk or future data access is detected."""

    code = "STRATEGY_LOOKAHEAD_DETECTED"


class SimArbitraryCodeRejectedError(StrategyError):
    """Raised when arbitrary user Python code execution is rejected."""

    code = "SIM_ARBITRARY_CODE_REJECTED"


class StrategyInternalError(StrategyError):
    """Raised when internal strategy computations fail."""

    code = "STRATEGY_INTERNAL_ERROR"


class StrategyLifecycleNotApprovedError(StrategyError):
    """Raised when strategy environment exceeds lifecycle approval state."""

    code = "STRATEGY_LIFECYCLE_NOT_APPROVED"


class StrategyEnvironmentNotPermittedError(StrategyError):
    """Raised when the target environment is not declared in registry."""

    code = "STRATEGY_ENVIRONMENT_NOT_PERMITTED"


class StrategyArtifactHashMismatchError(StrategyError):
    """Raised when package artifact hash does not match registry entry."""

    code = "STRATEGY_ARTIFACT_HASH_MISMATCH"


class StrategyDependencyHashMismatchError(StrategyError):
    """Raised when lockfile hash mismatch is detected."""

    code = "STRATEGY_DEPENDENCY_HASH_MISMATCH"


class IndicatorModuleError(StrategyError):
    """Raised when an underlying indicator module call fails."""

    code = "INDICATOR_MODULE_ERROR"


class StrategyCheckpointInvalidError(StrategyError):
    """Raised when checkpoint data shape is invalid."""

    code = "STRATEGY_CHECKPOINT_INVALID"


class StrategyCheckpointIncompatibleError(StrategyError):
    """Raised when restored checkpoint has mismatching settings or version."""

    code = "STRATEGY_CHECKPOINT_INCOMPATIBLE"


class StrategyDataNotReadyError(StrategyError):
    """Raised when input data is missing or not ready."""

    code = "STRATEGY_DATA_NOT_READY"


class StrategyIndicatorNotReadyError(StrategyError):
    """Raised when required indicators are warm-up incomplete."""

    code = "STRATEGY_INDICATOR_NOT_READY"


class StrategyMissingRequiredDataError(StrategyError):
    """Raised when data query yields missing fields."""

    code = "STRATEGY_MISSING_REQUIRED_DATA"


class StrategyStaleDataError(StrategyError):
    """Raised when data arrival exceeds latency threshold."""

    code = "STRATEGY_STALE_DATA"


class StrategyDuplicateIntentError(StrategyError):
    """Raised when idempotency or sequence keys collide."""

    code = "STRATEGY_DUPLICATE_INTENT"


class StrategyResourceLimitExceededError(StrategyError):
    """Raised when CPU time or memory allocations exceed limit."""

    code = "STRATEGY_RESOURCE_LIMIT_EXCEEDED"


class StrategyTimeoutError(StrategyError):
    """Raised when strategy hook timing exceeds budget limit."""

    code = "STRATEGY_TIMEOUT"


class StrategyValidationArtifactRequiredError(StrategyError):
    """Raised when promotion fails due to missing evidence artifact."""

    code = "STRATEGY_VALIDATION_ARTIFACT_REQUIRED"


class StrategyRiskProfileRequiredError(StrategyError):
    """Raised when strategy registry has no declared risk profile."""

    code = "STRATEGY_RISK_PROFILE_REQUIRED"


class StrategyCircuitBreakerTriggeredError(StrategyError):
    """Raised when circuit breaker stops intent generation."""

    code = "STRATEGY_CIRCUIT_BREAKER_TRIGGERED"


class StrategyPositionLimitExceededError(StrategyError):
    """Raised when intent exceeds local position sizing caps."""

    code = "STRATEGY_POSITION_LIMIT_EXCEEDED"


class StrategyVolumeParticipationExceededError(StrategyError):
    """Raised when volume size exceeds visible participation limit."""

    code = "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED"


class StrategyDataQualityGateFailedError(StrategyError):
    """Raised when timezone normalization or gaps reject tick inputs."""

    code = "STRATEGY_DATA_QUALITY_GATE_FAILED"


class StrategyPerformanceDegradedError(StrategyError):
    """Raised when analytics flag degraded returns."""

    code = "STRATEGY_PERFORMANCE_DEGRADED"


class StrategyDriftDetectedError(StrategyError):
    """Raised when model inputs drift statistical limits."""

    code = "STRATEGY_DRIFT_DETECTED"


class StrategyRegulatoryLimitBreachedError(StrategyError):
    """Raised when local validation hits regulatory caps."""

    code = "STRATEGY_REGULATORY_LIMIT_BREACHED"


class StrategyMarketAccessRevokedError(StrategyError):
    """Raised when broker reports login or venue suspension."""

    code = "STRATEGY_MARKET_ACCESS_REVOKED"


class StrategyHardKilledError(StrategyError):
    """Raised when external orchestration sends emergency hard kill signal."""

    code = "STRATEGY_HARD_KILLED"


def map_exception_to_strategy_error(exc: Exception) -> StrategyError:
    """Map any lower-level exception to a StrategyError code at boundaries.

    Ensures lookahead, indicator, and data errors map deterministically.
    """
    if isinstance(exc, StrategyError):
        return exc

    exc_name = exc.__class__.__name__
    msg = str(exc)

    # Check for lookahead
    if (
        exc_name == "LookaheadRiskError"
        or "LookaheadRisk" in exc_name
        or getattr(exc, "code", "") == "IND_LOOKAHEAD_RISK"
    ):
        return StrategyLookaheadDetectedError(msg)

    # Check for indicator failures
    if (
        exc_name.startswith("Indicator")
        or "Indicator" in exc_name
        or getattr(exc, "code", "").startswith("IND_")
    ):
        return IndicatorModuleError(f"Underlying indicator execution failed: {msg}")

    # Check for data service issues
    if "Data" in exc_name or getattr(exc, "code", "").startswith("DATA_"):
        return StrategyDataNotReadyError(f"Underlying data service failed: {msg}")

    # Fallback to internal error
    return StrategyInternalError(f"Internal calculation failed: {msg}")
