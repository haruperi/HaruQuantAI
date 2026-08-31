"""Tests for DependencyGraph topological sorting, cycle detection, and eligibility."""

import pytest
from app.kernel.capability import CapabilityKey
from app.kernel.feature import FeatureSpec
from app.kernel.graph import (
    AmbiguousProviderError,
    DependencyCycleError,
    DependencyGraph,
    ProviderSelectionError,
)

from tests._support.composability import (
    CONSUMER_CAPABILITY,
    OPTIONAL_CAPABILITY,
    PROVIDER_CAPABILITY,
    ROOT_CAPABILITY,
)

CAP_RESEARCH = CapabilityKey[object](name="research.dataset", major=1)
CAP_ALPHA = CapabilityKey[object](name="research.alpha", major=1)


def test_graph_linear_dependency_resolution() -> None:
    """Test linear dependency chain start and stop order."""
    clock_spec = FeatureSpec(
        "FEAT-TEST-PROVIDE_ROOT", "system", provides=frozenset({ROOT_CAPABILITY})
    )
    broker_spec = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
        requires=frozenset({ROOT_CAPABILITY}),
    )
    data_spec = FeatureSpec(
        "FEAT-TEST-CONSUME_SERVICE",
        "data",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )
    res_spec = FeatureSpec(
        "FEAT-TEST-CONSUME_CHAIN",
        "research",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({CONSUMER_CAPABILITY}),
    )

    specs = {s.feature_id: s for s in [clock_spec, broker_spec, data_spec, res_spec]}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.start_order == (
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
        "FEAT-TEST-CONSUME_CHAIN",
    )
    assert resolution.stop_order == (
        "FEAT-TEST-CONSUME_CHAIN",
        "FEAT-TEST-CONSUME_SERVICE",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-PROVIDE_ROOT",
    )
    assert len(resolution.blocked_features) == 0

    # Test transitive closures
    clock_dependents = resolution.get_transitive_dependents("FEAT-TEST-PROVIDE_ROOT")
    assert clock_dependents == {
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
        "FEAT-TEST-CONSUME_CHAIN",
    }

    dataset_dependencies = resolution.get_transitive_dependencies(
        "FEAT-TEST-CONSUME_CHAIN"
    )
    assert dataset_dependencies == {
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
    }


def test_graph_missing_dependency_blocks_dependents() -> None:
    """Test missing provider leaves consumer in blocked_features."""
    data_spec = FeatureSpec(
        "FEAT-TEST-CONSUME_SERVICE",
        "data",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )
    res_spec = FeatureSpec(
        "FEAT-TEST-CONSUME_CHAIN",
        "research",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({CONSUMER_CAPABILITY}),
    )

    # Note: PROVIDER_CAPABILITY provider is NOT enabled/provided
    specs = {data_spec.feature_id: data_spec, res_spec.feature_id: res_spec}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.eligible_features == ()
    assert resolution.start_order == ()
    assert "FEAT-TEST-CONSUME_SERVICE" in resolution.blocked_features
    assert "FEAT-TEST-CONSUME_CHAIN" in resolution.blocked_features
    assert "test.provider@1" in resolution.blocked_features["FEAT-TEST-CONSUME_SERVICE"]


def test_graph_cycle_detection_raises_error() -> None:
    """Test cyclic required dependencies raise DependencyCycleError."""
    spec_a = FeatureSpec(
        "FEAT-TEST-CONSUME_ALPHA",
        "test",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({CAP_ALPHA}),
    )
    spec_b = FeatureSpec(
        "FEAT-TEST-PRODUCE_ALPHA",
        "test",
        provides=frozenset({CAP_ALPHA}),
        requires=frozenset({CAP_RESEARCH}),
    )

    specs = {spec_a.feature_id: spec_a, spec_b.feature_id: spec_b}
    graph = DependencyGraph(specs)

    with pytest.raises(DependencyCycleError, match=r"(?i)circular required dependency"):
        graph.resolve(specs.keys())


def test_graph_optional_dependency_ordering() -> None:
    """Test optional dependency respects topological order when provider is enabled."""
    cache_spec = FeatureSpec(
        "FEAT-TEST-PROVIDE_OPTIONAL", "data", provides=frozenset({OPTIONAL_CAPABILITY})
    )
    data_spec = FeatureSpec(
        "FEAT-TEST-CONSUME_SERVICE",
        "data",
        provides=frozenset({CONSUMER_CAPABILITY}),
        optional=frozenset({OPTIONAL_CAPABILITY}),
    )

    specs = {cache_spec.feature_id: cache_spec, data_spec.feature_id: data_spec}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.start_order == (
        "FEAT-TEST-PROVIDE_OPTIONAL",
        "FEAT-TEST-CONSUME_SERVICE",
    )


