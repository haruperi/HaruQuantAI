"""Microkernel exception hierarchy, reason codes, and unavailability structures.

Traces to: P4-T02, Gate G4
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class KernelError(Exception):
    """Base exception for all microkernel errors."""


class ManifestValidationError(ValueError, KernelError):
    """Raised when a static provider manifest fails schema validation."""


class ResolutionError(RuntimeError, KernelError):
    """Raised when provider graph resolution fails due to cycles or unresolvable constraints."""


class LifecycleError(RuntimeError, KernelError):
    """Raised when component activation or deactivation fails."""

    def __init__(
        self,
        message: str,
        *,
        failures: tuple[BaseException, ...] = (),
    ) -> None:
        """Initialize LifecycleError with message and optional failures tuple."""
        super().__init__(message)
        self.failures = failures


class CapabilityReasonCode(StrEnum):
    """Standardized machine reason codes for unavailable capabilities."""

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
    """Standardized error evidence record for an unavailable capability."""

    code: Literal["CAPABILITY_UNAVAILABLE"]
    reason_code: CapabilityReasonCode
    capability: str
    consumer: str | None
    provider_id: str | None
    provider_state: str | None
    profile: str | None
    dependency_chain: tuple[str, ...]
    retryable: bool


class CapabilityUnavailableError(KernelError):
    """Raised by typed boundaries when a required capability is unavailable."""

    def __init__(self, detail: CapabilityUnavailable) -> None:
        """Initialize exception with structured unavailability evidence."""
        super().__init__(
            f"capability {detail.capability} unavailable ({detail.reason_code})"
        )
        self.detail = detail


def capability_unavailable_payload(
    detail: CapabilityUnavailable,
) -> dict[str, object]:
    """Project a CapabilityUnavailable record into a JSON-serializable dictionary.

    Args:
        detail: The structured unavailability detail record.

    Returns:
        Mapping containing all 9 normalized fields with no omitted nulls.

    Raises:
        ValueError: If dependency_chain is empty or does not end with detail.capability.
    """
    if not detail.dependency_chain or detail.dependency_chain[-1] != detail.capability:
        msg = "dependency_chain must end with capability"
        raise ValueError(msg)

    return {
        "code": detail.code,
        "reason_code": str(detail.reason_code),
        "capability": detail.capability,
        "consumer": detail.consumer,
        "provider_id": detail.provider_id,
        "provider_state": detail.provider_state,
        "profile": detail.profile,
        "dependency_chain": list(detail.dependency_chain),
        "retryable": detail.retryable,
    }


__all__ = (
    "CapabilityReasonCode",
    "CapabilityUnavailable",
    "CapabilityUnavailableError",
    "KernelError",
    "LifecycleError",
    "ManifestValidationError",
    "ResolutionError",
    "capability_unavailable_payload",
)
