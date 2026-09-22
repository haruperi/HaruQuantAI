"""Validate and run one fixed graph of host-owned lifecycle components."""

from __future__ import annotations

import heapq
from collections.abc import Callable, Sequence
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any, Self, cast

from app.kernel.capability import Capability, CapabilityUnavailableError
from app.kernel.context import DiagnosticSink, FeatureContext, KernelDiagnostic
from app.kernel.feature import Feature, FeatureSpec

type FeatureFactory = Callable[[], Feature]


def _ignore_diagnostic(_diagnostic: KernelDiagnostic) -> None:
    """Accept a lifecycle diagnostic when no observer was injected."""


class Runtime:
    """Start an immutable required-dependency graph and own its cleanup."""

    def __init__(
        self,
        factories: Sequence[FeatureFactory],
        enabled: frozenset[str] | set[str] | Sequence[str] | None = None,
        *,
        diagnostic_sink: DiagnosticSink = _ignore_diagnostic,
    ) -> None:
        self._factories = tuple(factories)
        self._enabled = frozenset(enabled) if enabled is not None else None
        self._diagnostic_sink = diagnostic_sink
        self._providers: dict[Capability[Any], object] = {}
        self._stack = AsyncExitStack()
        self._used = False
        self._active = False
        self._closed = False
        self._active_features: list[str] = []
        self._cleanup_errors: list[BaseException] = []

    @property
    def active_features(self) -> tuple[str, ...]:
        """Return a stable composition report without exposing providers."""
        return tuple(self._active_features)

    def _diagnose(self, code: str, owner: str = "runtime", detail: str = "") -> None:
        try:
            self._diagnostic_sink(KernelDiagnostic(code, owner, detail))
        except BaseException:
            return

    def _ordered(self) -> list[tuple[Feature, FeatureSpec]]:
        candidates = [(feature, feature.spec) for feature in self._make_features()]
        by_name: dict[str, tuple[Feature, FeatureSpec]] = {}
        provider_of: dict[Capability[Any], str] = {}
        for feature, spec in candidates:
            if spec.name in by_name:
                raise ValueError(f"Duplicate feature name: {spec.name}")
            by_name[spec.name] = (feature, spec)
            for capability in spec.provides:
                if existing := provider_of.get(capability):
                    raise ValueError(
                        f"Duplicate provider for {capability.identifier}: "
                        f"{existing}, {spec.name}"
                    )
                provider_of[capability] = spec.name

        dependencies: dict[str, set[str]] = {name: set() for name in by_name}
        dependents: dict[str, list[str]] = {name: [] for name in by_name}
        for name, (_, spec) in by_name.items():
            for required in spec.requires:
                provider = provider_of.get(required)
                if provider is None:
                    raise CapabilityUnavailableError(
                        required.identifier, blocked_by=spec.name
                    )
                dependencies[name].add(provider)
                dependents[provider].append(name)

        indegree = {name: len(required) for name, required in dependencies.items()}
        ready = [name for name, count in indegree.items() if count == 0]
        heapq.heapify(ready)
        ordered_names: list[str] = []
        while ready:
            name = heapq.heappop(ready)
            ordered_names.append(name)
            for dependent in sorted(dependents[name]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(ready, dependent)
        if len(ordered_names) != len(by_name):
            cycle_members = sorted(name for name, count in indegree.items() if count)
            raise ValueError(f"Required dependency cycle: {', '.join(cycle_members)}")
        return [by_name[name] for name in ordered_names]

    def _make_features(self) -> tuple[Feature, ...]:
        all_features = tuple(factory() for factory in self._factories)
        if self._enabled is None:
            return all_features
        known = {feature.spec.name for feature in all_features}
        if unknown := self._enabled - known:
            raise ValueError(
                f"Unknown enabled feature(s): {', '.join(sorted(unknown))}"
            )
        return tuple(
            feature for feature in all_features if feature.spec.name in self._enabled
        )

    async def _close_scope(self, context: FeatureContext, feature_name: str) -> None:
        try:
            await context.close()
        except BaseException as error:
            self._diagnose(
                "kernel.feature.cleanup_failed", feature_name, type(error).__name__
            )
            self._cleanup_errors.append(error)

    async def __aenter__(self) -> Self:
        """Validate first, then start and atomically publish each component."""
        if self._used:
            raise RuntimeError("Runtime instances are single-use")
        self._used = True
        ordered = self._ordered()
        try:
            for feature, spec in ordered:
                context = FeatureContext(
                    spec, self._providers, diagnostic_sink=self._diagnostic_sink
                )
                self._stack.push_async_callback(self._close_scope, context, spec.name)
                await feature.start(context)
                self._providers.update(context.commit_exports())
                self._active_features.append(spec.name)
            self._active = True
        except BaseException as startup_error:
            self._diagnose(
                "kernel.runtime.start_failed", detail=type(startup_error).__name__
            )
            try:
                await self.close()
            except BaseException as cleanup_error:
                raise BaseExceptionGroup(
                    "Startup and cleanup failed", (startup_error, cleanup_error)
                ) from None
            raise
        return self

    def require[T](self, key: Capability[T]) -> T:
        """Resolve an explicitly requested capability from an active root."""
        if not self._active or key not in self._providers:
            raise CapabilityUnavailableError(key.identifier)
        return cast("T", self._providers[key])

    async def close(self) -> None:
        """Stop admission, close consumers before providers, and withdraw values."""
        if self._closed:
            return
        self._closed = True
        self._active = False
        try:
            await self._stack.aclose()
        finally:
            self._providers.clear()
            self._active_features.clear()
        if self._cleanup_errors:
            errors, self._cleanup_errors = self._cleanup_errors, []
            raise BaseExceptionGroup("Runtime cleanup failed", errors)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close without hiding either caller or cleanup failures."""
        del exc_type, traceback
        try:
            await self.close()
        except BaseException as cleanup_error:
            if exc is not None:
                raise BaseExceptionGroup(
                    "Application and cleanup failed", (exc, cleanup_error)
                ) from None
            raise


__all__ = ("FeatureFactory", "Runtime")
