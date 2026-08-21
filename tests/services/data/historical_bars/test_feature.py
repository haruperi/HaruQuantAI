"""Tests for FEAT-DATA-RETRIEVE_BARS feature composition and lifecycle mounting."""

from collections.abc import Sequence
from typing import override

import pytest

from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.contracts.data.historical_bars import HISTORICAL_BARS, HistoricalBars
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.data.historical_bars.feature import (
    HistoricalBarsFeature,
    create_feature,
)
from app.services.data.historical_bars.manifest import SPEC


class DummyBrokerMarketData(BrokerMarketData):
    """Test double implementing BrokerMarketData protocol."""

    @override
    async def retrieve_bars(self, request: BrokerBarsRequest) -> Sequence[BrokerRawBar]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=1.1000,
                high_price=1.1050,
                low_price=1.0990,
                close_price=1.1020,
                volume=100.0,
            ),
        )


@pytest.mark.asyncio
async def test_historical_bars_feature_mount_success() -> None:
    """Test mounting HistoricalBarsFeature when BROKER_MARKET_DATA is available."""
    feature = create_feature()
    assert isinstance(feature, HistoricalBarsFeature)
    assert feature.spec == SPEC
    assert feature.spec.feature_id == "FEAT-DATA-RETRIEVE_BARS"

    scope = FeatureScope(feature.spec.feature_id)
    provided: dict[str, object] = {}
    broker_service = DummyBrokerMarketData()

    def registrar(key: object, impl: object, _sc: FeatureScope) -> None:
        if hasattr(key, "identifier"):
            provided[key.identifier] = impl

    def resolver(key: object) -> object | None:
        if (
            hasattr(key, "identifier")
            and key.identifier == BROKER_MARKET_DATA.identifier
        ):
            return broker_service
        return None

    ctx = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=resolver,
        provider_registrar=registrar,
    )

    await feature.mount(ctx, {"default_timeframe": "M5"})
    assert HISTORICAL_BARS.identifier in provided
    assert isinstance(provided[HISTORICAL_BARS.identifier], HistoricalBars)

    await scope.close()


@pytest.mark.asyncio
async def test_historical_bars_feature_mount_missing_dependency_raises() -> None:
    """Test mounting raises CapabilityUnavailableError when broker dependency is missing."""
    feature = create_feature()
    scope = FeatureScope(feature.spec.feature_id)

    ctx = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=lambda _key: None,
    )

    with pytest.raises(CapabilityUnavailableError):
        await feature.mount(ctx, {})

    await scope.close()
