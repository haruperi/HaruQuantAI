"""Unit tests for the trading operations gateway."""

from uuid import uuid7

import pytest
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateTradingEventSubscription,
    OperateTradingRequest,
)
from app.contracts.trading.models import TradingSessionRef
from app.services.interfaces.operate_trading.config import OperateTradingConfig
from app.services.interfaces.operate_trading.gateway import TradingGateway


@pytest.mark.asyncio
async def test_gateway_fails_closed_when_upstream_absent() -> None:
    """Verify operations return CAPABILITY_UNAVAILABLE when upstream provider is absent."""
    gateway = TradingGateway(config=OperateTradingConfig())
    req_id = str(uuid7())
    request = OperateTradingRequest(
        request_id=req_id,
        capability_snapshot_id=str(uuid7()),
        operation="READINESS",
        session_ref=TradingSessionRef(session_id=str(uuid7()), mode="PAPER"),
    )
    result = await gateway.operate_trading(request)
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"
    assert result.request_id == req_id


@pytest.mark.asyncio
async def test_gateway_fails_closed_when_closed() -> None:
    """Verify operations return CAPABILITY_UNAVAILABLE after close."""
    gateway = TradingGateway(config=OperateTradingConfig())
    await gateway.close()
    assert gateway.closed is True

    req_id = str(uuid7())
    request = OperateTradingRequest(
        request_id=req_id,
        capability_snapshot_id=str(uuid7()),
        operation="READINESS",
        session_ref=TradingSessionRef(session_id=str(uuid7()), mode="PAPER"),
    )
    result = await gateway.operate_trading(request)
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_event_subscription_empty_when_no_publisher() -> None:
    """Verify event subscription yields nothing when upstream is absent."""
    gateway = TradingGateway(config=OperateTradingConfig())
    sub = OperateTradingEventSubscription(
        session_ref=str(uuid7()),
        replay_limit=10,
    )
    events = [event async for event in gateway.subscribe_operate_trading_events(sub)]
    assert len(events) == 0
