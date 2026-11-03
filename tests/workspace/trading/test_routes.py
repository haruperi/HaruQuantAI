"""Tests for Live Trading REST endpoints and WebSocket streaming.

Description:
    Verify declared strategy behavior and explicit rejection of unavailable inputs.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Regression evidence for shared strategy execution.
Key Capabilities:
    - FR-hsl-regression-evidence: Assert observable results and failure boundaries.
Python API Usage:
    Run this module through pytest.
CLI Usage:
    uv run pytest tests/workspace/trading --no-cov
"""

from __future__ import annotations

from typing import override

import pytest
from app.core.enums import AccountTradeMode, OrderType, TradeAction, TradeRetcode
from app.core.trading.connection.base import TradingClient
from app.core.trading.connection.contracts import (
    AccountInfo,
    OrderInfo,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.main import create_app
from app.workspace.trading.brokers.registry import default_broker_registry
from fastapi.testclient import TestClient


class MockRouteClient(TradingClient):
    """Mock client registered for route testing."""

    def __init__(self, name: str = "MockRouteClient") -> None:
        super().__init__(name)
        self.connect()
        self.arm()
        self._positions: list[PositionInfo] = [
            PositionInfo(ticket=1001, symbol="EURUSD", volume=1.0, position_type=0)
        ]
        self._orders: list[OrderInfo] = [
            OrderInfo(ticket=2001, symbol="EURUSD", volume_initial=0.5)
        ]
        self._account = AccountInfo(
            login=99999,
            trade_mode=AccountTradeMode.DEMO,
            balance=100000.0,
            equity=100000.0,
            margin=0.0,
            free_margin=100000.0,
            currency="USD",
            server="Mock-Server",
        )

    @override
    def get_account_info(self) -> AccountInfo:
        return self._account

    @override
    def get_positions(self) -> list[PositionInfo]:
        return list(self._positions)

    @override
    def get_orders(self) -> list[OrderInfo]:
        return list(self._orders)

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        if request.action == TradeAction.DEAL and request.position:
            self._positions = [
                p for p in self._positions if p.ticket != request.position
            ]
            return TradeResult(retcode=int(TradeRetcode.DONE), deal=request.position)
        if request.action == TradeAction.REMOVE:
            self._orders = [o for o in self._orders if o.ticket != request.order]
            return TradeResult(retcode=int(TradeRetcode.DONE), order=request.order)

        ticket = len(self._positions) + 5001
        self._positions.append(
            PositionInfo(
                ticket=ticket,
                symbol=request.symbol,
                volume=request.volume,
                position_type=0 if request.order_type == OrderType.BUY else 1,
            )
        )
        return TradeResult(retcode=int(TradeRetcode.DONE), order=ticket)


@pytest.fixture
def client_app() -> TestClient:
    default_broker_registry.close_all()
    mock_client = MockRouteClient()
    default_broker_registry.register("test-conn", mock_client)
    app = create_app()
    return TestClient(app)


def test_routes_accounts_positions_orders(client_app: TestClient) -> None:
    # Accounts
    res_acc = client_app.get("/api/v1/trading/accounts")
    assert res_acc.status_code == 200
    accounts = res_acc.json()
    assert len(accounts) == 1
    assert accounts[0]["connection_id"] == "test-conn"
    assert accounts[0]["balance"] == 100000.0

    # Positions
    res_pos = client_app.get("/api/v1/trading/positions")
    assert res_pos.status_code == 200
    positions = res_pos.json()
    assert len(positions) == 1
    assert positions[0]["ticket"] == 1001

    # Orders
    res_ord = client_app.get("/api/v1/trading/orders")
    assert res_ord.status_code == 200
    orders = res_ord.json()
    assert len(orders) == 1
    assert orders[0]["ticket"] == 2001


def test_routes_market_order_and_close(client_app: TestClient) -> None:
    # Error for missing connection
    bad_req = {
        "connection_id": "nonexistent",
        "symbol": "EURUSD",
        "volume": 0.5,
        "order_type": "BUY",
    }
    assert (
        client_app.post("/api/v1/trading/orders/market", json=bad_req).status_code
        == 404
    )

    # Valid market order
    good_req = {
        "connection_id": "test-conn",
        "symbol": "EURUSD",
        "volume": 0.5,
        "order_type": "BUY",
    }
    res_market = client_app.post("/api/v1/trading/orders/market", json=good_req)
    assert res_market.status_code == 200
    assert res_market.json()["retcode"] == int(TradeRetcode.DONE)

    # Close position
    close_req = {
        "connection_id": "test-conn",
        "ticket": 1001,
        "symbol": "EURUSD",
    }
    res_close = client_app.post("/api/v1/trading/orders/close", json=close_req)
    assert res_close.status_code == 200
    assert res_close.json()["retcode"] == int(TradeRetcode.DONE)


def test_routes_emergency_panic_endpoints(client_app: TestClient) -> None:
    # Flatten all
    res_flat = client_app.post(
        "/api/v1/trading/emergency/flatten",
        json={"connection_id": "test-conn"},
    )
    assert res_flat.status_code == 200
    assert res_flat.json()["status"] == "success"

    # Cancel all
    res_cancel = client_app.post(
        "/api/v1/trading/emergency/cancel-all",
        json={"connection_id": "test-conn"},
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "success"


def test_routes_strategy_deploy_and_control(client_app: TestClient) -> None:
    deploy_req = {
        "strategy_id": "strat-live-1",
        "symbol": "EURUSD",
        "connection_id": "test-conn",
        "timeframe": "PERIOD_H1",
        "document": {"strategy": {"id": "strat-live-1", "name": "Live test"}},
    }
    res_deploy = client_app.post("/api/v1/trading/strategies/deploy", json=deploy_req)
    assert res_deploy.status_code == 200
    data = res_deploy.json()
    session_id = data["session_id"]
    assert data["status"] == "RUNNING"

    # Pause
    res_pause = client_app.post(f"/api/v1/trading/strategies/{session_id}/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "PAUSED"

    # Resume
    res_resume = client_app.post(f"/api/v1/trading/strategies/{session_id}/resume")
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "RUNNING"

    # List
    res_list = client_app.get("/api/v1/trading/strategies")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Stop
    res_stop = client_app.post(f"/api/v1/trading/strategies/{session_id}/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "STOPPED"


def test_routes_websocket_streaming(client_app: TestClient) -> None:
    with client_app.websocket_connect("/api/v1/trading/stream") as ws:
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"
