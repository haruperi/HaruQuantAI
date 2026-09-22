"""Immutable typed identities for explicitly bound host contracts.

This module defines ``Capability[T]``, the typed capability primitive
every host owner composes through: contracts are declared, required,
and provided as capability values, and identity is purely structural.
A capability carries no behavior and no registration; equality and
hashing depend only on ``name`` and ``major``, so instances work as
typed slots in provider mappings and frozen declaration sets.

Authority: this module is part of the standard-library kernel required
by ``AGENTS.md``. It uses only the Python standard library and contains
no product, plugin, UI, persistence, or integration logic. Importing it
performs no I/O, starts no tasks or threads, configures no logging, and
reads no environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override


@dataclass(frozen=True, slots=True)
class Capability[T]:
    """Identify one public contract and its compatibility major.

    Instances are frozen, slotted dataclasses: immutable and hashable
    value objects, typically created once as module-level constants by
    feature authors. ``T`` is a phantom type parameter with no runtime
    field; it exists so a ``Capability[T]`` declaration types the value
    that ``FeatureContext.require`` returns for that binding.

    Identity is structural: two capabilities are equal exactly when
    their names and majors are equal, and ``description`` is excluded
    from both equality and hashing. Raising the major expresses a
    breaking change as a new binding: ``name@2`` does not match, and
    does not satisfy a requirement on, ``name@1``.

    Attributes:
        name: Unique, trimmed, space-free contract name.
        major: Compatibility major version, starting at one.
        description: Presentation metadata excluded from identity.
    """

    name: str
    major: int = 1
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Reject ambiguous names and invalid compatibility majors.

        Raises:
            ValueError: If ``name`` is empty, padded with outer
                whitespace, or contains any whitespace character, or if
                ``major`` is less than one.
        """
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
        """Return the stable name and compatibility-major identity.

        Returns:
            The ``name@major`` string naming this binding in errors
            and diagnostics.
        """
        return f"{self.name}@{self.major}"

    @override
    def __repr__(self) -> str:
        """Return a concise representation independent of the description."""
        return f"Capability({self.name!r}, major={self.major})"


class CapabilityUnavailableError(LookupError):
    """Report one unavailable declared capability with optional attribution.

    Subclassing ``LookupError`` separates a missing capability from
    programming errors such as an undeclared dependency.

    Attributes:
        capability: The unavailable ``name@major`` identifier.
        blocked_by: Name of the feature whose requirement went
            unsatisfied, or ``None`` when no feature is attributable.
    """

    def __init__(self, capability: str, *, blocked_by: str | None = None) -> None:
        self.capability = capability
        self.blocked_by = blocked_by
        message = capability
        if blocked_by is not None:
            message = f"{message} (blocked by {blocked_by!r})"
        super().__init__(message)


__all__ = ("Capability", "CapabilityUnavailableError")
