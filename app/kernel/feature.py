"""Business-neutral declarations for host-owned lifecycle components.

This module holds the declarations every host-owned component supplies
to the kernel: ``FeatureSpec``, the immutable record of what a
component provides and requires, and the ``Feature`` protocol, the
structural startup contract the runtime invokes. Both stay business
neutral: the kernel attaches no product, plugin, UI, persistence, or
integration meaning to any name or capability declared here.

Authority: this module is part of the standard-library kernel required
by ``AGENTS.md``. It imports only from the standard library and from
``app.kernel.capability``. Importing it performs no I/O, starts no
tasks or threads, configures no logging, and reads no environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.kernel.capability import Capability

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Declare one component's exports and mandatory startup dependencies.

    A spec is an immutable, hashable value created by the feature that
    owns it and only read by the runtime. ``provides`` names the exact
    capability set the feature must stage during ``start``; ``requires``
    names the capabilities that must already be published when
    ``start`` runs. Requirements are the only startup-ordering edges: a
    feature starts only after every feature providing one of its
    requirements.

    Attributes:
        name: Unique feature name within one composition.
        provides: Exact set of capabilities staged and published on a
            successful start.
        requires: Capabilities that must be published by other
            features before this feature starts.
        description: Presentation metadata excluded from equality and
            hashing.
    """

    name: str
    provides: frozenset[Capability[Any]] = frozenset()
    requires: frozenset[Capability[Any]] = frozenset()
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Reject ambiguous names, mutable declarations, and self-dependency.

        Raises:
            ValueError: If ``name`` is empty or padded with outer
                whitespace, or if the same capability is both provided
                and required.
            TypeError: If ``provides`` or ``requires`` is not exactly a
                ``frozenset`` instance.
        """
        if not self.name or self.name != self.name.strip():
            raise ValueError("Feature names must be nonempty and trimmed")
        if type(self.provides) is not frozenset or type(self.requires) is not frozenset:
            raise TypeError("Capability declarations must be frozensets")
        if self.provides & self.requires:
            raise ValueError("A feature cannot require its own export")


@runtime_checkable
class Feature(Protocol):
    """Structural startup contract implemented by host-owned components.

    The protocol is ``runtime_checkable`` and purely structural: any
    object exposing a ``spec`` property and an async ``start`` method
    satisfies it, with no base class, registration, or import-time
    coupling. The runtime awaits each feature's ``start`` sequentially,
    one feature at a time, after that feature's providers are
    published; implementations must acquire their owned resources and
    stage every declared export through the given context before
    returning.
    """

    @property
    def spec(self) -> FeatureSpec:
        """Return this component's immutable lifecycle declaration."""
        ...

    async def start(self, context: FeatureContext) -> None:
        """Acquire owned resources and stage every declared export.

        The received context is restricted to this feature's spec:
        dependency reads through ``context.require``, export staging
        through ``context.provide``, and owned resources, cleanup
        callbacks, and tasks registered on the same scope. The runtime
        commits the export bundle after this coroutine returns, and
        closes the scope in reverse startup order during shutdown.

        Args:
            context: The scope owned by this feature for its whole
                lifetime.

        Raises:
            Exception: Any failure aborts composition; the runtime
                unwinds this feature's scope and every already-started
                scope before propagating it.
        """
        ...


__all__ = ("Feature", "FeatureSpec")
