"""Unit tests for the trading operations gateway."""

from pathlib import Path
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


@pytest.mark.asyncio
async def test_manage_execution_sessions_fails_closed_when_unmounted() -> None:
    """Verify manage_execution_sessions returns CAPABILITY_UNAVAILABLE when provider is absent."""
    gateway = TradingGateway(config=OperateTradingConfig())
    req_id = str(uuid7())
    from app.contracts.trading.models import ManageExecutionSessionsRequest

    request = ManageExecutionSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=str(uuid7()),
        operation="LIST_SESSIONS",
    )
    result = await gateway.manage_execution_sessions(request)
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"
    assert result.problem.status == 503
    assert result.request_id == req_id


@pytest.mark.asyncio
async def test_manage_execution_sessions_fails_closed_when_closed() -> None:
    """Verify manage_execution_sessions returns CAPABILITY_UNAVAILABLE after close."""
    gateway = TradingGateway(config=OperateTradingConfig())
    await gateway.close()
    req_id = str(uuid7())
    from app.contracts.trading.models import ManageExecutionSessionsRequest

    request = ManageExecutionSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=str(uuid7()),
        operation="LIST_SESSIONS",
    )
    result = await gateway.manage_execution_sessions(request)
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"
    assert result.problem.status == 503


@pytest.mark.asyncio
async def test_manage_execution_sessions_delegates(tmp_path: object) -> None:
    """Verify delegation to active upstream provider and error mapping."""
    from app.contracts.trading.models import (
        ManageExecutionSessionsRequest,
        ManageExecutionSessionsSuccess,
    )
    from app.services.trading.manage_execution_sessions.config import (
        ManageExecutionSessionsConfig,
    )
    from app.services.trading.manage_execution_sessions.execution_sessions import (
        ExecutionSessionsService,
    )

    db_path = Path(str(tmp_path)) / "gateway_test.db"
    upstream = ExecutionSessionsService(
        ManageExecutionSessionsConfig(database_path=db_path)
    )
    gateway = TradingGateway(
        config=OperateTradingConfig(),
        execution_sessions=upstream,
    )

    req_id = str(uuid7())
    request = ManageExecutionSessionsRequest(
        request_id=req_id,
        capability_snapshot_id=str(uuid7()),
        operation="LIST_SESSIONS",
    )
    result = await gateway.manage_execution_sessions(request)
    assert isinstance(result, ManageExecutionSessionsSuccess)
    assert len(result.sessions) >= 1

    # Verify error mapping from upstream TradingFailure
    err_request = ManageExecutionSessionsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="STOP_SESSION",
        session_id="non-existent",
    )
    err_result = await gateway.manage_execution_sessions(err_request)
    assert isinstance(err_result, InterfaceFailure)
    assert err_result.problem.status == 404
    assert err_result.problem.code == "SESSION_NOT_FOUND"

    upstream.close()
