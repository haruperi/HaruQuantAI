"""Unit evidence for the validated in-process composition graph."""

import pytest
from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    get_required_in_process_provider_names,
)


def _providers() -> dict[str, object]:
    """Build complete inert provider values for composition validation."""
    return {
        name: lambda *args, **kwargs: (args, kwargs)
        for name in get_required_in_process_provider_names()
    }


def test_provider_manifest_is_exact_and_deterministic() -> None:
    """Expose one stable provider manifest without duplicate route bindings."""
    names = get_required_in_process_provider_names()
    assert names == (
        "agentic.source",
        "dashboard.source",
        "data.dataset_source",
        "operator.audit_source",
        "operator.event_source",
        "optimization.source",
        "portfolio.source",
        "risk.command_source",
        "risk.source",
        "simulation.live_source",
        "simulation.result_source",
        "simulation.run_source",
        "simulation.session_source",
        "strategy.mutation_source",
        "trading.mutation_source",
        "trading.session_source",
    )
    assert len(set(names)) == len(names)
    assert names == tuple(sorted(names))


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
