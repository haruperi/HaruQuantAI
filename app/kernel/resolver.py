"""Deterministic provider resolution and dependency graph computation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.manifests import ProviderManifest
from app.kernel.profiles import CapabilityUnavailable


@dataclass(frozen=True, slots=True)
class ResolvedBinding:
    """Active binding of a capability to a provider."""

    capability_id: CapabilityId
    provider_id: ProviderId
    provider_version: SemanticVersion


@dataclass(frozen=True, slots=True)
class InactiveCapability:
    """Inactive capability descriptor."""

    capability_id: CapabilityId
    detail: CapabilityUnavailable


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    """Immutable resolution outcome."""

    bindings: tuple[ResolvedBinding, ...]
    inactive: tuple[InactiveCapability, ...]
    activation_order: tuple[ProviderId, ...]
    deactivation_order: tuple[ProviderId, ...]


def resolve_providers(
    manifests: tuple[ProviderManifest, ...],
    *,
    enabled_provider_ids: frozenset[ProviderId]
    | set[ProviderId]
    | tuple[ProviderId, ...],
    selected_provider_ids: Mapping[CapabilityId, ProviderId] | None = None,
) -> ResolutionReport:
    """Resolve enabled manifests into bindings and activation order.

    Args:
        manifests: Tuple of all available ProviderManifest records.
        enabled_provider_ids: Set of enabled provider identifiers.
        selected_provider_ids: Optional manual capability -> provider mappings.

    Returns:
        ResolutionReport with bindings, inactive items, and order.
    """
    _selected = dict(selected_provider_ids or {})
    enabled_set = {str(pid) for pid in enabled_provider_ids}

    # Map available provided capabilities to providers
    available_manifests = [
        m
        for m in sorted(manifests, key=lambda x: str(x.id))
        if str(m.id) in enabled_set
    ]
    provided_map: dict[str, ProviderManifest] = {}
    for m in available_manifests:
        for p in m.provides:
            provided_map[str(p.capability_id)] = m

    active_manifests: list[ProviderManifest] = []
    inactive: list[InactiveCapability] = []

    # Filter manifests whose required dependencies are fully satisfied
    changed = True
    candidates = list(available_manifests)
    while changed:
        changed = False
        remaining: list[ProviderManifest] = []
        for m in candidates:
            missing_reqs = [
                str(r.capability_id)
                for r in m.requires
                if not r.optional and str(r.capability_id) not in provided_map
            ]
            if missing_reqs:
                changed = True
                # Remove capabilities this manifest provides
                for p in m.provides:
                    provided_map.pop(str(p.capability_id), None)
                    inactive.append(
                        InactiveCapability(
                            capability_id=CapabilityId.parse(str(p.capability_id)),
                            detail=CapabilityUnavailable(
                                code="CAPABILITY_UNAVAILABLE",
                                reason_code="DEPENDENCY_UNAVAILABLE",
                                capability=str(p.capability_id),
                                consumer=str(m.id),
                                provider_id=str(m.id),
                                dependency_chain=(str(m.id), missing_reqs[0]),
                            ),
                        )
                    )
                for missing in missing_reqs:
                    inactive.append(
                        InactiveCapability(
                            capability_id=CapabilityId.parse(missing),
                            detail=CapabilityUnavailable(
                                code="CAPABILITY_UNAVAILABLE",
                                reason_code="NOT_INSTALLED",
                                capability=missing,
                                consumer=str(m.id),
                            ),
                        )
                    )
            else:
                remaining.append(m)
        candidates = remaining

    active_manifests = candidates

    # Topological sort of active_manifests
    # Build graph: m -> list of providers it depends on
    prov_by_id = {str(m.id): m for m in active_manifests}
    dep_graph: dict[str, set[str]] = {str(m.id): set() for m in active_manifests}
    for m in active_manifests:
        for r in m.requires:
            cap_str = str(r.capability_id)
            if cap_str in provided_map:
                supplying_m = provided_map[cap_str]
                if (
                    str(supplying_m.id) != str(m.id)
                    and str(supplying_m.id) in prov_by_id
                ):
                    dep_graph[str(m.id)].add(str(supplying_m.id))

    # Kahn's algorithm
    activation_order_ids: list[ProviderId] = []
    visited: set[str] = set()
    while len(visited) < len(active_manifests):
        ready = [
            pid
            for pid, deps in sorted(dep_graph.items())
            if pid not in visited and deps.issubset(visited)
        ]
        if not ready:
            # Fallback if cycle
            break
        for pid in ready:
            visited.add(pid)
            activation_order_ids.append(ProviderId.parse(pid))

    bindings: list[ResolvedBinding] = []
    for m in active_manifests:
        prov_id = ProviderId.parse(str(m.id))
        ver_str = str(m.version) if hasattr(m, "version") and m.version else "1.0.0"
        try:
            sem_ver = SemanticVersion.parse(ver_str)
        except Exception:
            sem_ver = SemanticVersion(1, 0, 0)

        for p in m.provides:
            cap_id = CapabilityId.parse(str(p.capability_id))
            bindings.append(
                ResolvedBinding(
                    capability_id=cap_id,
                    provider_id=prov_id,
                    provider_version=sem_ver,
                )
            )

    bindings.sort(key=lambda b: (str(b.capability_id), str(b.provider_id)))
    act_order = tuple(activation_order_ids)
    deact_order = tuple(reversed(activation_order_ids))

    return ResolutionReport(
        bindings=tuple(bindings),
        inactive=tuple(inactive),
        activation_order=act_order,
        deactivation_order=deact_order,
    )
