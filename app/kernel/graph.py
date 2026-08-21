"""Dependency graph construction, cycle detection, and topological ordering."""

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


class DependencyError(RuntimeError):
    """Base exception for dependency graph errors."""


class DependencyCycleError(DependencyError):
    """Raised when a circular dependency is detected among required capabilities."""

    def __init__(self, cycle: Sequence[str]) -> None:
        self.cycle = tuple(cycle)
        super().__init__(
            f"Circular required dependency detected: {' -> '.join(self.cycle)}"
        )


class AmbiguousProviderError(DependencyError):
    """Raised when multiple enabled features provide a capability without selection."""

    def __init__(self, capability: str, providers: Sequence[str]) -> None:
        self.capability = capability
        self.providers = tuple(sorted(providers))
        super().__init__(
            f"Capability '{capability}' has multiple enabled providers: "
            f"{', '.join(self.providers)}. Configure an explicit provider selection."
        )


class InvalidProviderSelectionError(DependencyError):
    """Raised when configured provider selection cannot satisfy a capability."""


@dataclass(frozen=True, slots=True)
class GraphResolution:
    """Calculated dependency resolution and execution orders."""

    eligible_features: tuple[str, ...]
    start_order: tuple[str, ...]
    stop_order: tuple[str, ...]
    blocked_features: dict[str, str]
    provider_map: dict[str, str]


