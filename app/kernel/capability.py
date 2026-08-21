"""Capability key and identification primitives for the composition kernel."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityKey[T]:
    """Stable identifier for one versioned capability contract.

    Attributes:
        name: Capability domain and name (e.g., 'data.historical-bars').
        major: SemVer major version of the capability contract.
    """

    name: str
    major: int = 1

    @property
    def identifier(self) -> str:
        """Return the formatted capability identifier string.

        Returns:
            Formatted identifier string '<name>@<major>'.
        """
        return f"{self.name}@{self.major}"


class CapabilityError(RuntimeError):
    """Base exception for capability-related errors."""


class CapabilityUnavailableError(CapabilityError):
    """Raised when a requested capability has no active provider in the registry.

    Attributes:
        capability: The identifier of the missing capability.
        blocked_by: Optional identifier of the upstream dependency causing blockage.
    """

    def __init__(self, capability: str, blocked_by: str | None = None) -> None:
        """Initialize the capability unavailable error.

        Args:
            capability: The identifier of the unavailable capability.
            blocked_by: Optional upstream capability identifier causing the blockage.
        """
        self.capability = capability
        self.blocked_by = blocked_by
        message = f"Capability '{capability}' is unavailable"
        if blocked_by:
            message += f" (blocked by '{blocked_by}')"
        super().__init__(message)
