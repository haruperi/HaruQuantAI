"""Unit tests for root HaruQuantAPI facade and create_api factory."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.api.facade import HaruQuantAPI, create_api
from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBarsRequest,
)
from app.contracts.system.storage import SYSTEM_STORAGE
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.feature import FeatureSpec

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class InMemoryStorageEngine:
    """In-memory test storage engine."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    async def set(self, key: str, value: bytes) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        return key in self._data


class TestHistoricalBarsProvider:
    """Test historical bars provider implementation."""

    async def retrieve(self, _request: HistoricalBarsRequest) -> list[Bar]:
        return [
            Bar(
                datetime=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
                open=1.1,
                high=1.2,
                low=1.0,
                close=1.15,
                volume=100.0,
            )
        ]


class TestStorageFeature:
    """Test feature providing system storage."""

    spec = FeatureSpec(
        feature_id="FEAT-SYS-TEST_STORAGE",
        domain="system",
        provides=frozenset({SYSTEM_STORAGE}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        storage = InMemoryStorageEngine()
        context.provide(SYSTEM_STORAGE, storage)


class TestMockFeedFeature:
    """Test feature providing market data."""

    spec = FeatureSpec(
        feature_id="FEAT-BROKER-TEST_MOCK_FEED",
        domain="broker",
        provides=frozenset({BROKER_MARKET_DATA}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(BROKER_MARKET_DATA, object())


class TestHistoricalBarsFeature:
    """Test feature providing historical bars."""

    spec = FeatureSpec(
        feature_id="FEAT-DATA-TEST_RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        provider = TestHistoricalBarsProvider()
        context.provide(HISTORICAL_BARS, provider)


@pytest.mark.asyncio
async def test_root_haruquant_api_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full HaruQuantAPI dynamic resolution with active features."""
    storage_feat = TestStorageFeature()
    mock_feed = TestMockFeedFeature()
    hist_bars = TestHistoricalBarsFeature()

    engine = CompositionEngine()
    monkeypatch.setattr(
        FeatureDiscoverer,
        "discover",
        lambda _self: DiscoveryResult(
            discovered={
                "FEAT-SYS-TEST_STORAGE": storage_feat,
                "FEAT-BROKER-TEST_MOCK_FEED": mock_feed,
                "FEAT-DATA-TEST_RETRIEVE_BARS": hist_bars,
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
    config_toml = """
    [application]
    profile = "research"

    [features.FEAT-SYS-TEST_STORAGE]
    enabled = true

    [features.FEAT-BROKER-TEST_MOCK_FEED]
    enabled = true

    [features.FEAT-DATA-TEST_RETRIEVE_BARS]
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
        caps["data.historical-bars@1"].provider_feature_id
        == "FEAT-DATA-TEST_RETRIEVE_BARS"
    )

    # 6. Unmount features -> verify graceful capability degradation
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "research"
        [features.FEAT-DATA-TEST_RETRIEVE_BARS]
        enabled = false
        """
    )
    assert api.data.is_historical_bars_available is False
    with pytest.raises(CapabilityUnavailableError):
        await api.data.get_historical_bars(req)

    await engine.reconciler.stop_all()
