"""Topological Bootstrapper and Composition Runtime.

In a modular microkernel architecture with decoupled features, managing
startup sequence, dependency injection, and resource lifecycles manually
is brittle and error-prone:
- If Feature B depends on Feature A, Feature A must start first.
- If Feature A and Feature B both attempt to provide the same capability,
  the system has an ambiguous provider conflict.
- If Feature A depends on Feature B and Feature B depends on Feature A,
  the system suffers a circular dependency deadlock.
- If Feature B requires a capability not provided by any feature, the system
  should fail fast before running side-effecting code.
- If Feature B optionally uses Feature A, Feature A should start first when
  present, without causing a deadlock if a cycle exists.

The `Runtime` solves these problems systematically:
1. Provider Conflict Detection: Verifies that no two features claim to provide
   the same capability token.
2. Fail-Fast Graph Closure: Validates that all mandatory `requires` dependencies
   are satisfied within the active feature set before starting any feature.
3. Cycle-Safe Topological Sorting (Kahn's Algorithm): Resolves declared dependencies
   and non-cyclic optional enhancements into a deterministic startup order.
4. Dynamic Subset Filtering: Allows activating named profiles or explicit feature
   subsets (`enabled`) while strictly verifying dependency closure.
5. Transactional Export Publication: Staged capability exports are committed
   atomically only after a feature's `start()` method completes successfully.
6. LIFO Teardown & Exception Aggregation: Uses Python's `AsyncExitStack` to unwind
   all feature resources in exact reverse acquisition order, grouping any cleanup
   failures into a `BaseExceptionGroup`.

Example:
    >>> factories = [DatabaseFeature, CacheFeature, UserFeature]
    >>> async with Runtime(factories) as app:
    ...     user_service = app.require(USER_SERVICE)
    ...     # Application is fully wired and running!
    ...     # On block exit, resources are torn down in exact reverse order.
"""

from collections.abc import Callable, Sequence
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any, Self, cast

from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import FeatureContext
from app.kernel.events import EventBus
from app.kernel.feature import Feature, FeatureSpec
from app.kernel.logging import get_logger

logger = get_logger(__name__)
type FeatureFactory = Callable[[], Feature]


def _is_reachable(start: str, target: str, graph: dict[str, set[str]]) -> bool:
    """Return True if target is reachable from start in graph via depth-first search.

    Used by the topological sorter to determine if adding an optional dependency
    edge from a consumer to an optional provider would introduce a directed cycle.

    Args:
        start: Starting node name in the dependency graph.
        target: Target node name to check reachability for.
        graph: Adjacency list mapping node names to their upstream dependencies.

    Returns:
        True if target can be reached from start; False otherwise.
    """
    visited: set[str] = set()
    stack: list[str] = [start]
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node not in visited:
            visited.add(node)
            stack.extend(graph.get(node, ()))
    return False


