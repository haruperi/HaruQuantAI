"""Removal-safe integration test for a provider-consumer feature pair."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, override

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBars,
    HistoricalBarsRequest,
)
from app.kernel.feature import Feature, FeatureSpec, FeatureState

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class TestMarketData(BrokerMarketData):
    """Deterministic provider independent of built-in feature packages."""

    @override
    async def retrieve_bars(
        self,
        request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=1.0,
                high_price=1.2,
                low_price=0.9,
                close_price=1.1,
                volume=100.0,
            ),
        )


class TestHistoricalBars(HistoricalBars):
    """Required consumer retaining the resolved provider object."""

    def __init__(self, provider: BrokerMarketData) -> None:
        self.provider = provider

    @override
    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        raw = await self.provider.retrieve_bars(
            BrokerBarsRequest(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
            )
        )
        return tuple(
            Bar(
                datetime=item.timestamp,
                open=item.open_price,
                high=item.high_price,
                low=item.low_price,
                close=item.close_price,
                volume=item.volume,
            )
            for item in raw
        )


class TestProviderFeature(Feature):
    """Local provider used by core composability tests."""

    spec = FeatureSpec(
        "FEAT-TEST-MARKET_DATA",
        "test",
        provides=frozenset({BROKER_MARKET_DATA}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(BROKER_MARKET_DATA, TestMarketData())


class TestConsumerFeature(Feature):
    """Local required consumer used by core composability tests."""

    spec = FeatureSpec(
        "FEAT-TEST-HISTORICAL_BARS",
        "test",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(
            HISTORICAL_BARS,
            TestHistoricalBars(context.require(BROKER_MARKET_DATA)),
        )


@pytest.mark.asyncio
async def test_vertical_pair_end_to_end_provider_loss_and_recovery() -> None:
    """Required capability loss blocks the consumer without breaking the shell."""
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(TestProviderFeature())
    discoverer.register_feature(TestConsumerFeature())
    engine = CompositionEngine(discoverer=discoverer)

    enabled = """
    [application]
    profile = "research"
    [features.FEAT-TEST-MARKET_DATA]
    enabled = true
    [features.FEAT-TEST-HISTORICAL_BARS]
    enabled = true
    """
    provider_disabled = """
    [application]
    profile = "research"
    [features.FEAT-TEST-MARKET_DATA]
    enabled = false
    [features.FEAT-TEST-HISTORICAL_BARS]
    enabled = true
    """

    await engine.load_and_reconcile_toml(enabled)
    service = engine.registry.require(HISTORICAL_BARS)
    bars = await service.retrieve(
        HistoricalBarsRequest(
            symbol="EURUSD",
            timeframe="M5",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
        )
    )
    assert len(bars) == 1

    await engine.load_and_reconcile_toml(provider_disabled)
    assert not engine.registry.is_available(BROKER_MARKET_DATA)
    assert not engine.registry.is_available(HISTORICAL_BARS)
    assert engine.reconciler.feature_states["FEAT-TEST-HISTORICAL_BARS"] == (
        FeatureState.BLOCKED
    )
    assert not engine.get_status().is_ready

    await engine.load_and_reconcile_toml(enabled)
    assert engine.registry.is_available(HISTORICAL_BARS)
    assert engine.get_status().is_ready
    await engine.shutdown()
