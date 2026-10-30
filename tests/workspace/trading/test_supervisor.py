"""Tests for LiveStrategySupervisor session management and real-time tick ingestion."""

from __future__ import annotations

from typing import override

from app.core.data.contracts import (
    MarketTick,
    PositionInfo,
    TradeRequest,
    TradeResult,
)
from app.core.enums import OrderType, TradeAction, TradeRetcode
from app.core.trading.connection.base import TradingClient
from app.core.trading.strategy.contracts import (
    ActionKind,
    ConditionDefinition,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    StrategyContext,
    StrategyDocument,
)
from app.workspace.trading.brokers.registry import BrokerRegistry
from app.workspace.trading.risk_guard import RiskGuard
from app.workspace.trading.supervisor import (
    LiveStrategySession,
    LiveStrategySupervisor,
    StrategyDeploySpec,
)


class MockSupervisorClient(TradingClient):
    """Mock TradingClient for testing supervisor execution."""

    def __init__(self, name: str = "MockSupervisorClient") -> None:
        super().__init__(name)
        self.connect()
        self.arm()
        self.sent_requests: list[TradeRequest] = []
        self._positions: list[PositionInfo] = []

    @override
    def get_positions(self) -> list[PositionInfo]:
        return list(self._positions)

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        self.sent_requests.append(request)
        ticket = len(self.sent_requests) + 1000
        if request.action == TradeAction.DEAL:
            self._positions.append(
                PositionInfo(
                    ticket=ticket,
                    symbol=request.symbol,
                    volume=request.volume,
                    position_type=0 if request.order_type == OrderType.BUY else 1,
                )
            )
        return TradeResult(retcode=int(TradeRetcode.DONE), order=ticket)


def _sample_strategy(symbol: str = "EURUSD") -> StrategyDocument:
    """Build a minimal strategy document that triggers BUY on tick."""
    rule = RuleDefinition(
        rule_id="r1",
        name="BuyOnTick",
        trigger=RuleTriggerKind.ON_TICK,
        conditions=(ConditionDefinition(left=1.0, comparator=">", right=0.0),),
        actions=(
            RuleAction(
                kind=ActionKind.ENTER,
                direction=1,
                volume=0.5,
                order_type=OrderType.BUY,
            ),
        ),
    )
    return StrategyDocument(
        strategy_id="strat-test-1",
        rules=(rule,),
    )


def _get_status(session: LiveStrategySession) -> str:
    return str(session.status)


def test_supervisor_session_lifecycle() -> None:
    registry = BrokerRegistry()
    client = MockSupervisorClient()
    registry.register("conn-1", client)

    supervisor = LiveStrategySupervisor(broker_registry=registry)
    doc = _sample_strategy("EURUSD")

    spec = StrategyDeploySpec(
        strategy_doc=doc,
        symbol="EURUSD",
        connection_id="conn-1",
    )
    session = supervisor.start_strategy(spec)

    assert _get_status(session) == "RUNNING"
    assert session.symbol == "EURUSD"
    assert supervisor.get_session(session.session_id) is session
    assert len(supervisor.list_sessions()) == 1

    # Pause
    supervisor.pause_strategy(session.session_id)
    assert _get_status(session) == "PAUSED"

    # Resume
    supervisor.resume_strategy(session.session_id)
    assert _get_status(session) == "RUNNING"

    # Stop with close_positions
    client._positions.append(
        PositionInfo(ticket=999, symbol="EURUSD", volume=0.5, position_type=0)
    )
    supervisor.stop_strategy(session.session_id, close_positions=True)
    assert _get_status(session) == "STOPPED"
    assert any(r.position == 999 for r in client.sent_requests)


def test_supervisor_on_tick_dispatch() -> None:
    registry = BrokerRegistry()
    client = MockSupervisorClient()
    registry.register("conn-1", client)

    guard = RiskGuard()
    supervisor = LiveStrategySupervisor(broker_registry=registry, risk_guard=guard)
    doc = _sample_strategy("EURUSD")

    spec = StrategyDeploySpec(
        strategy_doc=doc,
        symbol="EURUSD",
        connection_id="conn-1",
    )
    session = supervisor.start_strategy(spec)

    tick = MarketTick(time_msc=1700000000000, bid=1.1000, ask=1.1002, last=1.1001)

    # Tick for different symbol is ignored
    results_other = supervisor.on_tick(tick, symbol="GBPUSD")
    assert len(results_other) == 0
    assert len(client.sent_requests) == 0

    # Matching symbol executes rule
    results = supervisor.on_tick(tick, symbol="EURUSD")
    assert len(results) == 1
    assert results[0].retcode == int(TradeRetcode.DONE)
    assert session.trades_count == 1
    assert len(client.sent_requests) == 1
    assert client.sent_requests[0].symbol == "EURUSD"
    assert client.sent_requests[0].volume == 0.5


def test_supervisor_exit_rule_dispatch() -> None:
    registry = BrokerRegistry()
    client = MockSupervisorClient()
    registry.register("conn-1", client)

    exit_rule = RuleDefinition(
        rule_id="r_exit",
        name="ExitOnTick",
        trigger=RuleTriggerKind.ON_TICK,
        conditions=(ConditionDefinition(left=1.0, comparator=">", right=0.0),),
        actions=(
            RuleAction(
                kind=ActionKind.EXIT,
                volume=1.0,
                order_type=OrderType.SELL,
            ),
        ),
    )
    doc = StrategyDocument(
        strategy_id="strat-exit",
        rules=(exit_rule,),
    )
    supervisor = LiveStrategySupervisor(broker_registry=registry)
    spec = StrategyDeploySpec(
        strategy_doc=doc,
        symbol="EURUSD",
        connection_id="conn-1",
    )
    session = supervisor.start_strategy(spec)
    # Add open position
    client._positions.append(
        PositionInfo(ticket=5555, symbol="EURUSD", volume=1.0, position_type=0)
    )
    session.context = StrategyContext(
        positions=(
            PositionInfo(ticket=5555, symbol="EURUSD", volume=1.0, position_type=0),
        )
    )

    tick = MarketTick(time_msc=1700000000000, bid=1.1000, ask=1.1002, last=1.1001)
    results = supervisor.on_tick(tick, symbol="EURUSD")
    assert len(results) >= 1
    assert any(r.retcode == int(TradeRetcode.DONE) for r in results)
    assert any(req.position == 5555 for req in client.sent_requests)
