"""Deterministic provider dependency graph resolution and cycle detection.

Traces to: P4-T05, Gate G4
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    ResolutionError,
)
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.manifests import (
    Cardinality,
    OnMissing,
    ProvidedCapability,
    ProviderManifest,
)


@dataclass(frozen=True, slots=True)
class ResolvedBinding:
    """Binding of a capability ID to a specific provider and its version."""

    capability_id: CapabilityId
    provider_id: ProviderId
    provider_version: SemanticVersion


@dataclass(frozen=True, slots=True)
class InactiveCapability:
    """Record of an inactive capability and the reason detail."""

    capability_id: CapabilityId
    detail: CapabilityUnavailable


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    """Complete immutable resolution report of bindings, inactive items, and activation order."""

    bindings: tuple[ResolvedBinding, ...]
    inactive: tuple[InactiveCapability, ...]
    activation_order: tuple[ProviderId, ...]
    deactivation_order: tuple[ProviderId, ...]


def resolve_providers(
    manifests: tuple[ProviderManifest, ...],
    *,
    enabled_provider_ids: frozenset[ProviderId],
    selected_provider_ids: Mapping[CapabilityId, ProviderId],
) -> ResolutionReport:
    """Resolve enabled provider manifests into bindings and deterministic lifecycle order.

    Args:
        manifests: Full inventory of available provider manifests.
        enabled_provider_ids: Set of explicitly enabled provider IDs.
        selected_provider_ids: Map of explicit capability-to-provider selections.

    Returns:
        Immutable ResolutionReport.

    Raises:
        ResolutionError: If a hard dependency cycle or unresolvable ambiguity is encountered.
    """
    manifest_by_id = {m.provider_id: m for m in manifests}

    # 1. Map capabilities to providing manifests
    enabled_by_cap: dict[
        CapabilityId, list[tuple[ProviderManifest, ProvidedCapability]]
    ] = {}
    disabled_by_cap: dict[
        CapabilityId, list[tuple[ProviderManifest, ProvidedCapability]]
    ] = {}

    all_caps: set[CapabilityId] = set()

    for m in manifests:
        for p in m.provides:
            all_caps.add(p.capability_id)
            if m.provider_id in enabled_provider_ids:
                enabled_by_cap.setdefault(p.capability_id, []).append((m, p))
            else:
                disabled_by_cap.setdefault(p.capability_id, []).append((m, p))
        for r in list(m.requires) + list(m.optional_requires):
            all_caps.add(r.capability_id)

    # 2. Determine initial binding or unavailability per capability
    resolved_bindings: list[ResolvedBinding] = []
    inactive_map: dict[CapabilityId, CapabilityUnavailable] = {}
    bound_provider_map: dict[CapabilityId, list[ProviderManifest]] = {}

    for cap_id in sorted(all_caps):
        enabled_provs = enabled_by_cap.get(cap_id, [])
        if not enabled_provs:
            if cap_id in disabled_by_cap:
                disabled_prov = disabled_by_cap[cap_id][0][0]
                inactive_map[cap_id] = CapabilityUnavailable(
                    code="CAPABILITY_UNAVAILABLE",
                    reason_code=CapabilityReasonCode.DISABLED,
                    capability=str(cap_id),
                    consumer=None,
                    provider_id=str(disabled_prov.provider_id),
                    provider_state="DISABLED",
                    profile=None,
                    dependency_chain=(str(cap_id),),
                    retryable=False,
                )
            else:
                inactive_map[cap_id] = CapabilityUnavailable(
                    code="CAPABILITY_UNAVAILABLE",
                    reason_code=CapabilityReasonCode.NOT_INSTALLED,
                    capability=str(cap_id),
                    consumer=None,
                    provider_id=None,
                    provider_state="NOT_INSTALLED",
                    profile=None,
                    dependency_chain=(str(cap_id),),
                    retryable=False,
                )
            continue

        if len(enabled_provs) == 1:
            m, p = enabled_provs[0]
            resolved_bindings.append(
                ResolvedBinding(
                    capability_id=cap_id,
                    provider_id=m.provider_id,
                    provider_version=m.provider_version,
                )
            )
            bound_provider_map[cap_id] = [m]
        # Multiple enabled candidates
        elif cap_id in selected_provider_ids:
            selected_pid = selected_provider_ids[cap_id]
            match = [m for m, p in enabled_provs if m.provider_id == selected_pid]
            if match:
                m = match[0]
                resolved_bindings.append(
                    ResolvedBinding(
                        capability_id=cap_id,
                        provider_id=m.provider_id,
                        provider_version=m.provider_version,
                    )
                )
                bound_provider_map[cap_id] = [m]
            else:
                inactive_map[cap_id] = CapabilityUnavailable(
                    code="CAPABILITY_UNAVAILABLE",
                    reason_code=CapabilityReasonCode.PROVIDER_AMBIGUOUS,
                    capability=str(cap_id),
                    consumer=None,
                    provider_id=None,
                    provider_state="AMBIGUOUS",
                    profile=None,
                    dependency_chain=(str(cap_id),),
                    retryable=False,
                )
        elif enabled_provs[0][1].cardinality == Cardinality.MANY:
            # Cardinality MANY binds all enabled providers
            for m, _p in enabled_provs:
                resolved_bindings.append(
                    ResolvedBinding(
                        capability_id=cap_id,
                        provider_id=m.provider_id,
                        provider_version=m.provider_version,
                    )
                )
            bound_provider_map[cap_id] = [m for m, p in enabled_provs]
        else:
            inactive_map[cap_id] = CapabilityUnavailable(
                code="CAPABILITY_UNAVAILABLE",
                reason_code=CapabilityReasonCode.PROVIDER_AMBIGUOUS,
                capability=str(cap_id),
                consumer=None,
                provider_id=None,
                provider_state="AMBIGUOUS",
                profile=None,
                dependency_chain=(str(cap_id),),
                retryable=False,
            )

    # 3. Check requirement dependencies and evaluate missing policies
    active_providers: set[ProviderId] = {
        m.provider_id for m in manifests if m.provider_id in enabled_provider_ids
    }
    dep_graph: dict[ProviderId, set[ProviderId]] = {
        pid: set() for pid in active_providers
    }

    changed = True
    while changed:
        changed = False
        for pid in sorted(active_providers):
            m = manifest_by_id[pid]
            for req in list(m.requires) + list(m.optional_requires):
                req_cap = req.capability_id
                # Check version compatibility
                if req_cap in bound_provider_map:
                    for bound_m in bound_provider_map[req_cap]:
                        if bound_m.provider_id not in active_providers:
                            # Dependency provider was deactivated
                            continue
                        if bound_m.provider_version.major not in req.supported_majors:
                            inactive_map[req_cap] = CapabilityUnavailable(
                                code="CAPABILITY_UNAVAILABLE",
                                reason_code=CapabilityReasonCode.VERSION_INCOMPATIBLE,
                                capability=str(req_cap),
                                consumer=str(pid),
                                provider_id=str(bound_m.provider_id),
                                provider_state="VERSION_INCOMPATIBLE",
                                profile=None,
                                dependency_chain=(str(pid), str(req_cap)),
                                retryable=False,
                            )
                            if req in m.requires and req.on_missing in (
                                OnMissing.FAIL_CLOSED,
                                OnMissing.SKIP,
                            ):
                                active_providers.remove(pid)
                                changed = True
                                break
                        else:
                            dep_graph[pid].add(bound_m.provider_id)
                elif req in m.requires and req.on_missing in (
                    OnMissing.FAIL_CLOSED,
                    OnMissing.SKIP,
                ):
                    active_providers.remove(pid)
                    changed = True
                    break

    # 4. Clean resolved bindings for deactivated providers
    final_bindings = [b for b in resolved_bindings if b.provider_id in active_providers]
    final_bindings.sort(key=lambda b: (str(b.capability_id), str(b.provider_id)))

    # 5. Build inactive capability tuples
    final_inactive = [
        InactiveCapability(capability_id=cap_id, detail=detail)
        for cap_id, detail in sorted(inactive_map.items(), key=lambda x: str(x[0]))
    ]

    # 6. Cycle detection & Topological Sort on active_providers
    active_dep_graph = {
        pid: {d for d in dep_graph[pid] if d in active_providers}
        for pid in active_providers
    }

    # Tarjan / DFS cycle detection
    visited: set[ProviderId] = set()
    rec_stack: list[ProviderId] = []

    def _dfs_cycle(node: ProviderId) -> None:
        visited.add(node)
        rec_stack.append(node)
        for neighbor in sorted(active_dep_graph.get(node, set()), key=str):
            if neighbor not in visited:
                _dfs_cycle(neighbor)
            elif neighbor in rec_stack:
                cycle_start = rec_stack.index(neighbor)
                cycle = [*rec_stack[cycle_start:], neighbor]
                cycle_str = " -> ".join(str(p) for p in cycle)
                msg = f"hard dependency cycle: {cycle_str}"
                raise ResolutionError(msg)
        rec_stack.pop()

    for pid in sorted(active_providers, key=str):
        if pid not in visited:
            _dfs_cycle(pid)

    # Topological sort (Kahn's algorithm with deterministic tie-breaking)
    in_degree = dict.fromkeys(active_providers, 0)
    reverse_deps: dict[ProviderId, set[ProviderId]] = {
        pid: set() for pid in active_providers
    }

    for u, targets in active_dep_graph.items():
        for v in targets:
            # u depends on v, so v must activate before u
            in_degree[u] += 1
            reverse_deps[v].add(u)

    ready = [pid for pid in sorted(active_providers, key=str) if in_degree[pid] == 0]
    activation_order: list[ProviderId] = []

    while ready:
        ready.sort(key=str)
        curr = ready.pop(0)
        activation_order.append(curr)
        for dependent in sorted(reverse_deps[curr], key=str):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready.append(dependent)

    deactivation_order = tuple(reversed(activation_order))

    return ResolutionReport(
        bindings=tuple(final_bindings),
        inactive=tuple(final_inactive),
        activation_order=tuple(activation_order),
        deactivation_order=deactivation_order,
    )


__all__ = (
    "InactiveCapability",
    "ResolutionReport",
    "ResolvedBinding",
    "resolve_providers",
)
