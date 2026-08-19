"""Unit evidence for the validated in-process composition graph."""

import pytest
from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    get_required_in_process_provider_names,
)
from app.services.api.composition.adapters import get_route_dependency_bindings
from app.services.api.composition.capabilities import (
    get_capability_id,
    get_optional_capability_ids,
)

# Capabilities that must always compose; absence fails closed per AGENTS.md.
_REQUIRED_CAPABILITIES = frozenset(
    {
        # Analytics is required: `simulator` imports it, so it can never be absent.
        "analytics",
        "dashboard",
        "data",
        "operator",
        "risk",
        "simulation",
        "simulator",
        "strategy",
        "trading",
    }
)


def _providers() -> dict[str, object]:
    """Build complete inert provider values for composition validation."""
    return {
        name: lambda *args, **kwargs: (args, kwargs)
        for name in get_required_in_process_provider_names()
    }


def test_provider_manifest_is_consistent_and_deterministic() -> None:
    """Expose one deterministic manifest covering every required capability."""
    names = get_required_in_process_provider_names()
    assert len(set(names)) == len(names)
    assert names == tuple(sorted(names))
    assert all(name == name.strip() and "." in name for name in names)
    capabilities = {get_capability_id(name) for name in names}
    # Required capabilities must always compose; optional ones may be absent.
    assert capabilities >= _REQUIRED_CAPABILITIES
    assert capabilities - _REQUIRED_CAPABILITIES <= get_optional_capability_ids()
    bindings = get_route_dependency_bindings()
    assert set(names) == set(bindings)
    assert all(callable(binding) for binding in bindings.values())


def test_graph_rejects_missing_unknown_and_invalid_values() -> None:
    """Reject incomplete or speculative owner dependencies before startup."""
    providers = _providers()
    missing = dict(providers)
    missing.pop("operator.event_source")
    with pytest.raises(ValueError, match="missing in-process providers"):
        build_in_process_api_graph(missing)

    unknown = {**providers, "unknown.provider": object}
    with pytest.raises(ValueError, match="unknown in-process providers"):
        build_in_process_api_graph(unknown)

    invalid = {**providers, "operator.event_source": object()}
    with pytest.raises(TypeError, match="provider must be callable"):
        build_in_process_api_graph(invalid)

    with pytest.raises(TypeError, match="closers must be callable"):
        build_in_process_api_graph(
            providers,
            owned_resource_closers=(object(),),  # type: ignore[arg-type]
        )


def test_graph_cannot_mix_with_legacy_dependency_overrides() -> None:
    """Keep one canonical composition mechanism per application."""
    graph = build_in_process_api_graph(_providers())

    def dependency() -> object:
        """Return one legacy dependency value."""
        return object()

    with pytest.raises(ValueError, match="cannot be supplied together"):
        create_api_app(
            build_api_settings(),
            in_process_graph=graph,
            dependency_overrides={dependency: dependency},
        )
