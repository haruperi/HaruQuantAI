"""Live strategy supervisor coordinating real-time tick ingestion and order routing.

Description:
    Provides LiveStrategySupervisor, LiveStrategySession, and StrategyDeploySpec to
    manage live algorithmic strategies. Subscribes to real-time market data ticks,
    evaluates strategy rules through StrategyRuntime, filters effects through RiskGuard,
    and dispatches approved order and close intents to active broker clients.
Purpose:
    FEAT-LIVE-SUPERVISOR: Live strategy execution supervisor.
Key Capabilities:
    - FR-trading-supervisor-session: Manage strategy deployment lifecycle sessions.
    - FR-trading-supervisor-tick-dispatch: Ingest ticks and evaluate strategy rules.
    - FR-trading-supervisor-order-routing: Route approved effects to broker clients.
Python API Usage:
    from app.workspace.trading.supervisor import (
        LiveStrategySupervisor,
        StrategyDeploySpec,
    )
    supervisor = LiveStrategySupervisor()
    session = supervisor.start_strategy(spec)
    supervisor.on_tick(tick, symbol="EURUSD")
CLI Usage:
    uv run python -m pytest tests/workspace/trading/test_supervisor.py -q
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import Awaitable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Literal

from app.core.data.contracts import (
    AccountInfo,
    MarketTick,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.core.enums import (
    OrderTime,
    OrderType,
    Timeframe,
    TradeAction,
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.connection.base import TradingClient
from app.core.trading.strategy.contracts import (
    CloseRequest,
    EvaluationEvent,
    OrderRequest,
    StrategyContext,
    StrategyDocument,
    StrategyEffects,
    TickUpdateEvent,
)
from app.core.trading.strategy.runtime import StrategyRuntime
from app.workspace.trading.brokers.registry import (
    BrokerRegistry,
    default_broker_registry,
)
from app.workspace.trading.risk_guard import RiskGuard

logger = get_logger(__name__)


@dataclass(slots=True)
class LiveStrategySession:
    """Active live strategy session instance."""

    session_id: str
    strategy_doc: StrategyDocument
    symbol: str
    connection_id: str
    timeframe: Timeframe = Timeframe.PERIOD_H1
    status: Literal["RUNNING", "PAUSED", "STOPPED"] = "RUNNING"
    allow_order_submission: bool = False
    trades_count: int = 0
    pnl: float = 0.0
    context: StrategyContext = field(default_factory=StrategyContext)


@dataclass(frozen=True, slots=True)
class StrategyDeploySpec:
    """Deployment specification for starting a live strategy session."""

    strategy_doc: StrategyDocument
    symbol: str
    connection_id: str
    timeframe: Timeframe = Timeframe.PERIOD_H1
    session_id: str | None = None
    allow_order_submission: bool = False
    context: StrategyContext = field(default_factory=StrategyContext)


class LiveStrategySupervisor:
    """Supervisor coordinating strategy evaluation and execution."""

    def __init__(
        self,
        broker_registry: BrokerRegistry | None = None,
        risk_guard: RiskGuard | None = None,
        strategy_runtime: StrategyRuntime | None = None,
    ) -> None:
        self.registry = broker_registry or default_broker_registry
        self.risk_guard = risk_guard or RiskGuard()
        self.runtime = strategy_runtime or StrategyRuntime()
        self._sessions: dict[str, LiveStrategySession] = {}

    def start_strategy(self, spec: StrategyDeploySpec) -> LiveStrategySession:
        """Initialize runtime context and register a running strategy session."""
        session_id = spec.session_id or f"strat-{uuid.uuid4().hex[:8]}"
        session = LiveStrategySession(
            session_id=session_id,
            strategy_doc=spec.strategy_doc,
            symbol=spec.symbol,
            connection_id=spec.connection_id,
            allow_order_submission=spec.allow_order_submission,
            context=spec.context,
            timeframe=spec.timeframe,
            status="RUNNING",
        )
        self._sessions[session_id] = session
        logger.info(
            "FR-trading-supervisor-session: started strategy session %s for %s on %s",
            session_id,
            spec.symbol,
            spec.connection_id,
        )
        return session

    def pause_strategy(self, session_id: str) -> None:
        """Pause a strategy session from generating new trade orders."""
        session = self._sessions.get(session_id)
        if session is not None:
            session.status = "PAUSED"
            logger.info(
                "FR-trading-supervisor-session: paused strategy session %s",
                session_id,
            )

    def resume_strategy(self, session_id: str) -> None:
        """Resume a paused strategy session."""
        session = self._sessions.get(session_id)
        if session is not None:
            session.status = "RUNNING"
            logger.info(
                "FR-trading-supervisor-session: resumed strategy session %s",
                session_id,
            )

    def stop_strategy(
        self,
        session_id: str,
        *,
        close_positions: bool = False,
    ) -> None:
        """Stop a strategy session, optionally closing open positions."""
        session = self._sessions.get(session_id)
        if session is None:
            return

        session.status = "STOPPED"
        logger.info(
            "FR-trading-supervisor-session: stopped strategy session %s (close_pos=%s)",
            session_id,
            close_positions,
        )

        if close_positions:
            client = self.registry.get_trading_client(session.connection_id)
            if client is not None and client.is_connected:
                raw_positions = client.get_positions()
                positions: list[PositionInfo] = (
                    raw_positions
                    if not inspect.isawaitable(raw_positions)
                    else []  # Async positions handled by explicit async call if needed
                )
                for pos in positions:
                    if pos.symbol == session.symbol:
                        close_req = TradeRequest(
                            action=TradeAction.DEAL,
                            symbol=pos.symbol,
                            volume=pos.volume,
                            position=pos.ticket,
                            order_type=(
                                OrderType.SELL
                                if pos.position_type == 0
                                else OrderType.BUY
                            ),
                            comment="strategy stopped",
                        )
                        try:
                            client.order_send(close_req)
                        except Exception:
                            logger.exception(
                                "FR-trading-supervisor-order-routing: close error"
                            )

    def get_session(self, session_id: str) -> LiveStrategySession | None:
        """Return the strategy session by ID, or None."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[LiveStrategySession]:
        """Return a list of all active strategy sessions."""
        return list(self._sessions.values())

    def evaluate_event(
        self,
        session_id: str,
        event: EvaluationEvent,
        context: StrategyContext | None = None,
    ) -> StrategyEffects:
        """Evaluate any host event without sending orders; retain isolated state."""
        session = self._sessions[session_id]
        if session.status != "RUNNING" or session.symbol != event.symbol:
            return StrategyEffects()
        snapshot = context if context is not None else session.context
        snapshot = replace(snapshot, state=session.context.state)
        effects = self.runtime.evaluate(session.strategy_doc, snapshot, event)
        session.context = replace(snapshot, state=effects.state_updates)
        return effects

    def on_tick(self, tick: MarketTick, symbol: str) -> list[TradeResult]:
        """Adapt quotes into the same event dispatcher used by bars and lifecycle."""
        return self.on_event(TickUpdateEvent(symbol=symbol, tick=tick))

    def on_event(self, event: EvaluationEvent) -> list[TradeResult]:
        """Evaluate host events and submit effects only with distinct authorization."""
        symbol = event.symbol
        results: list[TradeResult] = []

        for session in list(self._sessions.values()):
            if session.status != "RUNNING" or session.symbol != symbol:
                continue

            client = self.registry.get_trading_client(session.connection_id)
            if client is None or not client.is_connected:
                continue

            snapshot = self._broker_snapshot(client, session.context)
            effects = self.evaluate_event(session.session_id, event, snapshot)
            if not session.allow_order_submission:
                logger.info("FR-trading-supervisor-order-routing: submission disabled")
                continue
            if effects.orders_to_cancel or effects.orders_to_modify:
                from app.core.lib.errors import DomainError

                raise DomainError(
                    code="HSL_LIVE_ACTION_UNAVAILABLE",
                    message="Live cancel/modify requires a confirmed broker adapter",
                )

            # Process exit requests
            for close_req in effects.positions_to_close:
                close_res = self._dispatch_close(client, close_req, session)
                if close_res is not None:
                    results.append(close_res)

            results.extend(self._dispatch_entries(client, session, effects))

        return results

    @staticmethod
    def _broker_snapshot(
        client: TradingClient, previous: StrategyContext
    ) -> StrategyContext:
        """Require synchronous broker snapshots before evaluating live effects."""
        methods = (client.get_positions, client.get_orders, client.get_account_info)
        if any(inspect.iscoroutinefunction(method) for method in methods):
            raise DomainError(
                code="HSL_ASYNC_BROKER_UNSUPPORTED",
                message="Synchronous dispatcher requires synchronous snapshots",
            )
        positions = client.get_positions()
        orders = client.get_orders()
        account = client.get_account_info()
        for value in (positions, orders, account):
            if inspect.isawaitable(value):
                if inspect.iscoroutine(value):
                    value.close()
                raise DomainError(
                    code="HSL_ASYNC_BROKER_UNSUPPORTED",
                    message="Async broker snapshots need an async host",
                )
        if (
            not isinstance(positions, list)
            or not isinstance(orders, list)
            or not isinstance(account, AccountInfo)
        ):
            raise DomainError(
                code="HSL_INVALID_BROKER_SNAPSHOT",
                message="Broker snapshot types do not match the host contract",
            )
        return replace(
            previous,
            positions=tuple(positions),
            orders=tuple(orders),
            account_balance=account.balance,
            account_equity=account.equity,
        )

    def _dispatch_entries(
        self,
        client: TradingClient,
        session: LiveStrategySession,
        effects: StrategyEffects,
    ) -> list[TradeResult]:
        """Apply host entry guards and return confirmed broker results."""
        results: list[TradeResult] = []

        # Process entry requests
        positions = session.context.positions
        symbol_pos_count = sum(1 for p in positions if p.symbol == session.symbol)

        for order_req in effects.orders_to_open:
            if not self.risk_guard.validate_order(order_req, symbol_pos_count):
                continue

            order_res = self._dispatch_order(client, order_req, session)
            if order_res is not None:
                results.append(order_res)
                if order_res.retcode == int(TradeRetcode.DONE):
                    session.trades_count += 1
                    symbol_pos_count += 1
        return results

    @staticmethod
    def _confirmed_result(result: TradeResult | Awaitable[TradeResult]) -> TradeResult:
        """Reject unconfirmed asynchronous operations in the synchronous host."""
        if inspect.isawaitable(result):
            if inspect.iscoroutine(result):
                result.close()
            raise DomainError(
                code="HSL_ASYNC_BROKER_UNSUPPORTED",
                message="Broker operation requires an async host",
            )
        return result

    def _dispatch_order(
        self,
        client: TradingClient,
        order_req: OrderRequest,
        session: LiveStrategySession,
    ) -> TradeResult | None:
        """Convert OrderRequest to TradeRequest and execute on broker client."""
        logger.info(
            "FR-trading-supervisor-order-routing: dispatching order %s vol=%.2f",
            order_req.symbol,
            order_req.volume,
        )
        trade_req = TradeRequest(
            action=TradeAction.DEAL
            if order_req.order_type in (OrderType.BUY, OrderType.SELL)
            else TradeAction.PENDING,
            type_time=OrderTime.SPECIFIED
            if order_req.atm_rules.get("expires_at")
            else OrderTime.GTC,
            expiration=datetime.fromtimestamp(
                int(order_req.atm_rules["expires_at"]), UTC
            )
            if order_req.atm_rules.get("expires_at")
            else None,
            symbol=order_req.symbol,
            volume=order_req.volume,
            order_type=order_req.order_type,
            price=order_req.price,
            sl=order_req.sl,
            tp=order_req.tp,
            magic=order_req.magic,
            comment=order_req.comment or f"live-strat-{session.session_id}",
        )
        if inspect.iscoroutinefunction(client.order_send):
            raise DomainError(
                code="HSL_ASYNC_BROKER_UNSUPPORTED",
                message="Synchronous dispatcher cannot submit async broker operations",
            )
        try:
            res = client.order_send(trade_req)
            return self._confirmed_result(res)
        except DomainError:
            raise
        except Exception as exc:
            logger.exception(
                "FR-trading-supervisor-order-routing: order execution failed"
            )
            return TradeResult(
                retcode=int(TradeRetcode.ERROR),
                comment=f"Order execution error: {exc}",
            )

    def _dispatch_close(
        self,
        client: TradingClient,
        close_req: CloseRequest,
        session: LiveStrategySession,
    ) -> TradeResult | None:
        """Convert CloseRequest to TradeRequest and execute on broker client."""
        logger.info(
            "FR-trading-supervisor-order-routing: dispatching close ticket %s",
            close_req.ticket,
        )
        position = next(
            (
                position
                for position in session.context.positions
                if str(position.ticket) == str(close_req.ticket)
            ),
            None,
        )
        if position is None or position.symbol != session.symbol:
            raise DomainError(
                code="HSL_POSITION_UNAVAILABLE",
                message="Close requires a confirmed matching position",
            )
        ticket = int(position.ticket)
        volume = close_req.volume if close_req.volume is not None else position.volume
        if not 0 < volume <= position.volume:
            raise DomainError(
                code="HSL_INVALID_CLOSE_VOLUME",
                message="Close quantity exceeds the confirmed position",
            )
        trade_req = TradeRequest(
            action=TradeAction.DEAL,
            symbol=session.symbol,
            position=ticket,
            volume=volume,
            order_type=OrderType.SELL if position.position_type == 0 else OrderType.BUY,
            comment=close_req.comment or "close position",
        )
        if inspect.iscoroutinefunction(client.order_send):
            raise DomainError(
                code="HSL_ASYNC_BROKER_UNSUPPORTED",
                message="Synchronous dispatcher cannot submit async broker operations",
            )
        try:
            res = client.order_send(trade_req)
            return self._confirmed_result(res)
        except DomainError:
            raise
        except Exception as exc:
            logger.exception(
                "FR-trading-supervisor-order-routing: close execution failed"
            )
            return TradeResult(
                retcode=int(TradeRetcode.ERROR),
                comment=f"Close error: {exc}",
            )


__all__ = [
    "LiveStrategySession",
    "LiveStrategySupervisor",
    "StrategyDeploySpec",
]
