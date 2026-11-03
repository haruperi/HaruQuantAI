"""Live trading REST endpoints and real-time streaming WebSocket routes.

Description:
    Provides FastAPI router with REST endpoints for querying accounts, open positions,
    working orders, submitting manual market orders, triggering emergency panic flatten,
    deploying live strategies, and streaming market updates over a WebSocket connection.
Purpose:
    FEAT-LIVE-ROUTES: Live trading HTTP and WebSocket API.
Key Capabilities:
    - FR-trading-routes-accounts: Aggregate active broker accounts and balances.
    - FR-trading-routes-positions: Query and close live market positions.
    - FR-trading-routes-orders: Query and submit market and pending orders.
    - FR-trading-routes-panic: Trigger emergency flatten and cancel operations.
    - FR-trading-routes-stream: Stream real-time events over WebSocket.
Python API Usage:
    from app.workspace.trading.routes import trading_router
    app.include_router(trading_router)
CLI Usage:
    uv run python -m pytest tests/workspace/trading/test_routes.py -q
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.core.data.contracts import (
    OrderInfo,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.core.enums import (
    OrderType,
    Timeframe,
    TradeAction,
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.core.trading.connection.base import TradingClient
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.workspace.trading.brokers.registry import default_broker_registry
from app.workspace.trading.risk_guard import RiskGuard
from app.workspace.trading.supervisor import (
    LiveStrategySupervisor,
    StrategyDeploySpec,
)

logger = get_logger(__name__)

trading_router = APIRouter(prefix="/api/v1/trading", tags=["trading"])

# Module-level singletons for route handling
_registry = default_broker_registry
_risk_guard = RiskGuard()
_supervisor = LiveStrategySupervisor(
    broker_registry=_registry,
    risk_guard=_risk_guard,
)
_active_websockets: list[WebSocket] = []
_ws_lock = asyncio.Lock()


# Request Models
class MarketOrderRequest(BaseModel):
    """Payload for manual market order submission."""

    connection_id: str = Field(description="Target broker connection ID")
    symbol: str = Field(description="Instrument symbol")
    volume: float = Field(gt=0, description="Order volume in lots")
    order_type: str = Field(default="BUY", description="BUY or SELL")
    price: float = Field(default=0.0, description="Execution price")
    sl: float | None = Field(default=None, description="Stop loss price")
    tp: float | None = Field(default=None, description="Take profit price")
    comment: str = Field(default="manual order", description="Order comment")


class ClosePositionRequest(BaseModel):
    """Payload to close an open position."""

    connection_id: str = Field(description="Target broker connection ID")
    ticket: int = Field(description="Position ticket to close")
    symbol: str = Field(default="", description="Position symbol")
    volume: float | None = Field(default=None, description="Volume to close")


class EmergencyActionRequest(BaseModel):
    """Payload for emergency panic actions."""

    connection_id: str | None = Field(
        default=None,
        description="Optional connection ID, or None for all",
    )


class DeployStrategyRequest(BaseModel):
    """Payload to deploy a strategy to live execution."""

    strategy_id: str = Field(description="Strategy ID")
    symbol: str = Field(description="Symbol to trade")
    connection_id: str = Field(description="Broker connection ID")
    timeframe: str = Field(default="H1", description="Timeframe")
    document: HSLStrategyDocument | None = None
    allow_order_submission: bool = False


async def broadcast_ws(event_type: str, data: dict[str, Any]) -> None:
    """Broadcast an event payload to all connected WebSocket clients."""
    msg = {"type": event_type, "data": data}
    async with _ws_lock:
        to_remove: list[WebSocket] = []
        for ws in _active_websockets:
            try:
                await ws.send_json(msg)
            except Exception:  # noqa: BLE001
                to_remove.append(ws)
        for ws in to_remove:
            if ws in _active_websockets:
                _active_websockets.remove(ws)


@trading_router.get("/accounts")
async def get_accounts() -> list[dict[str, Any]]:
    """List active broker accounts and live balances."""
    logger.info("FR-trading-routes-accounts: listing active broker accounts")
    accounts: list[dict[str, Any]] = []
    for cid, client in _registry.list_active():
        if isinstance(client, TradingClient):
            raw = client.get_account_info()
            info = await raw if inspect.isawaitable(raw) else raw
            accounts.append(
                {
                    "connection_id": cid,
                    "broker": client.name,
                    "connected": client.is_connected,
                    "login": info.login,
                    "balance": info.balance,
                    "equity": info.equity,
                    "margin": info.margin,
                    "free_margin": info.free_margin,
                    "currency": info.currency,
                    "server": info.server,
                }
            )
    return accounts


@trading_router.get("/positions")
async def get_positions() -> list[dict[str, Any]]:
    """List open positions across all connected broker clients."""
    logger.debug("FR-trading-routes-positions: querying aggregate positions")
    positions: list[dict[str, Any]] = []
    for cid, client in _registry.list_active():
        if isinstance(client, TradingClient) and client.is_connected:
            raw = client.get_positions()
            pos_list: list[PositionInfo] = (
                await raw if inspect.isawaitable(raw) else raw
            )
            for pos in pos_list:
                d = asdict(pos)
                d["connection_id"] = cid
                positions.append(d)
    return positions


@trading_router.get("/orders")
async def get_orders() -> list[dict[str, Any]]:
    """List working pending orders across all connected broker clients."""
    logger.debug("FR-trading-routes-orders: querying aggregate orders")
    orders: list[dict[str, Any]] = []
    for cid, client in _registry.list_active():
        if isinstance(client, TradingClient) and client.is_connected:
            raw = client.get_orders()
            order_list: list[OrderInfo] = await raw if inspect.isawaitable(raw) else raw
            for order in order_list:
                d = asdict(order)
                d["connection_id"] = cid
                orders.append(d)
    return orders


@trading_router.post("/orders/market")
async def submit_market_order(req: MarketOrderRequest) -> dict[str, Any]:
    """Submit a manual market order."""
    logger.info(
        "FR-trading-routes-orders: market order %s on %s vol=%.2f",
        req.symbol,
        req.connection_id,
        req.volume,
    )
    client = _registry.get_trading_client(req.connection_id)
    if client is None or not client.is_connected:
        raise HTTPException(
            status_code=404,
            detail=f"Connection {req.connection_id} not available",
        )

    order_type = OrderType.BUY if req.order_type.upper() == "BUY" else OrderType.SELL
    trade_req = TradeRequest(
        action=TradeAction.DEAL,
        symbol=req.symbol,
        volume=req.volume,
        order_type=order_type,
        price=req.price,
        sl=req.sl or 0.0,
        tp=req.tp or 0.0,
        comment=req.comment,
    )

    try:
        raw_res = client.order_send(trade_req)
        res: TradeResult = await raw_res if inspect.isawaitable(raw_res) else raw_res
        result_dict = asdict(res)
        await broadcast_ws("order_execution", result_dict)
        return result_dict
    except Exception as exc:
        logger.exception("FR-trading-routes-execution: order error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@trading_router.post("/orders/close")
async def close_position(req: ClosePositionRequest) -> dict[str, Any]:
    """Close an open position by ticket."""
    logger.info(
        "FR-trading-routes-positions: closing ticket %d on %s",
        req.ticket,
        req.connection_id,
    )
    client = _registry.get_trading_client(req.connection_id)
    if client is None or not client.is_connected:
        raise HTTPException(
            status_code=404,
            detail=f"Connection {req.connection_id} not available",
        )

    trade_req = TradeRequest(
        action=TradeAction.DEAL,
        symbol=req.symbol or "EURUSD",
        position=req.ticket,
        volume=req.volume or 1.0,
        order_type=OrderType.SELL,
        comment="manual close",
    )

    try:
        raw_res = client.order_send(trade_req)
        res: TradeResult = await raw_res if inspect.isawaitable(raw_res) else raw_res
        result_dict = asdict(res)
        await broadcast_ws("position_closed", result_dict)
        return result_dict
    except Exception as exc:
        logger.exception("FR-trading-routes-positions: close error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@trading_router.post("/emergency/flatten")
async def emergency_flatten(req: EmergencyActionRequest) -> dict[str, Any]:
    """Panic button to flatten all open positions."""
    logger.info(
        "FR-trading-routes-panic: emergency flatten requested (conn=%s)",
        req.connection_id,
    )
    targets: list[tuple[str, TradingClient]] = []
    if req.connection_id:
        c = _registry.get_trading_client(req.connection_id)
        if c is not None:
            targets.append((req.connection_id, c))
    else:
        for cid, client in _registry.list_active():
            if isinstance(client, TradingClient):
                targets.append((cid, client))

    flattened_count = 0
    for _, client in targets:
        results = await _risk_guard.flatten_all(client)
        flattened_count += sum(
            1 for r in results if r.retcode == int(TradeRetcode.DONE)
        )

    await broadcast_ws("emergency_flatten", {"closed_count": flattened_count})
    return {"status": "success", "closed_positions": flattened_count}


@trading_router.post("/emergency/cancel-all")
async def emergency_cancel_all(req: EmergencyActionRequest) -> dict[str, Any]:
    """Panic button to cancel all working pending orders."""
    logger.info(
        "FR-trading-routes-panic: emergency cancel all requested (conn=%s)",
        req.connection_id,
    )
    targets: list[tuple[str, TradingClient]] = []
    if req.connection_id:
        c = _registry.get_trading_client(req.connection_id)
        if c is not None:
            targets.append((req.connection_id, c))
    else:
        for cid, client in _registry.list_active():
            if isinstance(client, TradingClient):
                targets.append((cid, client))

    canceled_count = 0
    for _, client in targets:
        results = await _risk_guard.cancel_all(client)
        canceled_count += sum(1 for r in results if r.retcode == int(TradeRetcode.DONE))

    await broadcast_ws("emergency_cancel_all", {"canceled_count": canceled_count})
    return {"status": "success", "canceled_orders": canceled_count}


@trading_router.post("/strategies/deploy")
async def deploy_strategy(req: DeployStrategyRequest) -> dict[str, Any]:
    """Deploy a strategy to live execution."""
    logger.info(
        "FR-trading-routes-strategy: deploying strategy %s for %s",
        req.strategy_id,
        req.symbol,
    )
    if req.document is None or req.document.strategy.id != req.strategy_id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422, detail="A matching canonical HSL document is required"
        )
    doc = StrategyCompiler().compile_to_runtime(req.document)
    spec = StrategyDeploySpec(
        strategy_doc=doc,
        symbol=req.symbol,
        connection_id=req.connection_id,
        timeframe=Timeframe(req.timeframe.removeprefix("PERIOD_")),
        allow_order_submission=req.allow_order_submission,
    )
    session = _supervisor.start_strategy(spec)
    return {
        "session_id": session.session_id,
        "status": session.status,
        "symbol": session.symbol,
        "connection_id": session.connection_id,
    }


@trading_router.post("/strategies/{session_id}/pause")
async def pause_strategy(session_id: str) -> dict[str, str]:
    """Pause an active strategy session."""
    _supervisor.pause_strategy(session_id)
    return {"status": "PAUSED", "session_id": session_id}


@trading_router.post("/strategies/{session_id}/resume")
async def resume_strategy(session_id: str) -> dict[str, str]:
    """Resume a paused strategy session."""
    _supervisor.resume_strategy(session_id)
    return {"status": "RUNNING", "session_id": session_id}


@trading_router.post("/strategies/{session_id}/stop")
async def stop_strategy(
    session_id: str,
    close_positions: bool = False,
) -> dict[str, str]:
    """Stop an active strategy session."""
    _supervisor.stop_strategy(session_id, close_positions=close_positions)
    return {"status": "STOPPED", "session_id": session_id}


@trading_router.get("/strategies")
async def list_strategies() -> list[dict[str, Any]]:
    """List all deployed strategy sessions."""
    return [
        {
            "session_id": s.session_id,
            "strategy_id": s.strategy_doc.strategy_id,
            "symbol": s.symbol,
            "connection_id": s.connection_id,
            "status": s.status,
            "trades_count": s.trades_count,
            "pnl": s.pnl,
        }
        for s in _supervisor.list_sessions()
    ]


@trading_router.websocket("/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    """WebSocket streaming real-time trade receipts, ticks, and events."""
    await websocket.accept()
    async with _ws_lock:
        _active_websockets.append(websocket)
    logger.debug("FR-trading-routes-stream: accepted WebSocket connection")

    try:
        while True:
            # Keepalive and client command receiver
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.debug("FR-trading-routes-stream: WebSocket client disconnected")
    finally:
        async with _ws_lock:
            if websocket in _active_websockets:
                _active_websockets.remove(websocket)


__all__ = ["trading_router"]