def test_graph_conflict_detection() -> None:
    """Test feature conflicts block activation."""
    spec_mt5 = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
        conflicts=frozenset({"FEAT-TEST-PROVIDE_ALTERNATE"}),
    )
    spec_binance = FeatureSpec(
        "FEAT-TEST-PROVIDE_ALTERNATE",
        "test",
        provides=frozenset({PROVIDER_CAPABILITY}),
        conflicts=frozenset({"FEAT-TEST-PROVIDE_SERVICE"}),
    )

    specs = {spec_mt5.feature_id: spec_mt5, spec_binance.feature_id: spec_binance}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.eligible_features == ()
    assert "FEAT-TEST-PROVIDE_SERVICE" in resolution.blocked_features
    assert "FEAT-TEST-PROVIDE_ALTERNATE" in resolution.blocked_features
    assert "Conflicts" in resolution.blocked_features["FEAT-TEST-PROVIDE_SERVICE"]


def test_ambiguous_providers_rejected_without_selection() -> None:
    """Test two enabled providers for one capability without explicit selection raises AmbiguousProviderError."""
    spec_prov_a = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )
    spec_prov_b = FeatureSpec(
        "FEAT-TEST-PROVIDE_ALTERNATE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    specs = {
        spec_prov_a.feature_id: spec_prov_a,
        spec_prov_b.feature_id: spec_prov_b,
    }
    graph = DependencyGraph(specs)

    with pytest.raises(
        AmbiguousProviderError, match=r"(?i)ambiguous.*test\.provider@1"
    ):
        graph.resolve(specs.keys())


def test_explicit_selection_resolves_ambiguous_providers() -> None:
    """Test providing explicit selection in provider_selections resolves ambiguity."""
    spec_prov_a = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )
    spec_prov_b = FeatureSpec(
        "FEAT-TEST-PROVIDE_ALTERNATE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    specs = {
        spec_prov_a.feature_id: spec_prov_a,
        spec_prov_b.feature_id: spec_prov_b,
    }
    graph = DependencyGraph(specs)
    resolution = graph.resolve(
        specs.keys(),
        provider_selections={"test.provider@1": "FEAT-TEST-PROVIDE_ALTERNATE"},
    )

    assert resolution.provider_map["test.provider@1"] == "FEAT-TEST-PROVIDE_ALTERNATE"
    assert "FEAT-TEST-PROVIDE_ALTERNATE" in resolution.eligible_features


def test_invalid_provider_selection_raises_error() -> None:
    """Test selecting a non-existent or disabled feature raises ProviderSelectionError."""
    spec_prov_a = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )
    spec_prov_b = FeatureSpec(
        "FEAT-TEST-PROVIDE_ALTERNATE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    specs = {
        spec_prov_a.feature_id: spec_prov_a,
        spec_prov_b.feature_id: spec_prov_b,
    }
    graph = DependencyGraph(specs)

    with pytest.raises(
        ProviderSelectionError, match=r"(?i)not among enabled candidate"
    ):
        graph.resolve(
            specs.keys(),
            provider_selections={"test.provider@1": "FEAT-NONEXISTENT"},
        )


def test_selection_of_feature_not_providing_capability_raises_error() -> None:
    """Test selecting a feature that does not provide the capability raises ProviderSelectionError."""
    clock_spec = FeatureSpec(
        "FEAT-TEST-PROVIDE_ROOT",
        "system",
        provides=frozenset({ROOT_CAPABILITY}),
    )
    broker_spec = FeatureSpec(
        "FEAT-TEST-PROVIDE_SERVICE",
        "broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    specs = {clock_spec.feature_id: clock_spec, broker_spec.feature_id: broker_spec}
    graph = DependencyGraph(specs)

    with pytest.raises(
        ProviderSelectionError, match=r"(?i)does not provide capability"
    ):
        graph.resolve(
            specs.keys(),
            provider_selections={"test.provider@1": "FEAT-TEST-PROVIDE_ROOT"},
        )


def test_required_dependency_cycle_raises_explicit_error() -> None:
    """Characterization test: circular required dependencies must explicitly raise an error rather than silently blocking."""
    spec_a = FeatureSpec(
        "FEAT-TEST-CONSUME_ALPHA",
        "test",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({CAP_ALPHA}),
    )
    spec_b = FeatureSpec(
        "FEAT-TEST-PRODUCE_ALPHA",
        "test",
        provides=frozenset({CAP_ALPHA}),
        requires=frozenset({CAP_RESEARCH}),
    )

    specs = {spec_a.feature_id: spec_a, spec_b.feature_id: spec_b}
    graph = DependencyGraph(specs)

    with pytest.raises(DependencyCycleError, match=r"(?i)circular required dependency"):
        graph.resolve(specs.keys())
