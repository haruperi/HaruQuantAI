from dataclasses import dataclass

"""Accepted deterministic Strategy error catalogue."""

from enum import StrEnum
from types import MappingProxyType
from typing import Literal, cast

from app.utils import validate_error_catalog


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
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
        "internal"
        if code == "STRATEGY_INTERNAL_ERROR"
        else "safety"
        if code in {"STRATEGY_HARD_KILLED", "STRATEGY_LOOKAHEAD_DETECTED"}
        else "resource"
        if code in {"STRATEGY_RESOURCE_LIMIT_EXCEEDED", "STRATEGY_TIMEOUT"}
        else "validation"
    )
    severity = "critical" if category in {"internal", "safety"} else "error"
    return ErrorDefinition(
        code=code,
        domain="strategy",
        description=f"Strategy operation failed with code {code}",
        category=category,
        severity=cast("ErrorSeverity", severity),
        retryable=False,
        operator_action="Inspect the bounded Strategy diagnostic evidence",
    )


STRATEGY_ERROR_CATALOG = validate_error_catalog(
    MappingProxyType({code: _definition(code) for code in _APPROVED_CODES})
)


__all__ = ["STRATEGY_ERROR_CATALOG", "StrategyErrorCode"]
