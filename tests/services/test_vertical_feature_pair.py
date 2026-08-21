"""Integration test verifying vertical feature pair end-to-end and deletion behavior."""

from datetime import UTC, datetime

import pytest

from app.composition.engine import CompositionEngine
from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    HistoricalBars,
    HistoricalBarsRequest,
)
from app.kernel.feature import FeatureState

MockFeedFeature = pytest.importorskip(
    "app.services.broker.mock_feed.feature"
).MockFeedFeature
HistoricalBarsFeature = pytest.importorskip(
    "app.services.data.historical_bars.feature"
).HistoricalBarsFeature

TOML_ALL_ENABLED = """
[application]
profile = "research"
[features."FEAT-BROKER-FEED_MOCK"]
enabled = true
[features."FEAT-DATA-RETRIEVE_BARS"]
enabled = true
"""

TOML_BROKER_DISABLED = """
[application]
profile = "research"
[features."FEAT-BROKER-FEED_MOCK"]
enabled = false
[features."FEAT-DATA-RETRIEVE_BARS"]
enabled = true
"""


@pytest.mark.asyncio
async def test_vertical_pair_end_to_end_and_graceful_loss() -> None:
    engine = CompositionEngine()
    engine.discoverer.register_feature(MockFeedFeature())
    engine.discoverer.register_feature(HistoricalBarsFeature())

    report1 = await engine.load_and_reconcile_toml(TOML_ALL_ENABLED)
    assert report1.started == ("FEAT-BROKER-FEED_MOCK", "FEAT-DATA-RETRIEVE_BARS")
    assert engine.registry.is_available(BROKER_MARKET_DATA)
    assert engine.registry.is_available(HISTORICAL_BARS)

    service = engine.registry.require(HISTORICAL_BARS)
    assert isinstance(service, HistoricalBars)
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 15, tzinfo=UTC)
    bars = await service.retrieve(
        HistoricalBarsRequest(symbol="EURUSD", timeframe="M5", start=start, end=end)
    )
    assert len(bars) == 3

    report2 = await engine.load_and_reconcile_toml(TOML_BROKER_DISABLED)
    assert "FEAT-DATA-RETRIEVE_BARS" in report2.stopped
    assert "FEAT-BROKER-FEED_MOCK" in report2.stopped
    assert not engine.registry.is_available(BROKER_MARKET_DATA)
    assert not engine.registry.is_available(HISTORICAL_BARS)
    assert (
        engine.reconciler.feature_states["FEAT-DATA-RETRIEVE_BARS"]
        == FeatureState.BLOCKED
    )
    assert not engine.get_status().is_ready

    report3 = await engine.load_and_reconcile_toml(TOML_ALL_ENABLED)
    assert "FEAT-BROKER-FEED_MOCK" in report3.started
    assert "FEAT-DATA-RETRIEVE_BARS" in report3.started
    assert engine.get_status().is_ready
    await engine.shutdown()
