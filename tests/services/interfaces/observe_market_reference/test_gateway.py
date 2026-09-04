"""Translation and lifecycle tests for the observe-market-reference feature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid7

import pytest
from app.contracts.common.models import ProblemDetails
from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import BrowseReferenceSuccess
from app.contracts.data.ports import BrowseReferenceCapability
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_REFERENCE_CAPABILITY,
)
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    ObserveMarketReferenceRequest,
    ObserveMarketReferenceSuccess,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.browse_reference.browse_reference import (
    BrowseReferenceService,
)
from app.services.data.browse_reference.config import BrowseReferenceConfig
from app.services.interfaces.observe_market_reference.config import (
    ObserveMarketReferenceConfig,
)
from app.services.interfaces.observe_market_reference.feature import (
    ObserveMarketReferenceFeature,
)
from app.services.interfaces.observe_market_reference.gateway import (
    MarketReferenceGateway,
)

if TYPE_CHECKING:
    from pathlib import Path


def _request(operation: str, **kwargs: object) -> ObserveMarketReferenceRequest:
    """Build one operation request."""
    return ObserveMarketReferenceRequest(
        request_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _context(
    feature: ObserveMarketReferenceFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_gateway_unmounted_fails_closed() -> None:
    """Verify gateway without provider returns 503 CAPABILITY_UNAVAILABLE."""
    gateway = MarketReferenceGateway(ObserveMarketReferenceConfig(), provider=None)
    res = await gateway.observe_market_reference(_request("LIST_SERIES"))
    assert isinstance(res, InterfaceFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"
    assert res.problem.status == 503
    assert "not mounted" in res.problem.detail.lower()


@pytest.mark.asyncio
async def test_gateway_closed_fails_closed() -> None:
    """Verify gateway after close returns 503 CAPABILITY_UNAVAILABLE."""
    gateway = MarketReferenceGateway(ObserveMarketReferenceConfig(), provider=None)
    await gateway.close()
    assert gateway.closed is True
    res = await gateway.observe_market_reference(_request("LIST_SERIES"))
    assert isinstance(res, InterfaceFailure)
    assert res.code == "CAPABILITY_UNAVAILABLE"
    assert res.problem.status == 503
    assert "disposed" in res.problem.detail.lower()


class _MockBrowseProvider(BrowseReferenceCapability):
    """Mock provider for testing delegation and error mapping."""

    def __init__(self, failure: DataFailure | None = None) -> None:
        self.failure = failure
        self.last_request = None

    async def browse_reference(self, request: Any) -> Any:
        self.last_request = request
        if self.failure is not None:
            return self.failure
        return BrowseReferenceSuccess(
            request_id=request.request_id,
            data={"test_key": "test_value"},
        )


@pytest.mark.asyncio
async def test_gateway_delegates_to_provider() -> None:
    """Verify gateway delegates fields to BrowseReferenceCapability."""
    mock = _MockBrowseProvider()
    gateway = MarketReferenceGateway(ObserveMarketReferenceConfig(), provider=mock)
    req = _request(
        "READ_BARS",
        symbol="EURUSD",
        timeframe="H1",
        limit=50,
    )
    res = await gateway.observe_market_reference(req)
    assert isinstance(res, ObserveMarketReferenceSuccess)
    assert res.data == {"test_key": "test_value"}
    assert mock.last_request is not None
    assert mock.last_request.operation == "READ_BARS"
    assert mock.last_request.symbol == "EURUSD"
    assert mock.last_request.timeframe == "H1"
    assert mock.last_request.limit == 50


@pytest.mark.asyncio
async def test_gateway_translates_data_failure() -> None:
    """Verify DataFailure is translated to InterfaceFailure."""
    req_id = str(uuid7())
    fail = DataFailure(
        request_id=req_id,
        code="DATA_NOT_FOUND",
        problem=ProblemDetails(
            title="Instrument Not Found",
            detail="No instrument EURUSD",
            status=404,
            code="INSTRUMENT_NOT_FOUND",
        ),
    )
    mock = _MockBrowseProvider(failure=fail)
    gateway = MarketReferenceGateway(ObserveMarketReferenceConfig(), provider=mock)
    res = await gateway.observe_market_reference(
        _request("READ_INSTRUMENT", instrument="EURUSD")
    )
    assert isinstance(res, InterfaceFailure)
    assert res.code == "INTERFACE_VALIDATION_FAILED"
    assert res.problem.status == 404
    assert res.problem.title == "Instrument Not Found"
    assert res.problem.detail == "No instrument EURUSD"
    assert res.problem.code == "INSTRUMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_feature_mount_lifecycle(tmp_path: Path) -> None:
    """Verify feature mount with optional provider and cleanup on scope close."""
    registry = ServiceRegistry()
    feature = ObserveMarketReferenceFeature()

    # Mount without provider in registry (optional dependency)
    scope_no_prov = FeatureScope(owner_id="FEAT-IFACE-OBSERVE_MARKET_REFERENCE")
    ctx_no_prov = _context(feature, registry, scope_no_prov)
    await feature.mount(ctx_no_prov, None)
    assert feature.gateway is not None
    assert registry.resolve(OBSERVE_MARKET_REFERENCE_CAPABILITY) is feature.gateway

    # Calling unmounted gateway returns 503
    gw_call = await feature.gateway.observe_market_reference(_request("LIST_SERIES"))
    assert isinstance(gw_call, InterfaceFailure)
    assert gw_call.problem.status == 503

    # Close unmounted scope
    await scope_no_prov.close()

    # Mount with provider present using fresh registry
    registry2 = ServiceRegistry()
    db_file = tmp_path / "test_gw.db"
    store = BrowseReferenceService(BrowseReferenceConfig(database_path=str(db_file)))
    store_scope = FeatureScope(owner_id="FEAT-DATA-BROWSE_REFERENCE")
    registry2.register(
        BROWSE_REFERENCE_CAPABILITY,
        store,
        owner_id="FEAT-DATA-BROWSE_REFERENCE",
        scope=store_scope,
    )

    feature2 = ObserveMarketReferenceFeature()
    scope_with_prov = FeatureScope(owner_id="FEAT-IFACE-OBSERVE_MARKET_REFERENCE-2")
    ctx_with_prov = _context(feature2, registry2, scope_with_prov)
    await feature2.mount(ctx_with_prov, None)
    assert feature2.gateway is not None

    # Calling mounted gateway succeeds
    gw_call2 = await feature2.gateway.observe_market_reference(
        _request("LIST_CAPABILITIES")
    )
    assert isinstance(gw_call2, ObserveMarketReferenceSuccess)
    assert "capabilities" in gw_call2.data  # type: ignore[operator]

    # Scope close triggers gateway close
    await scope_with_prov.close()
    assert feature2.gateway.closed is True
    store.close()