class DependencyGraph:
    """Analyze feature capability dependencies deterministically."""

    def __init__(self, specs: Mapping[str, FeatureSpec]) -> None:
        self._specs = dict(specs)

    def resolve(
        self,
        enabled_feature_ids: Iterable[str],
        provider_selection: Mapping[str, str] | None = None,
    ) -> GraphResolution:
        """Calculate eligible features and deterministic execution order."""
        enabled_set = set(enabled_feature_ids)
        available_specs = {
            f_id: self._specs[f_id] for f_id in enabled_set if f_id in self._specs
        }
        blocked_features = {
            f_id: "Feature specification not found (MISSING)"
            for f_id in enabled_set
            if f_id not in self._specs
        }

        candidates, conflict_blocks = self._filter_conflicts(available_specs)
        blocked_features.update(conflict_blocks)

        provider_map = self._build_provider_map(
            candidates,
            provider_selection or {},
        )
        self._detect_required_cycles(candidates, provider_map)

        eligible_set, eligibility_blocks = self._resolve_eligibility(
            candidates,
            provider_map,
        )
        blocked_features.update(eligibility_blocks)

        start_order = self._topological_sort_required(
            eligible_set,
            candidates,
            provider_map,
        )
        start_order = self._apply_optional_startup_preferences(
            start_order,
            candidates,
            provider_map,
        )
        stop_order = tuple(reversed(start_order))

        return GraphResolution(
            eligible_features=start_order,
            start_order=start_order,
            stop_order=stop_order,
            blocked_features=blocked_features,
            provider_map={
                cap: provider
                for cap, provider in provider_map.items()
                if provider in eligible_set
            },
        )

    def _filter_conflicts(
        self,
        available_specs: Mapping[str, FeatureSpec],
    ) -> tuple[dict[str, FeatureSpec], dict[str, str]]:
        conflicted: set[str] = set()
        blocks: dict[str, str] = {}
        for f_id, spec in available_specs.items():
            for conflict_id in spec.conflicts:
                if conflict_id in available_specs and conflict_id != f_id:
                    conflicted.add(f_id)
                    blocks[f_id] = f"Conflicts with active feature '{conflict_id}'"
        return (
            {f_id: spec for f_id, spec in available_specs.items() if f_id not in conflicted},
            blocks,
        )

    def _build_provider_map(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_selection: Mapping[str, str],
    ) -> dict[str, str]:
        providers: dict[str, list[str]] = {}
        for f_id in sorted(candidates):
            for cap in candidates[f_id].provides:
                providers.setdefault(cap.identifier, []).append(f_id)

        result: dict[str, str] = {}
        for capability, feature_ids in providers.items():
            configured = provider_selection.get(capability)
            if configured is not None:
                if configured not in feature_ids:
                    msg = (
                        f"Configured provider '{configured}' does not provide enabled "
                        f"capability '{capability}'"
                    )
                    raise InvalidProviderSelectionError(msg)
                result[capability] = configured
            elif len(feature_ids) == 1:
                result[capability] = feature_ids[0]
            else:
                raise AmbiguousProviderError(capability, feature_ids)

        for capability, configured in provider_selection.items():
            if capability not in providers:
                msg = (
                    f"Configured provider '{configured}' targets unavailable capability "
                    f"'{capability}'"
                )
                raise InvalidProviderSelectionError(msg)
        return result

    def _required_edges(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> dict[str, set[str]]:
        edges: dict[str, set[str]] = {f_id: set() for f_id in candidates}
        for consumer_id, spec in candidates.items():
            for cap in spec.requires:
                provider_id = provider_map.get(cap.identifier)
                if provider_id is not None and provider_id != consumer_id:
                    edges[provider_id].add(consumer_id)
        return edges

    def _detect_required_cycles(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> None:
        edges = self._required_edges(candidates, provider_map)
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                start = stack.index(node)
                raise DependencyCycleError((*stack[start:], node))
            visiting.add(node)
            stack.append(node)
            for child in sorted(edges[node]):
                visit(child)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in sorted(edges):
            visit(node)

    def _resolve_eligibility(
        self,
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[set[str], dict[str, str]]:
        eligible: set[str] = set()
        changed = True
        while changed:
            changed = False
            for f_id in sorted(candidates):
                if f_id in eligible:
                    continue
                spec = candidates[f_id]
                missing = []
                for cap in spec.requires:
                    provider = provider_map.get(cap.identifier)
                    if provider is None or provider not in eligible:
                        missing.append(cap.identifier)
                if not missing:
                    eligible.add(f_id)
                    changed = True

        blocks: dict[str, str] = {}
        for f_id in sorted(candidates):
            if f_id in eligible:
                continue
            missing = [
                cap.identifier
                for cap in candidates[f_id].requires
                if provider_map.get(cap.identifier) not in eligible
            ]
            blocks[f_id] = (
                f"Missing required capabilities: {', '.join(missing)}"
                if missing
                else "Unsatisfied required dependencies"
            )
        return eligible, blocks

    def _topological_sort_required(
        self,
        eligible_set: set[str],
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[str, ...]:
        dependents: dict[str, set[str]] = {f_id: set() for f_id in eligible_set}
        in_degree: dict[str, int] = dict.fromkeys(eligible_set, 0)
        for consumer_id in eligible_set:
            for cap in candidates[consumer_id].requires:
                provider_id = provider_map.get(cap.identifier)
                if (
                    provider_id in eligible_set
                    and provider_id != consumer_id
                    and consumer_id not in dependents[provider_id]
                ):
                    dependents[provider_id].add(consumer_id)
                    in_degree[consumer_id] += 1

        queue = deque(sorted(f_id for f_id in eligible_set if in_degree[f_id] == 0))
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for consumer in sorted(dependents[node]):
                in_degree[consumer] -= 1
                if in_degree[consumer] == 0:
                    queue.append(consumer)

        if len(order) != len(eligible_set):
            unresolved = sorted(f_id for f_id in eligible_set if in_degree[f_id] > 0)
            raise DependencyCycleError(unresolved)
        return tuple(order)

    def _apply_optional_startup_preferences(
        self,
        required_order: tuple[str, ...],
        candidates: Mapping[str, FeatureSpec],
        provider_map: Mapping[str, str],
    ) -> tuple[str, ...]:
        """Move optional providers earlier when safe without making them dependencies."""
        order = list(required_order)
        position = {feature_id: index for index, feature_id in enumerate(order)}
        for consumer_id in tuple(order):
            for cap in candidates[consumer_id].optional:
                provider_id = provider_map.get(cap.identifier)
                if provider_id is None or provider_id == consumer_id:
                    continue
                if position[provider_id] > position[consumer_id]:
                    provider_index = order.index(provider_id)
                    order.pop(provider_index)
                    consumer_index = order.index(consumer_id)
                    order.insert(consumer_index, provider_id)
                    position = {fid: idx for idx, fid in enumerate(order)}
        return tuple(order)
