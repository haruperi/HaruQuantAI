"""Tests for dependency graph resolution and provider selection."""

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.capability import CapabilityKey
from app.kernel.feature import FeatureSpec
from app.kernel.graph import (
    AmbiguousProviderError,
    DependencyCycleError,
    DependencyGraph,
    InvalidProviderSelectionError,
)

CAP_RESEARCH = CapabilityKey[object](name="research.dataset", major=1)
CAP_ALPHA = CapabilityKey[object](name="research.alpha", major=1)


def test_graph_linear_dependency_resolution() -> None:
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
    resolution = DependencyGraph(specs).resolve(specs)
    assert resolution.start_order == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
        "FEAT-RESEARCH-PREPARE_DATASET",
    )
    assert resolution.stop_order == tuple(reversed(resolution.start_order))
    assert resolution.blocked_features == {}


def test_graph_missing_dependency_blocks_dependents() -> None:
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
    specs = {data_spec.feature_id: data_spec, res_spec.feature_id: res_spec}
    resolution = DependencyGraph(specs).resolve(specs)
    assert resolution.eligible_features == ()
    assert "broker.market-data@1" in resolution.blocked_features[data_spec.feature_id]
    assert res_spec.feature_id in resolution.blocked_features


def test_required_dependency_cycle_raises_error() -> None:
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
    with pytest.raises(DependencyCycleError):
        DependencyGraph(specs).resolve(specs)


def test_optional_dependency_cycle_never_blocks_activation() -> None:
    cap_a = CapabilityKey[object](name="test.a", major=1)
    cap_b = CapabilityKey[object](name="test.b", major=1)
    spec_a = FeatureSpec(
        "FEAT-TEST-A",
        "test",
        provides=frozenset({cap_a}),
        optional=frozenset({cap_b}),
    )
    spec_b = FeatureSpec(
        "FEAT-TEST-B",
        "test",
        provides=frozenset({cap_b}),
        optional=frozenset({cap_a}),
    )
    specs = {spec_a.feature_id: spec_a, spec_b.feature_id: spec_b}
    resolution = DependencyGraph(specs).resolve(specs)
    assert set(resolution.eligible_features) == set(specs)


def test_graph_optional_dependency_orders_provider_before_consumer() -> None:
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
    resolution = DependencyGraph(specs).resolve(specs)
    assert resolution.start_order.index(cache_spec.feature_id) < resolution.start_order.index(
        data_spec.feature_id
    )


def test_multiple_providers_require_explicit_selection() -> None:
    mt5 = FeatureSpec(
        "FEAT-BROKER-FEED_MT5",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )
    mock = FeatureSpec(
        "FEAT-BROKER-FEED_MOCK",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )
    data = FeatureSpec(
        "FEAT-DATA-RETRIEVE_BARS",
        "data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    specs = {spec.feature_id: spec for spec in [mt5, mock, data]}
    graph = DependencyGraph(specs)
    with pytest.raises(AmbiguousProviderError):
        graph.resolve(specs)

    resolution = graph.resolve(
        specs,
        provider_selection={"broker.market-data@1": "FEAT-BROKER-FEED_MOCK"},
    )
    assert resolution.provider_map["broker.market-data@1"] == "FEAT-BROKER-FEED_MOCK"


def test_invalid_provider_selection_fails() -> None:
    mock = FeatureSpec(
        "FEAT-BROKER-FEED_MOCK",
        "broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )
    with pytest.raises(InvalidProviderSelectionError):
        DependencyGraph({mock.feature_id: mock}).resolve(
            [mock.feature_id],
            provider_selection={"broker.market-data@1": "FEAT-BROKER-FEED_MT5"},
        )


def test_graph_conflict_detection_blocks_both_features() -> None:
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
    resolution = DependencyGraph(specs).resolve(specs)
    assert resolution.eligible_features == ()
    assert "Conflicts" in resolution.blocked_features[spec_mt5.feature_id]
