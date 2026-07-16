"""Deterministic Data-domain errors and immutable error metadata."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from app.utils import ValidationError as UtilsValidationError
from app.utils import logger, redact_text_value, validate_id

type JsonScalar = None | bool | int | float | str
type ErrorSeverity = Literal["info", "warning", "error", "critical"]

ERROR_SAFE_DETAILS_MAX_ITEMS = 64
ERROR_SAFE_DETAILS_MAX_BYTES = 8_192
_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
)


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Safe handling metadata for one deterministic Data error code."""

    code: str
    category: str
    retryable: bool
    severity: ErrorSeverity
    safe_message: str
    operator_action: str


def _definition(
    code: str,
    category: str,
    *,
    retryable: bool = False,
    severity: ErrorSeverity = "error",
    safe_message: str,
    operator_action: str,
) -> ErrorDefinition:
    """Build one internal immutable error definition."""
    logger.debug("Running DATA function: _definition")
    return ErrorDefinition(
        code=code,
        category=category,
        retryable=retryable,
        severity=severity,
        safe_message=safe_message,
        operator_action=operator_action,
    )


_ERROR_DEFINITIONS = (
    _definition(
        "INVALID_INPUT",
        "validation",
        safe_message="Input is invalid",
        operator_action="Correct the request",
    ),
    _definition(
        "VALIDATION_FAILED",
        "validation",
        safe_message="Validation failed",
        operator_action="Correct the supplied values",
    ),
    _definition(
        "DATA_QUALITY_FAILED",
        "quality",
        safe_message="Data quality validation failed",
        operator_action="Inspect quality evidence",
    ),
    _definition(
        "DATA_NOT_FOUND",
        "data",
        safe_message="Data was not found",
        operator_action="Verify the requested identity or range",
    ),
    _definition(
        "EMPTY_RESULT",
        "data",
        safe_message="The request returned no records",
        operator_action="Verify the requested range and source",
    ),
    _definition(
        "LIMIT_EXCEEDED",
        "validation",
        safe_message="A configured limit was exceeded",
        operator_action="Reduce the bounded request",
    ),
    _definition(
        "UNSUPPORTED_SOURCE",
        "source",
        safe_message="The source is unsupported",
        operator_action="Select a declared source",
    ),
    _definition(
        "UNSUPPORTED_TIMEFRAME",
        "validation",
        safe_message="The timeframe is unsupported",
        operator_action="Select a declared timeframe",
    ),
    _definition(
        "UNSUPPORTED_OPERATION",
        "validation",
        safe_message="The operation is unsupported",
        operator_action="Use a supported operation",
    ),
    _definition(
        "SOURCE_UNAVAILABLE",
        "source",
        retryable=True,
        safe_message="The source is unavailable",
        operator_action="Inspect source readiness and connectivity",
    ),
    _definition(
        "SERVICE_UNAVAILABLE",
        "service",
        retryable=True,
        safe_message="A required service is unavailable",
        operator_action="Restore the required service",
    ),
    _definition(
        "NETWORK_ERROR",
        "transport",
        retryable=True,
        safe_message="A network operation failed",
        operator_action="Inspect the provider transport",
    ),
    _definition(
        "TIMEOUT",
        "transport",
        retryable=True,
        safe_message="The operation timed out",
        operator_action="Inspect latency and configured timeout",
    ),
    _definition(
        "LICENSE_RESTRICTION",
        "policy",
        safe_message="The requested use is not licensed",
        operator_action="Review source license policy",
    ),
    _definition(
        "CREDENTIALS_MISSING",
        "security",
        safe_message="Required credentials are unavailable",
        operator_action="Configure the required secret reference",
    ),
    _definition(
        "AUTHENTICATION_FAILED",
        "security",
        safe_message="Provider authentication failed",
        operator_action="Verify the configured credentials",
    ),
    _definition(
        "PERMISSION_DENIED",
        "security",
        severity="critical",
        safe_message="Permission was denied",
        operator_action="Verify principal permissions and scope",
    ),
    _definition(
        "POLICY_BLOCKED",
        "policy",
        safe_message="Policy blocked the operation",
        operator_action="Review the governing policy evidence",
    ),
    _definition(
        "STALE_EVIDENCE",
        "validation",
        safe_message="Required evidence is stale",
        operator_action="Acquire fresh evidence",
    ),
    _definition(
        "CIRCUIT_BREAKER_OPEN",
        "transport",
        retryable=True,
        safe_message="The source circuit breaker is open",
        operator_action="Wait for an approved probe window",
    ),
    _definition(
        "PRECISION_MISMATCH",
        "validation",
        safe_message="Precision requirements are incompatible",
        operator_action="Provide compatible precision metadata",
    ),
    _definition(
        "MISSING_ASSET_METADATA",
        "validation",
        safe_message="Required asset metadata is missing",
        operator_action="Acquire complete asset metadata",
    ),
    _definition(
        "DATABASE_ERROR",
        "persistence",
        retryable=True,
        safe_message="A database operation failed",
        operator_action="Inspect database health",
    ),
    _definition(
        "DB_CONNECTION_ERROR",
        "persistence",
        retryable=True,
        safe_message="The database connection failed",
        operator_action="Verify database configuration and availability",
    ),
    _definition(
        "DB_WRITE_FAILED",
        "persistence",
        retryable=True,
        safe_message="A durable write failed",
        operator_action="Inspect storage health before retrying",
    ),
    _definition(
        "CONCURRENT_WRITE_LOCKED",
        "concurrency",
        retryable=True,
        safe_message="Another writer owns the resource",
        operator_action="Wait for the active bounded lease",
    ),
    _definition(
        "FILE_CORRUPTED",
        "storage",
        safe_message="A stored artifact is corrupted",
        operator_action="Quarantine and restore or re-ingest the artifact",
    ),
    _definition(
        "SCHEMA_MIGRATION_FAILED",
        "persistence",
        severity="critical",
        safe_message="Schema migration failed",
        operator_action="Inspect migration ownership, order, and checksum",
    ),
    _definition(
        "JOB_NOT_FOUND",
        "job",
        safe_message="The update job was not found",
        operator_action="Verify the job identifier",
    ),
    _definition(
        "SCHEDULER_ERROR",
        "job",
        retryable=True,
        safe_message="The scheduler operation failed",
        operator_action="Inspect job state and scheduler health",
    ),
    _definition(
        "CHECKPOINT_CORRUPTED",
        "job",
        severity="critical",
        safe_message="The checkpoint is corrupted",
        operator_action="Inspect committed chunk and checkpoint evidence",
    ),
    _definition(
        "STATE_RECOVERY_FAILED",
        "recovery",
        severity="critical",
        safe_message="State recovery could not be proven safe",
        operator_action="Stop processing and inspect persisted state",
    ),
    _definition(
        "BUFFER_OVERFLOW",
        "feed",
        safe_message="The feed buffer overflowed",
        operator_action="Apply the configured overflow response",
    ),
    _definition(
        "DATA_DROPPED",
        "feed",
        severity="warning",
        safe_message="Feed data was dropped",
        operator_action="Inspect the recorded gap before governed use",
    ),
    _definition(
        "FEED_HEARTBEAT_TIMEOUT",
        "feed",
        retryable=True,
        safe_message="The feed heartbeat timed out",
        operator_action="Inspect feed connectivity and breaker state",
    ),
    _definition(
        "UNKNOWN_ERROR",
        "internal",
        severity="critical",
        safe_message="An unexpected Data error occurred",
        operator_action="Inspect redacted diagnostic evidence",
    ),
)

