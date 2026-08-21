"""Tests for FEAT-BROKER-FEED_MOCK lifecycle mounting."""

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA, BrokerMarketData
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.broker.mock_feed.feature import MockFeedFeature, create_feature
from app.services.broker.mock_feed.manifest import SPEC


@pytest.mark.asyncio
async def test_mock_feed_feature_mount_and_provide() -> None:
    """Test MockFeedFeature mounts and provides BROKER_MARKET_DATA."""
    feature = create_feature()
    assert isinstance(feature, MockFeedFeature)
    assert feature.spec == SPEC
    assert feature.spec.feature_id == "FEAT-BROKER-FEED_MOCK"

    scope = FeatureScope(feature.spec.feature_id)
    provided: dict[str, object] = {}

    def registrar(key: object, impl: object, _sc: FeatureScope) -> None:
        if hasattr(key, "identifier"):
            provided[key.identifier] = impl

    ctx = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        provider_registrar=registrar,
    )

    await feature.mount(ctx, {"base_price": 1.0800})
    assert BROKER_MARKET_DATA.identifier in provided
    assert isinstance(provided[BROKER_MARKET_DATA.identifier], BrokerMarketData)

    await scope.close()
