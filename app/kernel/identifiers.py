"""Validated identifiers and semantic versions for spatiotemporal provider architecture.

Traces to: P4-T01, Gate G4
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import override

_IDENT_SEGMENT_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True, slots=True, order=True)
class CapabilityId:
    """Validated capability identifier representing a contract specification."""

    domain: str
    capability: str
    major: int

    @classmethod
    def parse(cls, value: str) -> CapabilityId:
        """Parse and validate a capability identifier string.

        Format: `<domain>.<capability>.v<major>`
        Example: `indicator.rsi.v1`

        Args:
            value: The string representation to parse.

        Returns:
            Validated CapabilityId instance.

        Raises:
            ValueError: If value is not a valid capability ID string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid capability id: {value!r}")

        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid capability id: {value!r}")

        domain, capability, major_str = parts
        if not _IDENT_SEGMENT_PATTERN.match(domain) or not _IDENT_SEGMENT_PATTERN.match(
            capability
        ):
            raise ValueError(f"invalid capability id: {value!r}")

        if not major_str.startswith("v") or len(major_str) < 2:
            raise ValueError(f"invalid capability id: {value!r}")

        try:
            major = int(major_str[1:])
        except ValueError:
            raise ValueError(f"invalid capability id: {value!r}") from None

        if major < 1:
            raise ValueError(f"invalid capability id: {value!r}")

        return cls(domain=domain, capability=capability, major=major)

    @override
    def __str__(self) -> str:
        """Format back to canonical string representation."""
        return f"{self.domain}.{self.capability}.v{self.major}"


@dataclass(frozen=True, slots=True, order=True)
class ProviderId:
    """Validated provider identifier representing a concrete provider implementation."""

    domain: str
    capability: str
    implementation: str

    @classmethod
    def parse(cls, value: str) -> ProviderId:
        """Parse and validate a provider identifier string.

        Format: `<domain>.<capability>.<implementation>`
        Example: `indicator.rsi.default`

        Args:
            value: The string representation to parse.

        Returns:
            Validated ProviderId instance.

        Raises:
            ValueError: If value is not a valid provider ID string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid provider id: {value!r}")

        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid provider id: {value!r}")

        domain, capability, implementation = parts
        if (
            not _IDENT_SEGMENT_PATTERN.match(domain)
            or not _IDENT_SEGMENT_PATTERN.match(capability)
            or not _IDENT_SEGMENT_PATTERN.match(implementation)
        ):
            raise ValueError(f"invalid provider id: {value!r}")

        return cls(
            domain=domain,
            capability=capability,
            implementation=implementation,
        )

    @override
    def __str__(self) -> str:
        """Format back to canonical string representation."""
        return f"{self.domain}.{self.capability}.{self.implementation}"


@dataclass(frozen=True, slots=True, order=True)
class SemanticVersion:
    """Validated three-component semantic version `MAJOR.MINOR.PATCH`."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemanticVersion:
        """Parse and validate a three-part semantic version string.

        Format: `<major>.<minor>.<patch>`
        Example: `1.0.0`

        Args:
            value: The string to parse.

        Returns:
            Validated SemanticVersion instance.

        Raises:
            ValueError: If value is not a valid semantic version string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid semantic version: {value!r}")

        m = _VERSION_PATTERN.match(value)
        if not m:
            raise ValueError(f"invalid semantic version: {value!r}")

        return cls(
            major=int(m.group(1)),
            minor=int(m.group(2)),
            patch=int(m.group(3)),
        )

    @override
    def __str__(self) -> str:
        """Format back to canonical string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"


__all__ = (
    "CapabilityId",
    "ProviderId",
    "SemanticVersion",
)