DATA_ERROR_MANIFEST: Mapping[str, ErrorDefinition] = MappingProxyType(
    {definition.code: definition for definition in _ERROR_DEFINITIONS}
)


def _validate_safe_details(
    details: Mapping[str, JsonScalar] | None,
) -> Mapping[str, JsonScalar]:
    """Validate and freeze flat boundary-safe error details."""
    logger.debug("Validating redacted Data error details")
    if details is None:
        return MappingProxyType({})
    if len(details) > ERROR_SAFE_DETAILS_MAX_ITEMS:
        raise ValueError("safe_details exceeds the maximum item count")
    validated: dict[str, JsonScalar] = {}
    for key, value in details.items():
        if not isinstance(key, str) or not key or key != key.strip():
            raise ValueError("safe_details keys must be non-empty trimmed strings")
        normalized = key.casefold().replace("-", "_")
        if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
            validated[key] = "[REDACTED]"
            continue
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("safe_details contains a non-finite number")
        if value is not None and not isinstance(value, bool | int | float | str):
            raise TypeError("safe_details values must be JSON scalars")
        if isinstance(value, str):
            validated[key] = str(redact_text_value(value).value)
        else:
            validated[key] = value
    encoded = json.dumps(
        validated,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(encoded) > ERROR_SAFE_DETAILS_MAX_BYTES:
        raise ValueError("safe_details exceeds the maximum canonical JSON size")
    return MappingProxyType(validated)


class DataError(Exception):
    """Redacted deterministic Data-domain exception."""

    def __init__(
        self,
        code: str,
        *,
        safe_details: Mapping[str, JsonScalar] | None = None,
        request_id: str | None = None,
    ) -> None:
        """Initialize a manifest-backed Data error.

        Args:
            code: Deterministic manifest code. Unknown values map to ``UNKNOWN_ERROR``.
            safe_details: Optional flat JSON-scalar diagnostic evidence.
            request_id: Optional caller-provided trace identifier.

        Raises:
            TypeError: If safe details are not JSON scalar values.
            ValueError: If safe details or the request identifier are unsafe.
        """
        definition = DATA_ERROR_MANIFEST.get(code, DATA_ERROR_MANIFEST["UNKNOWN_ERROR"])
        logger.debug("Initializing manifest-backed Data error")
        if request_id is not None:
            try:
                validate_id(request_id, expected_prefix="req")
            except UtilsValidationError as error:
                raise ValueError(
                    "request_id must be a prefixed UUID4 identifier"
                ) from error
        self.code = definition.code
        self.safe_details = _validate_safe_details(safe_details)
        self.request_id = request_id
        self.retryable = definition.retryable
        self.severity = definition.severity
        self.safe_message = definition.safe_message
        self.operator_action = definition.operator_action
        super().__init__(definition.code)


__all__ = [
    "DATA_ERROR_MANIFEST",
    "ERROR_SAFE_DETAILS_MAX_BYTES",
    "ERROR_SAFE_DETAILS_MAX_ITEMS",
    "DataError",
    "ErrorDefinition",
]
