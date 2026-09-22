"""Immutable typed identities for explicitly bound host contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override


@dataclass(frozen=True, slots=True)
class Capability[T]:
    """Identify one public contract and its compatibility major."""

    name: str
    major: int = 1
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Reject ambiguous names and invalid compatibility majors."""
        if (
            not self.name
            or self.name != self.name.strip()
            or any(character.isspace() for character in self.name)
        ):
            raise ValueError("Capability names must be nonempty and contain no space")
        if self.major < 1:
            raise ValueError("Capability majors must be positive")

    @property
    def identifier(self) -> str:
        """Return the stable name and compatibility-major identity."""
        return f"{self.name}@{self.major}"

    @override
    def __repr__(self) -> str:
        """Return a concise representation independent of the description."""
        return f"Capability({self.name!r}, major={self.major})"


class CapabilityUnavailableError(LookupError):
    """Report one unavailable declared capability with optional attribution."""

    def __init__(self, capability: str, *, blocked_by: str | None = None) -> None:
        self.capability = capability
        self.blocked_by = blocked_by
        message = capability
        if blocked_by is not None:
            message = f"{message} (blocked by {blocked_by!r})"
        super().__init__(message)


__all__ = ("Capability", "CapabilityUnavailableError")
