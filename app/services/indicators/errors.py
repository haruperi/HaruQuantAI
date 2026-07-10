"""Deterministic error-code mapping for the indicators service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.exceptions`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Indicators, and provides a single redacted mapping
helper for official Indicators tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


INDICATORS_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "UNKNOWN_ERROR",
        # Custom Indicator Codes
        "IND_INVALID_CONFIG",
        "IND_INVALID_PARAMETER",
        "IND_UNSUPPORTED_INDICATOR",
        "IND_UNSUPPORTED_TIMEFRAME",
        "IND_UNSUPPORTED_DTYPE",
        "IND_INVALID_INPUT_SCHEMA",
        "IND_MISSING_REQUIRED_COLUMN",
        "IND_INVALID_OUTPUT_COLUMN",
        "IND_OUTPUT_COLUMN_CONFLICT",
        "IND_INVALID_OUTPUT_MODE",
        "IND_INPUT_MUTATION_DETECTED",
        "IND_DUPLICATE_TIMESTAMP",
        "IND_NON_MONOTONIC_TIME",
        "IND_AMBIGUOUS_TIMESTAMP",
        "IND_INVALID_TIMEZONE",
        "IND_INVALID_OHLC",
        "IND_INSUFFICIENT_DATA",
        "IND_LOOKAHEAD_RISK",
        "IND_UNKNOWN_ADJUSTMENT_STATUS",
        "IND_STATE_INCOMPATIBLE",
        "IND_STATE_CORRUPTED",
        "IND_RESOURCE_LIMIT_EXCEEDED",
        "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED",
        "IND_SYMBOL_MAPPING_REQUIRED",
        "IND_STUB_QUOTE_REJECTED",
        "IND_INVERTED_MARKET",
        "IND_SPREAD_THRESHOLD_EXCEEDED",
        "IND_FORMULA_VERSION_MISMATCH",
        "IND_DEPRECATED",
        "IND_UNSUPPORTED_OUT_OF_CORE",
        "IND_ACCELERATION_BACKEND_UNAVAILABLE",
        "IND_TIMEOUT",
        "IND_CANCELLED",
        "IND_PARTIAL_RESULT",
        "IND_UNSUPPORTED_INCREMENTAL_MODE",
        "IND_CUSTOM_INDICATOR_REJECTED",
        "IND_ACCESS_DENIED",
        "IND_PROPRIETARY_UNAUTHORIZED",
        "IND_SLO_VIOLATION",
    }
)
"""Deterministic codes expected at the Indicators official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "IND_INVALID_CONFIG": "Indicator configuration combination checks failed.",
    "IND_INVALID_PARAMETER": "Formula parameter checks failed.",
    "IND_UNSUPPORTED_INDICATOR": "An unrecognized indicator ID is requested.",
    "IND_UNSUPPORTED_TIMEFRAME": "Timeframe is invalid or missing.",
    "IND_UNSUPPORTED_DTYPE": "Inputs contain unsupported float or integer precision.",
    "IND_INVALID_INPUT_SCHEMA": "DataFrame structure or column types failed validation.",
    "IND_MISSING_REQUIRED_COLUMN": "Required columns are missing.",
    "IND_INVALID_OUTPUT_COLUMN": "Output column naming is malformed or invalid.",
    "IND_OUTPUT_COLUMN_CONFLICT": "Output column names conflict with input columns.",
    "IND_INVALID_OUTPUT_MODE": "Output modes are mutually exclusive or invalid.",
    "IND_INPUT_MUTATION_DETECTED": "Indicator calculations modified input data in place.",
    "IND_DUPLICATE_TIMESTAMP": "Duplicate timestamps found in symbol dataset.",
    "IND_NON_MONOTONIC_TIME": "Timestamps are not strictly ascending.",
    "IND_AMBIGUOUS_TIMESTAMP": "Naive local time transitions made timestamps ambiguous.",
    "IND_INVALID_TIMEZONE": "Naive local timezone calculations rejected.",
    "IND_INVALID_OHLC": "Prices violate physical boundaries.",
    "IND_INSUFFICIENT_DATA": "Input row count is lower than indicator warmup requirements.",
    "IND_LOOKAHEAD_RISK": "Strategy attempted to consume data before it closed.",
    "IND_UNKNOWN_ADJUSTMENT_STATUS": "Adjustment status of input prices is unknown.",
    "IND_STATE_INCOMPATIBLE": "State serialization does not match current specifications.",
    "IND_STATE_CORRUPTED": "State payload cannot be parsed.",
    "IND_RESOURCE_LIMIT_EXCEEDED": "Calculations exceeded memory budget or time limit.",
    "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED": "Intra-bar adjustments are unsupported.",
    "IND_SYMBOL_MAPPING_REQUIRED": "Symbol mapping contract is required but missing.",
    "IND_STUB_QUOTE_REJECTED": "Bid/ask values represent stub quotes and are rejected.",
    "IND_INVERTED_MARKET": "Ask is less than bid.",
    "IND_SPREAD_THRESHOLD_EXCEEDED": "Bid/ask spread exceeds threshold.",
    "IND_FORMULA_VERSION_MISMATCH": "Calculation used incompatible formula versions.",
    "IND_DEPRECATED": "Deprecated indicator requested under strict deprecation phase.",
    "IND_UNSUPPORTED_OUT_OF_CORE": "Out-of-core calculations are unsupported.",
    "IND_ACCELERATION_BACKEND_UNAVAILABLE": "Acceleration backend is unavailable.",
    "IND_TIMEOUT": "Indicator calculation timed out.",
    "IND_CANCELLED": "Indicator calculation was cancelled.",
    "IND_PARTIAL_RESULT": "Partial result returned in strict modes.",
    "IND_UNSUPPORTED_INCREMENTAL_MODE": "Incremental calculation mode not supported.",
    "IND_CUSTOM_INDICATOR_REJECTED": "Conformance or side-effect checks rejected indicator.",
    "IND_ACCESS_DENIED": "Actor lacks basic access to indicator services.",
    "IND_PROPRIETARY_UNAUTHORIZED": "Access control blocked proprietary indicator.",
    "IND_SLO_VIOLATION": "SLO monitoring policy triggered synchronous rejection.",
}


