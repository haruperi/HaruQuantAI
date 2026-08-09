"""Accepted deterministic Strategy error catalogue."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Protocol, cast

from app.utils import validate_error_catalog

type ErrorSeverity = Literal["info", "warning", "error", "critical"]


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: ErrorSeverity
    retryable: bool
    operator_action: str


class StrategyErrorCode(StrEnum):
    """Failure codes reachable from approved Strategy capabilities."""

    INVALID_CONFIG = "STRATEGY_INVALID_CONFIG"
    NOT_FOUND = "STRATEGY_NOT_FOUND"
    VERSION_CONSTRAINT_UNSATISFIABLE = "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE"
    DEPRECATED = "STRATEGY_DEPRECATED"
    UNAPPROVED_MODULE = "STRATEGY_UNAPPROVED_MODULE"
    SCHEMA_VALIDATION_FAILED = "STRATEGY_SCHEMA_VALIDATION_FAILED"
    UNSUPPORTED_TIMING_POLICY = "STRATEGY_UNSUPPORTED_TIMING_POLICY"
    LOOKAHEAD_DETECTED = "STRATEGY_LOOKAHEAD_DETECTED"
    ARBITRARY_CODE_REJECTED = "STRATEGY_ARBITRARY_CODE_REJECTED"
    INTERNAL_ERROR = "STRATEGY_INTERNAL_ERROR"
    LIFECYCLE_NOT_APPROVED = "STRATEGY_LIFECYCLE_NOT_APPROVED"
    ENVIRONMENT_NOT_PERMITTED = "STRATEGY_ENVIRONMENT_NOT_PERMITTED"
    ARTIFACT_HASH_MISMATCH = "STRATEGY_ARTIFACT_HASH_MISMATCH"
    DEPENDENCY_HASH_MISMATCH = "STRATEGY_DEPENDENCY_HASH_MISMATCH"
    INDICATOR_MODULE_ERROR = "INDICATOR_MODULE_ERROR"
    CHECKPOINT_INVALID = "STRATEGY_CHECKPOINT_INVALID"
    CHECKPOINT_INCOMPATIBLE = "STRATEGY_CHECKPOINT_INCOMPATIBLE"
    DATA_NOT_READY = "STRATEGY_DATA_NOT_READY"
    INDICATOR_NOT_READY = "STRATEGY_INDICATOR_NOT_READY"
    MISSING_REQUIRED_DATA = "STRATEGY_MISSING_REQUIRED_DATA"
    STALE_DATA = "STRATEGY_STALE_DATA"
    DUPLICATE_INTENT = "STRATEGY_DUPLICATE_INTENT"
    RESOURCE_LIMIT_EXCEEDED = "STRATEGY_RESOURCE_LIMIT_EXCEEDED"
    TIMEOUT = "STRATEGY_TIMEOUT"
    VALIDATION_ARTIFACT_REQUIRED = "STRATEGY_VALIDATION_ARTIFACT_REQUIRED"
    RISK_PROFILE_REQUIRED = "STRATEGY_RISK_PROFILE_REQUIRED"
    POSITION_LIMIT_EXCEEDED = "STRATEGY_POSITION_LIMIT_EXCEEDED"
    DATA_QUALITY_GATE_FAILED = "STRATEGY_DATA_QUALITY_GATE_FAILED"
    HARD_KILLED = "STRATEGY_HARD_KILLED"


_APPROVED_CODES = (
    "STRATEGY_INVALID_CONFIG",
    "STRATEGY_NOT_FOUND",
    "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE",
    "STRATEGY_DEPRECATED",
    "STRATEGY_UNAPPROVED_MODULE",
    "STRATEGY_SCHEMA_VALIDATION_FAILED",
    "STRATEGY_UNSUPPORTED_TIMING_POLICY",
    "STRATEGY_LOOKAHEAD_DETECTED",
    "STRATEGY_ARBITRARY_CODE_REJECTED",
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
    "STRATEGY_POSITION_LIMIT_EXCEEDED",
    "STRATEGY_DATA_QUALITY_GATE_FAILED",
    "STRATEGY_HARD_KILLED",
)


def _definition(code: str) -> ErrorDefinition:
    """Build one safe immutable definition for an approved Strategy code.

    Returns:
        The validated Utils error definition.
    """
    category = (
        "INTEGRITY"
        if code == "STRATEGY_INTERNAL_ERROR"
        else "DATA_STALE"
        if code
        in {
            "STRATEGY_DATA_NOT_READY",
            "STRATEGY_INDICATOR_NOT_READY",
            "STRATEGY_STALE_DATA",
        }
        else "TRANSIENT"
        if code == "STRATEGY_TIMEOUT"
        else "POLICY"
        if code
        in {
            "STRATEGY_ARBITRARY_CODE_REJECTED",
            "STRATEGY_ENVIRONMENT_NOT_PERMITTED",
            "STRATEGY_HARD_KILLED",
            "STRATEGY_LIFECYCLE_NOT_APPROVED",
            "STRATEGY_LOOKAHEAD_DETECTED",
            "STRATEGY_POSITION_LIMIT_EXCEEDED",
            "STRATEGY_RISK_PROFILE_REQUIRED",
            "STRATEGY_UNAPPROVED_MODULE",
            "STRATEGY_VALIDATION_ARTIFACT_REQUIRED",
        }
        else "PERMANENT"
    )
    severity = "critical" if category in {"INTEGRITY", "POLICY"} else "error"
    return ErrorDefinition(
        code=code,
        domain="strategy",
        description=f"Strategy operation failed with code {code}",
        category=category,
        severity=cast("ErrorSeverity", severity),
        retryable=False,
        operator_action="Inspect the bounded Strategy diagnostic evidence",
    )


class _CatalogValidator(Protocol):
    """Structural adapter for the Utils-owned catalogue validator."""

    def __call__(
        self, catalog: Mapping[str, ErrorDefinition]
    ) -> Mapping[str, ErrorDefinition]:
        """Validate one structurally compatible error catalogue."""


_validate_catalog = cast("_CatalogValidator", validate_error_catalog)

STRATEGY_ERROR_CATALOG = _validate_catalog(
    MappingProxyType({code: _definition(code) for code in _APPROVED_CODES})
)


def get_strategy_error_catalog() -> Mapping[str, ErrorDefinition]:
    """Return the immutable Strategy error catalogue.

    Returns:
        Immutable mapping proxy of error codes to ErrorDefinition entries.
    """
    return STRATEGY_ERROR_CATALOG


def get_strategy_error_code(value: str) -> StrategyErrorCode:
    """Return one accepted Strategy error code by value."""
    return StrategyErrorCode(value)


__all__ = [
    "STRATEGY_ERROR_CATALOG",
    "StrategyErrorCode",
    "get_strategy_error_catalog",
    "get_strategy_error_code",
]
