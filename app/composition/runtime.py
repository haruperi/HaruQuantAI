"""Composition runtime for atomic generational activation, injection, and leasing.

Traces to: P6-T02, Gate G6
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.composition.generations import (
    CapabilityLease,
    PinnedCapabilityGraph,
    ProviderGeneration,
    configuration_digest,
)
from app.kernel.effects import EffectScope
from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    CapabilityUnavailableError,
    LifecycleError,
)
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.lifecycle import (
    ActiveComponent,
    ProviderFactory,
    activate_component,
    deactivate_component,
)
from app.kernel.manifests import ProviderManifest
from app.utils.logging import get_logger

_logger = get_logger("app.composition.runtime")

if TYPE_CHECKING:
    from app.kernel.resolver import ResolutionReport


class CompositionRuntime:
    """Thread-safe generational composition runtime managing active provider graphs."""

    def __init__(self) -> None:
        """Initialize empty CompositionRuntime."""
        self._lock = threading.RLock()
        self._active_components: dict[ProviderId, ActiveComponent] = {}
        self._generations: dict[ProviderId, ProviderGeneration] = {}
        self._leases: dict[CapabilityId, CapabilityLease[object]] = {}

    def activate(
        self,
        report: ResolutionReport,
        *,
        factories: Mapping[ProviderId, ProviderFactory],
        configs: Mapping[ProviderId, Mapping[str, object]],
        manifests: Mapping[ProviderId, ProviderManifest]
        | Sequence[ProviderManifest]
        | None = None,
    ) -> tuple[ProviderGeneration, ...]:
        """Activate resolved providers in topological order with injected dependencies.

        Args:
            report: Resolution report with topological activation order.
            factories: Mapping of ProviderId to ProviderFactory callable.
            configs: Mapping of ProviderId to provider configuration dictionaries.
            manifests: Optional mapping or sequence of provider manifests.

        Returns:
            Tuple of activated ProviderGeneration records.

        Raises:
            LifecycleError: If a required factory is missing or component activation fails.
        """
        # 1. Validate all required factories are present
        for pid in report.activation_order:
            if pid not in factories:
                msg = f"missing provider factory: {pid}"
                raise LifecycleError(msg)

        # Build lookup for provided capabilities per provider
        manifest_map: dict[ProviderId, ProviderManifest] = {}
        if manifests is not None:
            if isinstance(manifests, Mapping):
                manifest_map = dict(manifests)
            else:
                manifest_map = {m.provider_id: m for m in manifests}

        manifest_by_provider: dict[ProviderId, ProviderManifest] = {}
        caps_by_provider: dict[ProviderId, list[CapabilityId]] = {}
        for b in report.bindings:
            manifest_by_provider[b.provider_id] = manifest_map.get(
                b.provider_id,
                ProviderManifest(
                    provider_id=b.provider_id,
                    provider_version=b.provider_version,
                    entry_point="",
                    config_schema=None,
                    provides=(),
                    requires=(),
                    optional_requires=(),
                    profiles=(),
                    scopes=(),
                    effect_classes=(),
                    lifecycle=None,  # type: ignore[arg-type]
                    reload=None,  # type: ignore[arg-type]
                    state_schema_id=None,
                    state_schema_version=None,
                    migration_manifest=None,
                    compatible_state_majors=(),
                    uninstall_retention=None,
                    purge_requires_authorization=False,
                ),
            )
            caps_by_provider.setdefault(b.provider_id, []).append(b.capability_id)

        for pid in report.activation_order:
            if pid not in manifest_by_provider:
                manifest_by_provider[pid] = manifest_map.get(
                    pid,
                    ProviderManifest(
                        provider_id=pid,
                        provider_version=SemanticVersion.parse("1.0.0"),
                        entry_point="",
                        config_schema=None,
                        provides=(),
                        requires=(),
                        optional_requires=(),
                        profiles=(),
                        scopes=(),
                        effect_classes=(),
                        lifecycle=None,  # type: ignore[arg-type]
                        reload=None,  # type: ignore[arg-type]
                        state_schema_id=None,
                        state_schema_version=None,
                        migration_manifest=None,
                        compatible_state_majors=(),
                        uninstall_retention=None,
                        purge_requires_authorization=False,
                    ),
                )

        candidate_components: list[ActiveComponent] = []
        candidate_generations: dict[ProviderId, ProviderGeneration] = {}
        candidate_leases: dict[CapabilityId, CapabilityLease[object]] = {}
        activated_instances: dict[CapabilityId, object] = {}
        provider_gen_ids: dict[ProviderId, UUID] = {}

        try:
            for pid in report.activation_order:
                _logger.info("Activating provider generation %s", pid)

                manifest = manifest_by_provider[pid]

                # Collect declared dependencies
                deps: dict[CapabilityId, object] = {}
                dep_gen_ids: list[UUID] = []
                if manifests is not None and pid in manifest_map:
                    needed_caps = {req.capability_id for req in manifest.requires} | {
                        req.capability_id for req in manifest.optional_requires
                    }
                    for cap_id in sorted(needed_caps, key=str):
                        if cap_id in candidate_leases:
                            lease = candidate_leases[cap_id]
                            deps[cap_id] = lease.instance
                            if lease.generation_id not in dep_gen_ids:
                                dep_gen_ids.append(lease.generation_id)
                else:
                    for cap_id, lease in candidate_leases.items():
                        deps[cap_id] = lease.instance
                        if lease.generation_id not in dep_gen_ids:
                            dep_gen_ids.append(lease.generation_id)
                conf = configs.get(pid, {})
                scope = EffectScope()

                active_comp = activate_component(
                    manifest=manifest,
                    factory=factories[pid],
                    dependencies=deps,
                    config=conf,
                    scope=scope,
                )
                candidate_components.append(active_comp)
                provider_gen_ids[pid] = active_comp.generation_id

                # Bind leases for this provider's capabilities
                for cap_id in caps_by_provider.get(pid, ()):
                    candidate_leases[cap_id] = CapabilityLease(
                        capability_id=cap_id,
                        generation_id=active_comp.generation_id,
                        instance=active_comp.instance,
                    )
                    activated_instances[cap_id] = active_comp.instance

                gen_record = ProviderGeneration(
                    provider_id=pid,
                    generation_id=active_comp.generation_id,
                    version=manifest.provider_version,
                    config_digest=configuration_digest(conf),
                    dependency_generation_ids=tuple(dep_gen_ids),
                    activated_at=datetime.now(UTC),
                )
                candidate_generations[pid] = gen_record

        except Exception:
            # Candidate activation failed; unwind candidate in reverse order
            while candidate_components:
                comp = candidate_components.pop()
                with contextlib.suppress(Exception):
                    deactivate_component(comp, timeout_seconds=5.0)
            raise

        # Atomic commit of active graph
        with self._lock:
            old_components = list(self._active_components.values())
            self._active_components = {c.provider_id: c for c in candidate_components}
            self._generations = candidate_generations
            self._leases = candidate_leases

        # Teardown superseded components in reverse order
        while old_components:
            old_comp = old_components.pop()
            _logger.info("Deactivating provider generation %s", old_comp.provider_id)
            with contextlib.suppress(Exception):
                deactivate_component(old_comp, timeout_seconds=10.0)

        return tuple(candidate_generations.values())

    def lease(self, capability_id: CapabilityId) -> CapabilityLease[object]:
        """Acquire a direct typed capability lease.

        Args:
            capability_id: Target capability ID.

        Returns:
            Active CapabilityLease instance.

        Raises:
            CapabilityUnavailableError: If capability is not installed or active.
        """
        with self._lock:
            lease = self._leases.get(capability_id)
            if lease is not None:
                return lease

        detail = CapabilityUnavailable(
            code="CAPABILITY_UNAVAILABLE",
            reason_code=CapabilityReasonCode.NOT_INSTALLED,
            capability=str(capability_id),
            consumer=None,
            provider_id=None,
            provider_state="NOT_INSTALLED",
            profile=None,
            dependency_chain=(str(capability_id),),
            retryable=False,
        )
        raise CapabilityUnavailableError(detail)

    def deactivate_all(self, *, timeout_seconds: float = 30.0) -> None:
        """Deactivate all active components in reverse order.

        Args:
            timeout_seconds: Timeout for component deactivation.
        """
        with self._lock:
            comps = list(self._active_components.values())
            self._active_components.clear()
            self._generations.clear()
            self._leases.clear()

        while comps:
            c = comps.pop()
            _logger.info("Deactivating provider generation %s", c.provider_id)
            deactivate_component(c, timeout_seconds=timeout_seconds)

    def pin_graph(self) -> PinnedCapabilityGraph:
        """Capture an immutable snapshot of active provider generations and capability leases.

        Returns:
            Immutable PinnedCapabilityGraph instance.
        """
        with self._lock:
            return PinnedCapabilityGraph(
                generations=dict(self._generations),
                leases=dict(self._leases),
            )


__all__ = ("CompositionRuntime",)
