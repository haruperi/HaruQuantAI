"""Spatiotemporal Provider Architecture Microkernel.

Traces to: Phase 4, Phase 5, Gate G4, Gate G5
"""

from __future__ import annotations

import importlib

_EXPORTS: dict[str, str] = {
    "CapabilityId": "app.kernel.identifiers",
    "ProviderId": "app.kernel.identifiers",
    "SemanticVersion": "app.kernel.identifiers",
    "RuntimeProfile": "app.kernel.profiles",
    "Cardinality": "app.kernel.manifests",
    "DowngradePolicy": "app.kernel.manifests",
    "EffectClass": "app.kernel.manifests",
    "LifecyclePolicy": "app.kernel.manifests",
    "OnMissing": "app.kernel.manifests",
    "ProvidedCapability": "app.kernel.manifests",
    "ProviderManifest": "app.kernel.manifests",
    "ReloadPolicy": "app.kernel.manifests",
    "RequiredCapability": "app.kernel.manifests",
    "load_manifest": "app.kernel.manifests",
    "DiscoveredProvider": "app.kernel.discovery",
    "discover_manifests": "app.kernel.discovery",
    "ProviderInventory": "app.kernel.registry",
    "build_inventory": "app.kernel.registry",
    "InactiveCapability": "app.kernel.resolver",
    "ResolutionReport": "app.kernel.resolver",
    "ResolvedBinding": "app.kernel.resolver",
    "resolve_providers": "app.kernel.resolver",
    "ComponentState": "app.kernel.states",
    "transition_component": "app.kernel.states",
    "KernelHealth": "app.kernel.health",
    "ProfileReadiness": "app.kernel.health",
    "evaluate_kernel_health": "app.kernel.health",
    "evaluate_profile_readiness": "app.kernel.health",
    "project_diagnostics": "app.kernel.diagnostics",
    "EffectScope": "app.kernel.effects",
    "AsyncEffectScopeAdapter": "app.kernel.async_effects",
    "ActiveComponent": "app.kernel.lifecycle",
    "ProviderFactory": "app.kernel.lifecycle",
    "activate_component": "app.kernel.lifecycle",
    "deactivate_component": "app.kernel.lifecycle",
    "CapabilityReasonCode": "app.kernel.errors",
    "CapabilityUnavailable": "app.kernel.errors",
    "CapabilityUnavailableError": "app.kernel.errors",
    "KernelError": "app.kernel.errors",
    "LifecycleError": "app.kernel.errors",
    "ManifestValidationError": "app.kernel.errors",
    "ResolutionError": "app.kernel.errors",
    "capability_unavailable_payload": "app.kernel.errors",
}


def __getattr__(name: str) -> object:
    """Lazily import and resolve kernel exports."""
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return all available public kernel symbols."""
    return sorted(set(globals().keys()) | set(_EXPORTS.keys()))


__all__ = tuple(sorted(_EXPORTS.keys()))
