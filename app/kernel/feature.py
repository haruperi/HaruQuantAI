"""Business-neutral declarations for host-owned lifecycle components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.kernel.capability import Capability

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Declare one component's exports and mandatory startup dependencies."""

    name: str
    provides: frozenset[Capability[Any]] = frozenset()
    requires: frozenset[Capability[Any]] = frozenset()
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Reject ambiguous names, mutable declarations, and self-dependency."""
        if not self.name or self.name != self.name.strip():
            raise ValueError("Feature names must be nonempty and trimmed")
        if type(self.provides) is not frozenset or type(self.requires) is not frozenset:
            raise TypeError("Capability declarations must be frozensets")
        if self.provides & self.requires:
            raise ValueError("A feature cannot require its own export")


@runtime_checkable
class Feature(Protocol):
    """Structural startup contract implemented by host-owned components."""

    @property
    def spec(self) -> FeatureSpec:
        """Return this component's immutable lifecycle declaration."""
        ...

    async def start(self, context: FeatureContext) -> None:
        """Acquire owned resources and stage every declared export."""
        ...


__all__ = ("Feature", "FeatureSpec")
