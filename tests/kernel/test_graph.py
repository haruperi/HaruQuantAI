"""Tests for DependencyGraph topological sorting, cycle detection, and eligibility."""

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.capability import CapabilityKey
from app.kernel.feature import FeatureSpec
from app.kernel.graph import DependencyGraph

CAP_RESEARCH = CapabilityKey[object](name="research.dataset", major=1)
CAP_ALPHA = CapabilityKey[object](name="research.alpha", major=1)


def test_graph_linear_dependency_resolution() -> None:
    """Test linear dependency chain start and stop order."""
    clock_spec = FeatureSpec(
        "FEAT-SYS-PROVIDE_CLOCK", "system", provides=frozenset({SYSTEM_CLOCK})
    )
    broker_spec = FeatureSpec(
        "FEAT-BROKER-FEED_MT5",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
        requires=frozenset({SYSTEM_CLOCK}),
    )
    data_spec = FeatureSpec(
        "FEAT-DATA-RETRIEVE_BARS",
        "data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    res_spec = FeatureSpec(
        "FEAT-RESEARCH-PREPARE_DATASET",
        "research",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({HISTORICAL_BARS}),
    )

    specs = {s.feature_id: s for s in [clock_spec, broker_spec, data_spec, res_spec]}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.start_order == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
        "FEAT-RESEARCH-PREPARE_DATASET",
    )
    assert resolution.stop_order == (
        "FEAT-RESEARCH-PREPARE_DATASET",
        "FEAT-DATA-RETRIEVE_BARS",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-SYS-PROVIDE_CLOCK",
    )
    assert len(resolution.blocked_features) == 0


def test_graph_missing_dependency_blocks_dependents() -> None:
    """Test missing provider leaves consumer in blocked_features."""
    data_spec = FeatureSpec(
        "FEAT-DATA-RETRIEVE_BARS",
        "data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    res_spec = FeatureSpec(
        "FEAT-RESEARCH-PREPARE_DATASET",
        "research",
        provides=frozenset({CAP_RESEARCH}),
        requires=frozenset({HISTORICAL_BARS}),
    )

    # Note: BROKER_MARKET_DATA provider is NOT enabled/provided
    specs = {data_spec.feature_id: data_spec, res_spec.feature_id: res_spec}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.eligible_features == ()
    assert resolution.start_order == ()
    assert "FEAT-DATA-RETRIEVE_BARS" in resolution.blocked_features
    assert "FEAT-RESEARCH-PREPARE_DATASET" in resolution.blocked_features
    assert (
        "broker.market-data@1" in resolution.blocked_features["FEAT-DATA-RETRIEVE_BARS"]
    )


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

    # In fixed-point iteration, neither satisfies requirements because of mutual dependency
    resolution = graph.resolve(specs.keys())
    assert resolution.eligible_features == ()
    assert "FEAT-TEST-CONSUME_ALPHA" in resolution.blocked_features
    assert "FEAT-TEST-PRODUCE_ALPHA" in resolution.blocked_features


def test_graph_optional_dependency_ordering() -> None:
    """Test optional dependency respects topological order when provider is enabled."""
    cache_spec = FeatureSpec(
        "FEAT-DATA-CACHE_BARS", "data", provides=frozenset({BAR_CACHE})
    )
    data_spec = FeatureSpec(
        "FEAT-DATA-RETRIEVE_BARS",
        "data",
        provides=frozenset({HISTORICAL_BARS}),
        optional=frozenset({BAR_CACHE}),
    )

    specs = {cache_spec.feature_id: cache_spec, data_spec.feature_id: data_spec}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.start_order == (
        "FEAT-DATA-CACHE_BARS",
        "FEAT-DATA-RETRIEVE_BARS",
    )


def test_graph_conflict_detection() -> None:
    """Test feature conflicts block activation."""
    spec_mt5 = FeatureSpec(
        "FEAT-BROKER-FEED_MT5",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
        conflicts=frozenset({"FEAT-BROKER-FEED_BINANCE"}),
    )
    spec_binance = FeatureSpec(
        "FEAT-BROKER-FEED_BINANCE",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
        conflicts=frozenset({"FEAT-BROKER-FEED_MT5"}),
    )

    specs = {spec_mt5.feature_id: spec_mt5, spec_binance.feature_id: spec_binance}
    graph = DependencyGraph(specs)
    resolution = graph.resolve(specs.keys())

    assert resolution.eligible_features == ()
    assert "FEAT-BROKER-FEED_MT5" in resolution.blocked_features
    assert "FEAT-BROKER-FEED_BINANCE" in resolution.blocked_features
    assert "Conflicts" in resolution.blocked_features["FEAT-BROKER-FEED_MT5"]


def test_ambiguous_providers_rejected_without_selection() -> None:
    """Characterization test: two enabled providers for one capability without explicit selection must fail or raise ambiguity."""
    spec_prov_a = FeatureSpec(
        "FEAT-BROKER-FEED_MT5",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )
    spec_prov_b = FeatureSpec(
        "FEAT-BROKER-FEED_CTRADER",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )

    specs = {
        spec_prov_a.feature_id: spec_prov_a,
        spec_prov_b.feature_id: spec_prov_b,
    }
    graph = DependencyGraph(specs)

    # Without explicit provider selection, graph resolution must fail or reject ambiguity
    with pytest.raises(
        (ValueError, RuntimeError), match=r"(?i)ambiguous|multiple providers|selection"
    ):
        graph.resolve(specs.keys())


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

    with pytest.raises((ValueError, RuntimeError), match=r"(?i)cycle|circular"):
        graph.resolve(specs.keys())
