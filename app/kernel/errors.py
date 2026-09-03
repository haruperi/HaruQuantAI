"""Minimal shared exception hierarchy and capability error definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

_SYMBOLIC_TOKEN = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


class HaruQuantError(Exception):
    """Base exception carrying only boundary-safe symbolic evidence."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize a shared exception.

        Args:
            code: Uppercase symbolic error code.
            detail: Uppercase symbolic safe detail.

        Raises:
            ValueError: If either token is malformed.
        """
        if _SYMBOLIC_TOKEN.fullmatch(code) is None:
            raise ValueError("code must be an uppercase symbolic token")
        if _SYMBOLIC_TOKEN.fullmatch(detail) is None:
            raise ValueError("detail must be an uppercase symbolic token")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


class ConfigurationError(HaruQuantError):
    """Invalid or unavailable configuration."""


class ValidationError(HaruQuantError):
    """Invalid shared-boundary value."""

    details: Any = None


class SecurityError(HaruQuantError):
    """Security policy or secret-resolution failure."""


class ExternalServiceError(HaruQuantError):
    """External service boundary failure."""


class CapabilityReasonCode(StrEnum):
    """Standardized capability failure and unreadiness reason codes."""

    NOT_INSTALLED = "NOT_INSTALLED"
    DISABLED = "DISABLED"
    VERSION_INCOMPATIBLE = "VERSION_INCOMPATIBLE"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    PROVIDER_AMBIGUOUS = "PROVIDER_AMBIGUOUS"
    CONFIG_INVALID = "CONFIG_INVALID"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    UNHEALTHY = "UNHEALTHY"
    DRAINING = "DRAINING"
    LOST_DURING_OPERATION = "LOST_DURING_OPERATION"
    PROFILE_REQUIREMENT_UNSATISFIED = "PROFILE_REQUIREMENT_UNSATISFIED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    CLEANUP_FAILED = "CLEANUP_FAILED"


@dataclass(frozen=True, slots=True)
class CapabilityUnavailable:
    """Structured evidence for an unavailable or unready capability."""

    code: Literal["CAPABILITY_UNAVAILABLE"]
    reason_code: CapabilityReasonCode
    capability: str
    consumer: str | None
    provider_id: str | None
    provider_state: str | None
    profile: str | None
    dependency_chain: tuple[str, ...]
    retryable: bool


def capability_unavailable_payload(detail: CapabilityUnavailable) -> dict[str, object]:
    """Project a CapabilityUnavailable record to a JSON-safe dictionary.

    Args:
        detail: Capability unreadiness record.

    Returns:
        JSON-serializable dictionary.

    Raises:
        ValueError: If dependency_chain does not terminate with target capability.
    """
    if not detail.dependency_chain or detail.dependency_chain[-1] != detail.capability:
        raise ValueError("dependency_chain must end with capability")
    return {
        "code": "CAPABILITY_UNAVAILABLE",
        "reason_code": detail.reason_code.value,
        "capability": detail.capability,
        "consumer": detail.consumer,
        "provider_id": detail.provider_id,
        "provider_state": detail.provider_state,
        "profile": detail.profile,
        "dependency_chain": list(detail.dependency_chain),
        "retryable": detail.retryable,
    }


class CapabilityUnavailableError(RuntimeError):
    """Exception raised when a required capability cannot be resolved or leased."""

    def __init__(self, detail: CapabilityUnavailable | str) -> None:
        """Initialize with capability unavailable record or string identifier.

        Args:
            detail: Structured unreadiness evidence or capability string.
        """
        if isinstance(detail, str):
            self.detail = CapabilityUnavailable(
                code="CAPABILITY_UNAVAILABLE",
                reason_code=CapabilityReasonCode.NOT_INSTALLED,
                capability=detail,
                consumer=None,
                provider_id=None,
                provider_state=None,
                profile=None,
                dependency_chain=(detail,),
                retryable=False,
            )
            super().__init__(f"capability {detail} unavailable (NOT_INSTALLED)")
        else:
            self.detail = detail
            code_val = getattr(detail.reason_code, "value", str(detail.reason_code))
            super().__init__(f"capability {detail.capability} unavailable ({code_val})")


class ManifestValidationError(ValueError):
    """Manifest structure or metadata constraint violation."""


class ResolutionError(RuntimeError):
    """Capability graph or provider resolution failure."""


class LifecycleError(RuntimeError):
    """Feature or provider lifecycle state violation."""


def create_validation_error(
    message: str = "Validation failed", *, details: Any = None
) -> ValidationError:
    """Construct a ValidationError exception instance."""
    err = ValidationError(message)
    if details is not None:
        err.details = details
    return err


def normalize_error_code(code: str) -> str:
    """Normalize error code to uppercase with underscores."""
    return code.strip().upper().replace("-", "_").replace(" ", "_")


def validate_error_catalog(catalog: Any) -> bool:
    """Validate that an error catalog or dictionary is non-empty and well-formed."""
    if not catalog:
        return False
    if isinstance(catalog, dict):
        return all(isinstance(k, str) for k in catalog)
    return True


def get_common_error_catalog() -> dict[str, Any]:
    """Return the common system error catalog."""
    return {
        "VALIDATION_FAILED": "Input validation failed",
        "CAPABILITY_UNAVAILABLE": "Requested capability is unavailable",
        "NOT_FOUND": "Resource not found",
        "CONFIGURATION_ERROR": "Invalid runtime configuration",
        "SECURITY_ERROR": "Security or permission violation",
        "EXTERNAL_SERVICE_ERROR": "External integration failure",
        "INTERNAL_ERROR": "Internal execution error",
    }


def map_exception(exc: Exception) -> dict[str, str]:
    """Map a generic Python exception to safe symbolic code and detail.

    Args:
        exc: Caught Python exception.

    Returns:
        Mapping containing safe uppercase symbolic code and detail.
    """
    if isinstance(exc, HaruQuantError):
        return {"code": exc.code, "detail": exc.detail}
    if isinstance(exc, (ValueError, TypeError)):
        return {"code": "VALIDATION_FAILED", "detail": "INVALID_ARGUMENT"}
    if isinstance(exc, PermissionError):
        return {"code": "SECURITY_ERROR", "detail": "PERMISSION_DENIED"}
    if isinstance(exc, TimeoutError):
        return {"code": "EXTERNAL_SERVICE_ERROR", "detail": "TIMEOUT"}
    return {"code": "INTERNAL_ERROR", "detail": "UNSPECIFIED"}
