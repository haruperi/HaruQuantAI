# cspell:words subtyping frozensets lifecycles
# pylint: disable=unnecessary-ellipsis
"""Declarative Feature Manifests and Startup Protocol.

In this architecture, a **Feature** is the fundamental modular building block.
Every major business capability — whether authentication, database persistence,
notification delivery, or background workers — is packaged as an independent,
single-file Feature.

The Anatomy of a Feature:
Every feature is defined by an immutable manifest (`FeatureSpec`) and an
asynchronous startup method (`start`):
1. `spec`: A `FeatureSpec` instance declaring the feature's name, published
   capabilities (`provides`), mandatory dependencies (`requires`), and optional
   enhancements (`optional`).
2. `start(context)`: The asynchronous startup method where the feature acquires
   its resources, stages provided services via `context.provide()`, and
   registers managed background tasks (`context.spawn()`) or cleanup routines
   (`context.on_close()`).

Why Protocol?
`Feature` is defined as a `typing.Protocol` (structural subtyping / duck typing).
Domain features do not need to inherit from any kernel base class. As long as a
class provides a `spec` attribute and an asynchronous `start(context)` method,
static type checkers and the runtime treat it as a valid `Feature`.

Example:
    Define a self-contained feature:
    >>> class DatabaseFeature:
    ...     spec = FeatureSpec(
    ...         name="database",
    ...         provides=frozenset({DATABASE_POOL}),
    ...         description="PostgreSQL connection pool provider",
    ...     )
    ...
    ...     async def start(self, context: FeatureContext) -> None:
    ...         pool = await create_pool()
    ...         context.on_close(pool.close)
    ...         context.provide(DATABASE_POOL, pool)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.kernel.capability import Capability

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """Declare a feature's exports, dependencies, and optional dependencies.

    A `FeatureSpec` is an immutable, validated manifest defining the public
    boundaries and requirements of a single feature. The runtime uses this
    specification to validate dependency graph closure, resolve startup
    sequence, and prevent duplicate capability providers before booting.

    Attributes:
        name: A unique, human-readable identifier for this feature.
        provides: Set of `Capability` keys published by this feature.
        requires: Set of mandatory `Capability` keys needed before start.
        optional: Set of optional `Capability` keys used if present.
        description: Brief documentation describing what the feature does.
    """

    name: str
    provides: frozenset[Capability[Any]] = frozenset()
    requires: frozenset[Capability[Any]] = frozenset()
    optional: frozenset[Capability[Any]] = frozenset()
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Validate declaration invariants upon construction.

        Raises:
            ValueError: If feature name is empty, if the feature depends on its
                own exports, or if a capability is both required and optional.
            TypeError: If provides, requires, or optional are not frozensets.
        """
        if not self.name.strip():
            raise ValueError("Feature name must be nonempty")
        if (
            type(self.provides) is not frozenset
            or type(self.requires) is not frozenset
            or type(self.optional) is not frozenset
        ):
            raise TypeError("Capability declarations must be frozensets")
        if self.provides & (self.requires | self.optional):
            raise ValueError("A feature cannot depend on its own exports")
        if self.requires & self.optional:
            raise ValueError("A capability cannot be both required and optional")

    @property
    def dependencies(self) -> frozenset[Capability[Any]]:
        """Return all declared dependencies, both required and optional."""
        return self.requires | self.optional


@runtime_checkable
class Feature(Protocol):
    """The structural contract that all domain features must satisfy.

    Any class or object providing an immutable `spec` manifest and an
    asynchronous `start(context)` method is considered a valid `Feature`.

    Attributes:
        spec: The feature's immutable declared manifest boundaries.
    """

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature's declared boundaries."""
        ...

    async def start(self, context: FeatureContext) -> None:
        """Acquire owned resources and stage every declared export.

        This method is invoked by the `Runtime` during application startup,
        after all declared dependencies in `requires` have been successfully
        started and committed.

        Args:
            context: The per-feature execution environment providing dependency
                lookup, export staging, and managed effect lifecycles.
        """
        ...