class Runtime:
    """Compose one graph per async context; reject invalid graphs before startup.

    The `Runtime` manages the complete lifecycle of a composable application.
    It takes a collection of feature factories, validates capability uniqueness
    and dependency requirements, sorts features in dependency order, activates
    them asynchronously, and guarantees reverse-order cleanup upon shutdown.

    Attributes:
        _factories: Immutable tuple of feature factories passed at initialization.
        _enabled: Optional set of feature names to activate for dynamic subsets.
        _providers: Registry mapping typed `Capability` tokens to active
            implementations.
        _stack: Root `AsyncExitStack` managing all feature lifecycles and resources.
        _used: Guard preventing multi-use execution of a single runtime instance.
        _active: Flag indicating whether startup completed and services are accessible.
        _active_features: List of active feature names in startup order.
        _cleanup_errors: List accumulating any exceptions raised during scope teardown.
    """

    def __init__(
        self,
        factories: Sequence[FeatureFactory],
        enabled: frozenset[str] | set[str] | Sequence[str] | None = None,
    ) -> None:
        """Initialize the composition runtime.

        Args:
            factories: Sequence of callable factories that instantiate `Feature`
                instances.
            enabled: Optional collection of feature names to activate. When provided,
                only features whose names are in this set will be booted. Passing an
                unrecognized name raises ValueError.
        """
        self._factories = tuple(factories)
        self._enabled: frozenset[str] | None = (
            frozenset(enabled) if enabled is not None else None
        )
        self._providers: dict[Capability[Any], object] = {}
        self._stack = AsyncExitStack()
        self._used = False
        self._active = False
        self._active_features: list[str] = []
        self._cleanup_errors: list[BaseException] = []

    @property
    def active_features(self) -> tuple[str, ...]:
        """Return the names of all currently active features in startup order."""
        return tuple(self._active_features)

    async def _close_scope(self, context: FeatureContext, feature_name: str) -> None:
        """Retain scope failures while allowing all other scopes to close.

        Invoked as an async callback on the root stack during shutdown. Captures
        any exceptions into `_cleanup_errors` so that a failure in one feature's
        cleanup routine does not prevent subsequent features from unwinding.

        Args:
            context: The feature context whose owned resources and tasks should close.
            feature_name: Name of the feature being closed, used for diagnostics.
        """
        try:
            await context.close()
        except BaseException as error:
            logger.warning(
                "feature_cleanup_failed",
                feature=feature_name,
                error=str(error),
                error_type=type(error).__name__,
            )
            self._cleanup_errors.append(error)

    def _ordered(self) -> list[tuple[Feature, FeatureSpec]]:
        """Validate uniqueness and dependencies, then sort deterministically.

        Algorithm Walkthrough:
        1. Instantiation & Filtering: Instantiates features from factories and filters
           by `enabled` if a dynamic subset was specified. Raises ValueError if unknown
           names were provided.
        2. Conflict Detection: Ensures all feature names are unique and that no two
           features provide the same `Capability` key.
        3. Fail-Fast Closure Check: Verifies that all `requires` dependencies are
           present in the exported capabilities of the active subset. Raises
           `CapabilityUnavailableError` if any requirement is missing.
        4. Graph Construction: Builds the dependency graph:
           - Adds mandatory edges from consumers to required providers.
           - Adds optional edges from consumers to active optional providers, provided
             the addition does not introduce a circular dependency cycle.
        5. Kahn's Algorithm: Computes in-degrees and uses a FIFO queue to determine a
           valid execution sequence where providers always boot before consumers.
        6. Cycle Detection: If the resolved order contains fewer features than the
           active graph, raises ValueError for a circular dependency cycle.

        Returns:
            A list of (Feature, FeatureSpec) tuples arranged in valid startup order.

        Raises:
            ValueError: If duplicate names/providers exist, unknown enabled features
                were specified, or a circular dependency cycle is detected.
            CapabilityUnavailableError: If any feature has an unfulfilled required
                dependency in the active subset.
        """
        all_candidates = [
            (feature, feature.spec) for feature in (f() for f in self._factories)
        ]
        if self._enabled is not None:
            known_names = {spec.name for _, spec in all_candidates}
            if unknown := self._enabled - known_names:
                raise ValueError(
                    f"Unknown enabled feature(s): {', '.join(sorted(unknown))}"
                )
            pending = [item for item in all_candidates if item[1].name in self._enabled]
            logger.info(
                "runtime_subset_selected",
                enabled_count=len(pending),
                total_candidates=len(all_candidates),
                enabled_features=[spec.name for _, spec in pending],
            )
        else:
            pending = list(all_candidates)

        names: set[str] = set()
        exports: set[Capability[Any]] = set()
        for _, spec in pending:
            if spec.name in names or exports & spec.provides:
                raise ValueError("Duplicate feature name or capability provider")
            names.add(spec.name)
            exports.update(spec.provides)

        for _, spec in pending:
            if missing := spec.requires - exports:
                key = sorted(missing, key=lambda item: (item.name, item.major))[0]
                raise CapabilityUnavailableError(f"{spec.name}: {key.name}")

        provider_of: dict[Capability[Any], str] = {
            cap: spec.name for _, spec in pending for cap in spec.provides
        }
        deps: dict[str, set[str]] = {spec.name: set() for _, spec in pending}

        for _, spec in pending:
            for req in spec.requires:
                provider = provider_of.get(req)
                if provider is not None and provider != spec.name:
                    deps[spec.name].add(provider)

        for _, spec in pending:
            for opt in spec.optional:
                provider = provider_of.get(opt)
                if (
                    provider is not None
                    and provider != spec.name
                    and not _is_reachable(provider, spec.name, deps)
                ):
                    deps[spec.name].add(provider)
                    logger.debug(
                        "optional_dependency_linked",
                        consumer=spec.name,
                        provider=provider,
                        capability=opt.name,
                    )

        by_name = {spec.name: (feat, spec) for feat, spec in pending}
        indegree = {name: len(prereqs) for name, prereqs in deps.items()}
        dependents: dict[str, list[str]] = {name: [] for name in deps}
        for name, prereqs in deps.items():
            for prereq in prereqs:
                dependents[prereq].append(name)

        queue = [name for name, deg in indegree.items() if deg == 0]
        order: list[str] = []
        while queue:
            name = queue.pop(0)
            order.append(name)
            for child in dependents[name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(order) != len(pending):
            raise ValueError("Required dependency cycle")

        logger.debug(
            "runtime_graph_ordered",
            feature_order=order,
            count=len(order),
        )
        return [by_name[name] for name in order]

    async def __aenter__(self) -> Self:
        """Start the graph and expose it only once every feature is ready.

        Instantiates and orders candidate features, registers an `AsyncExitStack`
        scope for each feature, executes `feature.start(ctx)`, and transactionally
        commits each feature's declared exports to the provider registry.

        If an exception occurs during the startup of any feature, the runtime
        immediately executes a full rollback, unwinding all previously initialized
        features in reverse order before re-raising the error.

        Returns:
            The active `Runtime` instance with all services available for lookup.

        Raises:
            RuntimeError: If this runtime instance was already used.
            BaseExceptionGroup: If startup failed and cleanup also encountered errors.
            Exception: If any feature raises an exception during startup.
        """
        if self._used:
            raise RuntimeError("Runtime instances are single-use")
        self._used = True
        events = EventBus()
        ordered = self._ordered()
        logger.info(
            "runtime_starting",
            feature_count=len(ordered),
        )
        try:
            for feature, spec in ordered:
                logger.debug(
                    "feature_starting",
                    feature=spec.name,
                    requires=[c.name for c in spec.requires],
                    optional=[c.name for c in spec.optional],
                )
                context = FeatureContext(spec, self._providers, events)
                self._stack.push_async_callback(self._close_scope, context, spec.name)
                try:
                    await feature.start(context)
                except BaseException as feat_err:
                    logger.error(
                        "feature_start_failed",
                        feature=spec.name,
                        error=str(feat_err),
                        error_type=type(feat_err).__name__,
                    )
                    raise
                committed = context.commit_exports()
                self._providers.update(committed)
                logger.debug(
                    "feature_started",
                    feature=spec.name,
                    exports=[c.name for c in committed],
                )
            self._active = True
            self._active_features = [spec.name for _, spec in ordered]
            logger.info(
                "runtime_started",
                feature_count=len(ordered),
                capability_count=len(self._providers),
            )
        except BaseException as startup_error:
            logger.error(
                "runtime_start_failed",
                error=str(startup_error),
                error_type=type(startup_error).__name__,
            )
            try:
                await self.close()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup(
                    "Startup and cleanup failed", [startup_error, cleanup_error]
                ) from None
            raise
        return self

    def has(self, key: Capability[Any]) -> bool:
        """Return True if the capability is available in the active runtime.

        Args:
            key: The typed `Capability` token to check.

        Returns:
            True if the runtime is active and the key is registered; False otherwise.
        """
        return self._active and key in self._providers

    def get[T](self, key: Capability[T], default: T | None = None) -> T | None:
        """Resolve a capability or return default if unavailable.

        Args:
            key: The typed `Capability` token to resolve.
            default: Value to return if the capability is not available.

        Returns:
            The service instance implementing the capability, or the default value.
        """
        if not self._active or key not in self._providers:
            return default
        return cast("T", self._providers[key])

    def require[T](self, key: Capability[T]) -> T:
        """Resolve a capability from a fully started application.

        Args:
            key: The typed `Capability` token identifying the requested service.

        Returns:
            The concrete service instance implementing the requested capability.

        Raises:
            CapabilityUnavailableError: If the runtime is not active or the key
                is not present in the provider registry.
        """
        if not self._active or key not in self._providers:
            raise CapabilityUnavailableError(key.name)
        return cast("T", self._providers[key])

    async def close(self) -> None:
        """Stop admission and unwind scopes before withdrawing providers.

        Marks the runtime as inactive, closes all feature scopes and owned tasks
        via the root `AsyncExitStack` in reverse LIFO order, and clears the provider
        registry.

        Raises:
            BaseExceptionGroup: If any exceptions were encountered during feature
                cleanup callbacks or task cancellations.
        """
        self._active = False
        logger.info("runtime_stopping")
        try:
            await self._stack.aclose()
        finally:
            self._providers.clear()
            self._active_features.clear()
            logger.info(
                "runtime_stopped",
                cleanup_errors=len(self._cleanup_errors),
            )
        if self._cleanup_errors:
            errors, self._cleanup_errors = self._cleanup_errors, []
            raise BaseExceptionGroup("Runtime cleanup failed", errors)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the application without suppressing caller exceptions.

        Ensures that `close()` is executed when exiting an `async with` block.
        If both the block body and runtime cleanup raise exceptions, groups them
        into a single `BaseExceptionGroup`.

        Args:
            exc_type: The exception type raised within the block, if any.
            exc: The exception instance raised within the block, if any.
            traceback: The traceback of the exception, if any.

        Raises:
            BaseExceptionGroup: If both block execution and cleanup failed.
            BaseException: If cleanup failed when no prior exception occurred.
        """
        try:
            await self.close()
        except BaseException as cleanup_error:
            if exc is not None:
                raise BaseExceptionGroup(
                    "Application and cleanup failed", [exc, cleanup_error]
                ) from None
            raise
