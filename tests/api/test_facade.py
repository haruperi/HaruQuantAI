"""Unit tests for root HaruQuantAPI facade and create_api factory."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.api.facade import HaruQuantAPI, create_api
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.data.historical_bars import HistoricalBarsRequest
from app.kernel.capability import CapabilityUnavailableError
from app.services.broker.mock_feed.feature import MockFeedFeature
from app.services.data.historical_bars.feature import HistoricalBarsFeature
from app.services.system.storage.feature import StorageFeature


@pytest.mark.asyncio
async def test_root_haruquant_api_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test full HaruQuantAPI dynamic resolution with active features."""
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
    assert api.engine is engine

    # Initially no features mounted
    assert api.data.is_historical_bars_available is False
    assert api.broker.is_market_data_available is False
    assert api.system.is_storage_available is False

    # 1. Mount features
    db_file = tmp_path / "app.db"
    config_toml = f"""
    [profile]
    name = "research"

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

    # 2. Check capabilities are now live through facade
    assert api.data.is_historical_bars_available is True
    assert api.broker.is_market_data_available is True
    assert api.system.is_storage_available is True

    # 3. Call DataAPI
    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="M5",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    bars = await api.data.get_historical_bars(req)
    assert len(bars) > 0

    # 4. Call Storage through SystemAPI
    storage = api.system.get_storage_engine()
    await storage.set("last_sync", b"2026-08-21")
    assert await storage.get("last_sync") == b"2026-08-21"

    # 5. Check capability introspection
    caps = api.system.list_capabilities()
    assert "data.historical-bars@1" in caps
    assert (
        caps["data.historical-bars@1"].provider_feature_id == "FEAT-DATA-RETRIEVE_BARS"
    )

    # 6. Unmount features -> verify graceful capability degradation
    await engine.load_and_reconcile_toml(
        """
        [profile]
        name = "research"
        [features.FEAT-DATA-RETRIEVE_BARS]
        enabled = false
        """
    )
    assert api.data.is_historical_bars_available is False
    with pytest.raises(CapabilityUnavailableError):
        await api.data.get_historical_bars(req)

    await engine.reconciler.stop_all()
