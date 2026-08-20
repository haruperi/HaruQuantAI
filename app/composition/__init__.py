"""Spatiotemporal Provider Architecture Composition Runtime.

Traces to: Phase 6, Gate G6
"""

from __future__ import annotations

import importlib

_EXPORTS: dict[str, str] = {
    "CapabilityLease": "app.composition.generations",
    "CompositionRuntime": "app.composition.runtime",
    "ConfigurationReplacementEvidence": "app.composition.controller",
    "PinnedCapabilityGraph": "app.composition.generations",
    "ProviderConfiguration": "app.composition.reconciliation",
    "ProviderGeneration": "app.composition.generations",
    "ReconciliationResult": "app.composition.reconciliation",
    "configuration_digest": "app.composition.generations",
    "reconcile_configuration": "app.composition.reconciliation",
    "replace_provider_configuration": "app.composition.controller",
}


def __getattr__(name: str) -> object:
    """Lazily import and resolve composition exports."""
    module_path = _EXPORTS.get(name)
    if module_path is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    module = importlib.import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return all available public composition symbols."""
    return sorted(set(globals().keys()) | set(_EXPORTS.keys()))


__all__ = tuple(sorted(_EXPORTS.keys()))
