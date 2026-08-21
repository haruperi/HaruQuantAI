"""Unit tests for root HaruQuantAPI facade and create_api factory."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.api.facade import HaruQuantAPI, create_api
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.data.historical_bars import HistoricalBarsRequest
from app.kernel.capability import CapabilityUnavailableError

MockFeedFeature = pytest.importorskip(
    "app.services.broker.mock_feed.feature"
).MockFeedFeature
HistoricalBarsFeature = pytest.importorskip(
    "app.services.data.historical_bars.feature"
).HistoricalBarsFeature
StorageFeature = pytest.importorskip(
    "app.services.system.storage.feature"
).StorageFeature


@pytest.mark.asyncio
async def test_root_haruquant_api_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage_feat = StorageFeature()
    mock_feed = MockFeedFeature()
    hist_bars = HistoricalBarsFeature()
    engine = CompositionEngine()
    monkeypatch.setattr(
        FeatureDiscoverer,
        "discover",
        lambda _self: DiscoveryResult(
            discovered={
                "FEAT-SYS-PERSIST_STORAGE": storage_feat,
                "FEAT-BROKER-FEED_MOCK": mock_feed,
                "FEAT-DATA-RETRIEVE_BARS": hist_bars,
            }
        ),
    )
    api = create_api(engine=engine)
    assert isinstance(api, HaruQuantAPI)
    assert api.data.is_historical_bars_available is False

    db_file = tmp_path / "app.db"
    config_toml = f"""
    [application]
    profile = "research"
    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = true
    db_path = "{db_file.as_posix()}"
    driver = "sqlite"
    [features.FEAT-BROKER-FEED_MOCK]
    enabled = true
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = true
    """
    await engine.load_and_reconcile_toml(config_toml)
    assert api.data.is_historical_bars_available is True
    assert api.broker.is_market_data_available is True
    assert api.system.is_storage_available is True

    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="M5",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert len(await api.data.get_historical_bars(req)) > 0
    storage = api.system.get_storage_engine()
    await storage.set("last_sync", b"2026-08-21")
    assert await storage.get("last_sync") == b"2026-08-21"

    caps = api.system.list_capabilities()
    assert caps["data.historical-bars@1"].provider_feature_id == "FEAT-DATA-RETRIEVE_BARS"

    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "research"
        [features.FEAT-DATA-RETRIEVE_BARS]
        enabled = false
        """
    )
    assert api.data.is_historical_bars_available is False
    with pytest.raises(CapabilityUnavailableError):
        await api.data.get_historical_bars(req)
    await engine.shutdown()
