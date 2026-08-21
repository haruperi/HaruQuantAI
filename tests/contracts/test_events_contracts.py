"""Tests for event contract DTO definitions."""

from datetime import UTC, datetime

from app.contracts.data.realtime_ticks import Tick
from app.contracts.events.broker import OrderCancelledEvent, OrderFilledEvent
from app.contracts.events.data import (
    HistoricalBarsRetrievedEvent,
    TickReceivedEvent,
)
from app.contracts.events.risk import (
    OrderProposalEvent,
    RiskLimitBreachedEvent,
)
from app.contracts.events.system import (
    FeatureMountedEvent,
    FeatureUnmountedEvent,
    ProfileReadinessChangedEvent,
)


def test_system_event_contracts() -> None:
    """Test system lifecycle events."""
    now = datetime.now(UTC)
    m_ev = FeatureMountedEvent(
        feature_id="FEAT-DATA-RETRIEVE_BARS", domain="data", timestamp=now
    )
    assert m_ev.feature_id == "FEAT-DATA-RETRIEVE_BARS"
    assert m_ev.domain == "data"
    assert m_ev.timestamp == now

    u_ev = FeatureUnmountedEvent(feature_id="FEAT-DATA-RETRIEVE_BARS", timestamp=now)
    assert u_ev.feature_id == "FEAT-DATA-RETRIEVE_BARS"

    r_ev = ProfileReadinessChangedEvent(
        profile="research",
        is_ready=False,
        missing_capabilities=("broker.market-data@1",),
        timestamp=now,
    )
    assert r_ev.profile == "research"
    assert r_ev.is_ready is False
    assert r_ev.missing_capabilities == ("broker.market-data@1",)


def test_data_event_contracts() -> None:
    """Test data domain events."""
    now = datetime.now(UTC)
    tick = Tick(symbol="EURUSD", timestamp=now, bid=1.1000, ask=1.1002)
    t_ev = TickReceivedEvent(symbol="EURUSD", tick=tick, timestamp=now)
    assert t_ev.symbol == "EURUSD"
    assert t_ev.tick.bid == 1.1000

    h_ev = HistoricalBarsRetrievedEvent(
        symbol="EURUSD", timeframe="M5", bar_count=100, timestamp=now
    )
    assert h_ev.bar_count == 100
    assert h_ev.timeframe == "M5"


def test_risk_event_contracts() -> None:
    """Test risk domain events."""
    now = datetime.now(UTC)
    breach = RiskLimitBreachedEvent(
        rule_name="MaxDrawdown",
        symbol="EURUSD",
        reason="Account drawdown exceeded 5%",
        timestamp=now,
    )
    assert breach.rule_name == "MaxDrawdown"

    proposal = OrderProposalEvent(
        symbol="EURUSD",
        side="BUY",
        quantity=1.0,
        price=1.1050,
        is_approved=True,
    )
    assert proposal.is_approved is True
    assert proposal.quantity == 1.0


def test_broker_event_contracts() -> None:
    """Test broker domain events."""
    now = datetime.now(UTC)
    filled = OrderFilledEvent(
        order_id="ORD-123",
        symbol="EURUSD",
        quantity=2.0,
        price=1.1025,
        timestamp=now,
    )
    assert filled.order_id == "ORD-123"
    assert filled.quantity == 2.0

    cancelled = OrderCancelledEvent(
        order_id="ORD-123",
        symbol="EURUSD",
        reason="User requested",
        timestamp=now,
    )
    assert cancelled.order_id == "ORD-123"
    assert cancelled.reason == "User requested"
