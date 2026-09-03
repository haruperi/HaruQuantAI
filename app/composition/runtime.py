"""Composition runtime activating providers and leasing capabilities."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.composition.facade import CapabilityLease
from app.kernel.effects import EffectScope
from app.kernel.errors import (
    CapabilityReasonCode,
    CapabilityUnavailable,
    CapabilityUnavailableError,
)
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.manifests import ProviderManifest
from app.kernel.resolver import ResolutionReport


class CompositionRuntime:
    """Manages active provider lifecycle and leases resolved capabilities."""

    def __init__(self) -> None:
        self._scope = EffectScope()
        self._instances: dict[CapabilityId, Any] = {}
        self._providers: dict[ProviderId | str, Any] = {}
        self._report: ResolutionReport | None = None

    def activate(
        self,
        report: ResolutionReport,
        *,
        factories: Mapping[ProviderId | str, Callable[..., Any]],
        configs: Mapping[ProviderId | str, Mapping[str, Any]],
        manifests: tuple[ProviderManifest, ...] = (),
    ) -> None:
        """Activate resolved providers using the provided factories and configs.

        Args:
            report: ResolutionReport from kernel resolver.
            factories: Mapping from provider ID to factory function.
            configs: Mapping from provider ID to config mapping.
            manifests: Optional tuple of provider manifests.
        """
        self._report = report
        factory_dict = {str(k): v for k, v in factories.items()}
        config_dict = {str(k): v for k, v in configs.items()}
        manifest_dict = {str(m.id): m for m in manifests}

        for prov_id in report.activation_order:
            prov_id_str = str(prov_id)
            factory = factory_dict.get(prov_id_str)
            if not factory:
                continue
            cfg = config_dict.get(prov_id_str, {})
            m = manifest_dict.get(prov_id_str)
            deps: dict[CapabilityId, Any] = {}
            if m:
                for req in m.requires:
                    req_cap = CapabilityId.parse(str(req.capability_id))
                    if req_cap in self._instances:
                        deps[req_cap] = self._instances[req_cap]

            instance = factory(
                dependencies=deps,
                config=cfg,
                scope=self._scope,
            )
            self._providers[prov_id] = instance
            self._providers[prov_id_str] = instance
            if m:
                for prov_cap in m.provides:
                    self._instances[CapabilityId.parse(str(prov_cap.capability_id))] = (
                        instance
                    )

        for binding in report.bindings:
            prov_inst = self._providers.get(binding.provider_id) or self._providers.get(
                str(binding.provider_id)
            )
            if prov_inst is not None:
                self._instances[binding.capability_id] = prov_inst

    def lease(self, capability_id: CapabilityId | str) -> CapabilityLease:
        """Lease an active capability instance.

        Args:
            capability_id: Target capability identifier.

        Returns:
            CapabilityLease instance.

        Raises:
            CapabilityUnavailableError: If capability is not active or available.
        """
        cap_str = str(capability_id)
        for k, v in self._instances.items():
            if str(k) == cap_str:
                return CapabilityLease(instance=v)

        CapabilityId.parse(cap_str)
        detail: Any = CapabilityUnavailable(
            code="CAPABILITY_UNAVAILABLE",
            reason_code=CapabilityReasonCode.NOT_INSTALLED,
            capability=cap_str,
            consumer=None,
            provider_id=None,
            provider_state="absent",
            profile=None,
            dependency_chain=(cap_str,),
            retryable=False,
        )
        if self._report:
            for inact in self._report.inactive:
                if str(inact.capability_id) == cap_str:
                    detail = inact.detail
                    break
        raise CapabilityUnavailableError(cast("Any", detail))

    def close(self) -> None:
        """Close the runtime and dispose all managed resources."""
        self._scope.close()
        self._instances.clear()
        self._providers.clear()