def to_indicators_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Indicators error payload.

    Use this at the indicators tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Indicators functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "VALIDATION_FAILED"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Indicators service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}


# --- Indicators Domain Exceptions ---


class IndicatorError(Exception):
    """Base error type for all indicator calculations and registry operations.

    Ensures that custom IND_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class IndicatorConfigError(IndicatorError):
    """Raised when configuration combination checks fail."""

    code = "IND_INVALID_CONFIG"


class IndicatorParameterError(IndicatorError):
    """Raised when formula parameter checks fail (e.g. period <= 0)."""

    code = "IND_INVALID_PARAMETER"


class UnsupportedIndicatorError(IndicatorError):
    """Raised when an unrecognized indicator ID is requested."""

    code = "IND_UNSUPPORTED_INDICATOR"


class UnsupportedTimeframeError(IndicatorError):
    """Raised when timeframe is invalid or missing."""

    code = "IND_UNSUPPORTED_TIMEFRAME"


class UnsupportedDtypeError(IndicatorError):
    """Raised when inputs contain unsupported float or integer precision."""

    code = "IND_UNSUPPORTED_DTYPE"


class InvalidInputSchemaError(IndicatorError):
    """Raised when DataFrame structure or column types fail validation."""

    code = "IND_INVALID_INPUT_SCHEMA"


class MissingRequiredColumnError(IndicatorError):
    """Raised when required columns (e.g. 'close') are missing."""

    code = "IND_MISSING_REQUIRED_COLUMN"


class InvalidOutputColumnError(IndicatorError):
    """Raised when output column naming is malformed or invalid."""

    code = "IND_INVALID_OUTPUT_COLUMN"


class OutputColumnConflictError(IndicatorError):
    """Raised when output column names conflict with input columns."""

    code = "IND_OUTPUT_COLUMN_CONFLICT"


class InvalidOutputModeError(IndicatorError):
    """Raised when output modes are mutually exclusive or invalid."""

    code = "IND_INVALID_OUTPUT_MODE"


class InputMutationError(IndicatorError):
    """Raised when indicator calculations modify input data in place."""

    code = "IND_INPUT_MUTATION_DETECTED"


class DuplicateTimestampError(IndicatorError):
    """Raised when duplicate timestamps are found in a single symbol dataset."""

    code = "IND_DUPLICATE_TIMESTAMP"


class NonMonotonicTimeError(IndicatorError):
    """Raised when timestamps are not strictly ascending."""

    code = "IND_NON_MONOTONIC_TIME"


class AmbiguousTimestampError(IndicatorError):
    """Raised when naive local time transitions make timestamps ambiguous."""

    code = "IND_AMBIGUOUS_TIMESTAMP"


class InvalidTimezoneError(IndicatorError):
    """Raised when naive local timezone calculations are rejected."""

    code = "IND_INVALID_TIMEZONE"


class InvalidOHLCError(IndicatorError):
    """Raised when prices violate physical boundaries (e.g. low > high)."""

    code = "IND_INVALID_OHLC"


class InsufficientDataError(IndicatorError):
    """Raised when input row count is lower than indicator warmup requirements."""

    code = "IND_INSUFFICIENT_DATA"


class LookaheadRiskError(IndicatorError):
    """Raised when strategy attempts to consume data before it is closed/available."""

    code = "IND_LOOKAHEAD_RISK"


class UnknownAdjustmentStatusError(IndicatorError):
    """Raised when adjustment status of input prices is unknown."""

    code = "IND_UNKNOWN_ADJUSTMENT_STATUS"


class StateIncompatibleError(IndicatorError):
    """Raised when state serialization does not match current specifications."""

    code = "IND_STATE_INCOMPATIBLE"


class StateCorruptedError(IndicatorError):
    """Raised when state payload cannot be parsed."""

    code = "IND_STATE_CORRUPTED"


class ResourceLimitExceededError(IndicatorError):
    """Raised when calculations exceed memory budget or time limit."""

    code = "IND_RESOURCE_LIMIT_EXCEEDED"


class UnsupportedIntraBarAdjustmentError(IndicatorError):
    """Raised when intra-bar corporate-action adjustments are unsupported."""

    code = "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED"


class SymbolMappingRequiredError(IndicatorError):
    """Raised when symbol mapping contract is required but missing."""

    code = "IND_SYMBOL_MAPPING_REQUIRED"


class StubQuoteRejectedError(IndicatorError):
    """Raised when bid/ask values represent stub quotes and are rejected."""

    code = "IND_STUB_QUOTE_REJECTED"


class InvertedMarketError(IndicatorError):
    """Raised when ask is less than bid."""

    code = "IND_INVERTED_MARKET"


class SpreadThresholdExceededError(IndicatorError):
    """Raised when bid/ask spread exceeds the configured threshold."""

    code = "IND_SPREAD_THRESHOLD_EXCEEDED"


class FormulaVersionMismatchError(IndicatorError):
    """Raised when calculation uses incompatible formula versions."""

    code = "IND_FORMULA_VERSION_MISMATCH"


class DeprecatedIndicatorError(IndicatorError):
    """Raised when a deprecated indicator is requested under strict deprecation phase."""

    code = "IND_DEPRECATED"


class UnsupportedOutOfCoreError(IndicatorError):
    """Raised when indicator requires full context and out-of-core is unsupported."""

    code = "IND_UNSUPPORTED_OUT_OF_CORE"


class AccelerationBackendUnavailableError(IndicatorError):
    """Raised when requested acceleration backend is not available."""

    code = "IND_ACCELERATION_BACKEND_UNAVAILABLE"


class IndicatorTimeoutError(IndicatorError):
    """Raised when calculation times out."""

    code = "IND_TIMEOUT"


class CalculationCancelledError(IndicatorError):
    """Raised when calculation is cancelled before completion."""

    code = "IND_CANCELLED"


class PartialResultError(IndicatorError):
    """Raised when only a partial result is returned in strict modes."""

    code = "IND_PARTIAL_RESULT"


class UnsupportedIncrementalModeError(IndicatorError):
    """Raised when incremental calculation mode is not supported by the indicator."""

    code = "IND_UNSUPPORTED_INCREMENTAL_MODE"


class CustomIndicatorRejectedError(IndicatorError):
    """Raised when conformance or side-effect checks reject custom indicators."""

    code = "IND_CUSTOM_INDICATOR_REJECTED"


class AccessDeniedError(IndicatorError):
    """Raised when actor/workflow lacks basic access to indicator services."""

    code = "IND_ACCESS_DENIED"


class ProprietaryUnauthorizedError(IndicatorError):
    """Raised when access control blocks proprietary/licensed indicators."""

    code = "IND_PROPRIETARY_UNAUTHORIZED"


class SLOViolationError(IndicatorError):
    """Raised when SLO monitoring policy triggers synchronous rejection."""

    code = "IND_SLO_VIOLATION"
