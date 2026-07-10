"""Unit tests for the trading monitoring and health submodule."""

import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Any, Self

import pytest
from app.services.trading.config.models import (
    MonitoringSettings,
    SecretReference,
    StoreConnectionTargets,
    TradingRuntimeConfig,
)
from app.services.trading.contracts import TradingRoute
from app.services.trading.monitoring.heartbeat_watchdog import HeartbeatEmitter
from app.services.trading.monitoring.operational_signals import (
    OperationalSignalsManager,
)
from app.services.trading.monitoring.service import MonitoringService
from app.services.trading.monitoring.timeouts_and_staleness import (
    LatencyTracker,
    LostOrderWatchdog,
)
from app.services.trading.monitoring.tool_health import ToolHealthMonitor

# --- Mock Classes ---


class DummyClock:
    """Mock clock for deterministic test time."""

    def __init__(self, start_time: datetime | None = None) -> None:
        """Initialize the dummy clock."""
        self._now = start_time or datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)
        self._monotonic = 0.0

    def now_utc(self) -> datetime:
        """Return the current mocked time."""
        return self._now

    def now_ptp(self) -> datetime:
        """Return the current mocked time aligned with PTP."""
        return self._now

    def monotonic(self) -> float:
        """Return monotonic elapsed time."""
        return self._monotonic

    def advance(self, seconds: float) -> None:
        """Advance the current mocked time."""
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds


class DummyReconciliationService:
    """Mock reconciliation service to verify watchdog triggers."""

    def __init__(self, should_fail: bool = False) -> None:
        """Initialize dummy reconciliation service."""
        self.called = False
        self.last_route: TradingRoute | None = None
        self.last_run_type: str | None = None
        self._should_fail = should_fail

    def run_reconciliation(
        self,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        run_type: str,
    ) -> object:
        """Simulate running reconciliation."""
        _ = (tenant_id, account_id)
        self.called = True
        self.last_route = route
        self.last_run_type = run_type
        if self._should_fail:
            raise RuntimeError("Simulation of reconciliation service failure.")
        return {}


# --- Helper to create a valid config ---


def create_test_config(
    consecutive_rejects_limit: int = 5,
    unknown_outcomes_limit: int = 3,
    unknown_outcomes_window_seconds: int = 300,
    latency_p95_limit_ms: float = 500.0,
    latency_window_samples: int = 100,
    latency_downgrade_duration_seconds: int = 60,
    life_to_live_seconds: int = 120,
    heartbeat_interval_seconds: int = 30,
) -> TradingRuntimeConfig:
    """Build a configuration model with custom monitoring parameters."""
    return TradingRuntimeConfig(
        active_broker="mt5",
        store_targets=StoreConnectionTargets(
            trade_store_ref="store://trade",
            state_store_ref="store://state",
            audit_sink_ref="sink://audit",
            idempotency_store_ref="store://idempotency",
            event_journal_ref="journal://event",
        ),
        secret_references={
            "broker_credentials": SecretReference(reference="vault://broker"),
            "database_credentials": SecretReference(reference="vault://db"),
        },
        monitoring=MonitoringSettings(
            consecutive_rejects_limit=consecutive_rejects_limit,
            unknown_outcomes_limit=unknown_outcomes_limit,
            unknown_outcomes_window_seconds=unknown_outcomes_window_seconds,
            latency_p95_limit_ms=latency_p95_limit_ms,
            latency_window_samples=latency_window_samples,
            latency_downgrade_duration_seconds=latency_downgrade_duration_seconds,
            life_to_live_seconds=life_to_live_seconds,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            runbook_registry={
                "stale_order": "RB-STALE-ORDER-001",
                "circuit_breaker": "RB-CB-001",
            },
            escalation_chain={
                "high": ["pagerduty", "ops-channel"],
                "critical": ["pagerduty", "telephony", "slack-emergency"],
            },
        ),
    )


# --- LatencyTracker Tests ---


def test_latency_tracker_percentile() -> None:
    """Test LatencyTracker handles p95 and bounded samples properly."""
    tracker = LatencyTracker(max_samples=5)

    # Empty tracker returns 0.0
    assert tracker.get_p95_latency() == 0.0

    # Negative values are ignored
    tracker.record_latency(-5.0)
    assert len(tracker.samples) == 0

    # Record some observations
    for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
        tracker.record_latency(lat)

    assert len(tracker.samples) == 5
    # Samples are: [10, 20, 30, 40, 50]. 95th percentile index is 5 * 0.95 = 4
    # Sorted[4] is 50.0
    assert tracker.get_p95_latency() == 50.0

    # Test limit enforcement
    tracker.record_latency(60.0)
    assert len(tracker.samples) == 5
    assert tracker.samples == [20.0, 30.0, 40.0, 50.0, 60.0]


# --- LostOrderWatchdog Tests ---


def test_lost_order_watchdog() -> None:
    """Test LostOrderWatchdog identifies stale orders and forces syncs."""
    clock = DummyClock()
    watchdog = LostOrderWatchdog(life_to_live_seconds=60, clock=clock)
    rec_service = DummyReconciliationService()

    active_orders: list[dict[str, Any]] = [
        # Terminal state - ignored
        {
            "ticket": "t-1",
            "state": "FILLED",
            "created_at": clock.now_utc() - timedelta(seconds=100),
        },
        # Missing created_at - ignored
        {"ticket": "t-2", "state": "NEW"},
        # Invalid created_at type/format - ignored
        {"ticket": "t-3", "state": "NEW", "created_at": "invalid-timestamp"},
        # Fresh order - ignored
        {
            "ticket": "t-4",
            "state": "NEW",
            "created_at": clock.now_utc() - timedelta(seconds=30),
        },
        # Stale order - datetime format
        {
            "ticket": "t-5",
            "state": "NEW",
            "created_at": clock.now_utc() - timedelta(seconds=120),
        },
        # Stale order - ISO string format
        {
            "ticket": "t-6",
            "state": "NEW",
            "created_at": (clock.now_utc() - timedelta(seconds=90)).isoformat(),
        },
    ]

    stale_tickets = watchdog.check_stale_orders(
        active_orders=active_orders,
        reconciliation_service=rec_service,
        route=TradingRoute.PAPER,
        tenant_id="tenant-1",
        account_id="acct-1",
    )

    assert "t-5" in stale_tickets
    assert "t-6" in stale_tickets
    assert len(stale_tickets) == 2
    assert active_orders[4]["state"] == "STALE"
    assert active_orders[5]["state"] == "STALE"
    assert rec_service.called
    assert rec_service.last_route == TradingRoute.PAPER
    assert rec_service.last_run_type == "stale_order"

    # Edge Case: Stale order but missing/empty ticket key or value
    active_orders_no_ticket: list[dict[str, Any]] = [
        {"state": "NEW", "created_at": clock.now_utc() - timedelta(seconds=200)},
    ]
    rec_service.called = False
    stale_no_ticket = watchdog.check_stale_orders(
        active_orders=active_orders_no_ticket,
        reconciliation_service=rec_service,
        route=TradingRoute.PAPER,
        tenant_id="tenant-1",
        account_id="acct-1",
    )
    assert len(stale_no_ticket) == 0
    assert not rec_service.called

    # Edge Case: Run check with empty orders list (empty stale_tickets)
    stale_empty = watchdog.check_stale_orders(
        active_orders=[],
        reconciliation_service=rec_service,
        route=TradingRoute.PAPER,
        tenant_id="tenant-1",
        account_id="acct-1",
    )
    assert len(stale_empty) == 0


def test_lost_order_watchdog_swallows_failure() -> None:
    """Test LostOrderWatchdog handles reconciliation exceptions safely."""
    clock = DummyClock()
    watchdog = LostOrderWatchdog(life_to_live_seconds=60, clock=clock)
    rec_service = DummyReconciliationService(should_fail=True)

    active_orders: list[dict[str, Any]] = [
        {
            "ticket": "t-1",
            "state": "NEW",
            "created_at": clock.now_utc() - timedelta(seconds=120),
        },
    ]

    # Should not raise exception
    stale = watchdog.check_stale_orders(
        active_orders=active_orders,
        reconciliation_service=rec_service,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
    )
    assert len(stale) == 1
    assert rec_service.called


# --- ToolHealthMonitor Tests ---


def test_tool_health_monitor() -> None:
    """Test ToolHealthMonitor degrades and restores health correctly."""
    monitor = ToolHealthMonitor(failure_threshold=3)

    assert str(monitor.status) == "HEALTHY"
    assert monitor.is_healthy
    assert monitor.consecutive_failures == 0

    # First failure -> degraded
    monitor.record_failure("Timeout 1")
    assert str(monitor.status) == "DEGRADED"
    assert not monitor.is_healthy
    assert monitor.consecutive_failures == 1

    # Second failure -> degraded
    monitor.record_failure("Timeout 2")
    assert str(monitor.status) == "DEGRADED"
    assert monitor.consecutive_failures == 2

    # Third failure -> failed
    monitor.record_failure("Timeout 3")
    assert str(monitor.status) == "FAILED"
    assert monitor.consecutive_failures == 3

    # Success restores to healthy
    monitor.record_success()
    assert str(monitor.status) == "HEALTHY"
    assert monitor.is_healthy
    assert monitor.consecutive_failures == 0


# --- OperationalSignalsManager Tests ---


def test_signals_manager() -> None:
    """Test signals manager triggers alerts and handles escalations."""
    clock = DummyClock()
    registry = {"stale_order": "RB-STALE-ORDER-001"}
    chain = {
        "high": ["ops-channel", "email"],
        "critical": ["ops-channel", "sms", "pagerduty"],
    }

    manager = OperationalSignalsManager(
        runbook_registry=registry,
        escalation_chain=chain,
        clock=clock,
        rate_limit_seconds=10.0,
    )

    # Normal emit
    sig1 = manager.emit_signal(
        incident_id="inc-1",
        incident_class="stale_order",
        severity="high",
        message="Stale order t-100",
    )
    assert sig1 is not None
    assert sig1.runbook_id == "RB-STALE-ORDER-001"
    assert sig1.severity == "high"

    # Rate limiting checks
    sig2 = manager.emit_signal(
        incident_id="inc-2",
        incident_class="stale_order",
        severity="high",
        message="Stale order t-101",
    )
    assert sig2 is None  # Skipped due to rate-limiting

    # Advance clock and try again
    clock.advance(15.0)
    sig3 = manager.emit_signal(
        incident_id="inc-3",
        incident_class="stale_order",
        severity="high",
        message="Stale order t-102",
    )
    assert sig3 is not None

    # Missing runbook ID sets default
    sig_no_rb = manager.emit_signal(
        incident_id="inc-4",
        incident_class="unknown_class",
        severity="warning",
        message="Unknown incident class check",
    )
    assert sig_no_rb is not None
    assert sig_no_rb.runbook_id == "RB-UNKNOWN-001"

    # Test escalations
    # Sig1 and Sig3 are active incidents of 'high' severity.
    # High has escalation window chain: ['ops-channel', 'email'].
    # A check immediately does not trigger escalations
    actions_none = manager.check_escalations(window_seconds=30.0)
    assert len(actions_none) == 0

    # Advance clock to exceed window (30s)
    clock.advance(35.0)
    actions = manager.check_escalations(window_seconds=30.0)
    # Both active signals inc-1 and inc-3 should escalate to step 1 ('ops-channel')
    assert len(actions) == 2
    assert actions[0]["incident_id"] == "inc-1"
    assert actions[0]["channel"] == "ops-channel"
    assert actions[0]["step"] == 1

    # Acknowledge one incident
    manager.acknowledge_incident("inc-1")
    # Acknowledging again returns False
    assert not manager.acknowledge_incident("inc-1")

    # Advance clock to exceed step 2 window (total elapsed 70s)
    clock.advance(35.0)
    actions_step2 = manager.check_escalations(window_seconds=30.0)
    # Only inc-3 escalates to step 2 ('email')
    assert len(actions_step2) == 1
    assert actions_step2[0]["incident_id"] == "inc-3"
    assert actions_step2[0]["channel"] == "email"
    assert actions_step2[0]["step"] == 2

    # A check after exhaust does nothing further
    clock.advance(35.0)
    actions_exhausted = manager.check_escalations(window_seconds=30.0)
    assert len(actions_exhausted) == 0


# --- HeartbeatEmitter Tests ---


class MockResponse:
    """Simulated http response."""

    def __init__(self, status: int) -> None:
        """Initialize mock response."""
        self.status = status

    def __enter__(self) -> Self:
        """Enter context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context."""
        return


def test_heartbeat_emitter_scheme_check() -> None:
    """Test heartbeat validates url scheme."""
    clock = DummyClock()
    emitter = HeartbeatEmitter(watchdog_url="ftp://localhost/hb", clock=clock)
    assert not emitter.send_heartbeat()
    assert not emitter.last_success


def test_heartbeat_emitter_url_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test heartbeat emitter handles network returns and errors."""
    clock = DummyClock()
    emitter = HeartbeatEmitter(watchdog_url="http://localhost:8080/hb", clock=clock)

    # 1. Success case (200 OK)
    def mock_ok(req: Any, timeout: float | None = None) -> MockResponse:
        _ = (req, timeout)
        return MockResponse(200)

    monkeypatch.setattr("urllib.request.urlopen", mock_ok)
    assert emitter.send_heartbeat()
    assert emitter.last_success
    assert emitter.last_heartbeat_time == clock.now_utc()

    # 2. Bad Status code (500 Internal Error)
    def mock_fail(req: Any, timeout: float | None = None) -> MockResponse:
        _ = (req, timeout)
        return MockResponse(500)

    monkeypatch.setattr("urllib.request.urlopen", mock_fail)
    assert not emitter.send_heartbeat()
    assert not emitter.last_success

    # 3. Connection Exception / URLError
    def raise_url_error(*_args: Any, **_kwargs: Any) -> Any:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
    assert not emitter.send_heartbeat()
    assert not emitter.last_success


# --- MonitoringService Tests ---


def test_monitoring_service_triggers() -> None:
    """Test MonitoringService circuit breakers triggers."""
    clock = DummyClock()
    config = create_test_config(consecutive_rejects_limit=2, unknown_outcomes_limit=2)
    sig_manager = OperationalSignalsManager(
        runbook_registry=config.monitoring.runbook_registry,
        escalation_chain=config.monitoring.escalation_chain,
        clock=clock,
    )
    emitter = HeartbeatEmitter("http://localhost:8080/hb", clock=clock)

    service = MonitoringService(
        config=config,
        clock=clock,
        signals_manager=sig_manager,
        heartbeat_emitter=emitter,
    )

    # Healthy state
    status = service.get_monitoring_status()
    assert not status["circuit_breaker_tripped"]
    assert status["tool_health_status"] == "HEALTHY"
    assert status["current_capability"] == "full_live"

    # Test Consecutive Rejects Breaker
    service.record_broker_reject()
    assert not service.circuit_breaker_tripped
    service.record_broker_reject()
    assert service.circuit_breaker_tripped
    assert "Consecutive broker rejects" in service._circuit_breaker_reason

    # Reset breaker
    service.reset_circuit_breaker()
    assert not service.circuit_breaker_tripped
    # Reset again when not tripped to cover False branch of tripped check
    service.reset_circuit_breaker()

    # Test Unknown Outcomes Breaker
    service.record_unknown_outcome()
    assert not service.circuit_breaker_tripped
    # Advance clock a little, remaining in window
    clock.advance(10.0)
    service.record_unknown_outcome()
    assert service.circuit_breaker_tripped
    assert "Unknown outcomes count" in service._circuit_breaker_reason

    service.reset_circuit_breaker()

    # Test Reconciliation Drift Breaker
    service.record_reconciliation_mismatch("Price drift on EURUSD")
    assert service.circuit_breaker_tripped
    assert "Reconciliation drift limits exceeded" in service._circuit_breaker_reason

    service.reset_circuit_breaker()

    # Test Stream Gap Breaker
    service.record_stream_gap()
    assert service.circuit_breaker_tripped
    assert "stream or sequence gap" in service._circuit_breaker_reason
    # Record another stream gap while breaker is already tripped
    # (covers True branch of check)
    service.record_stream_gap()

    service.reset_circuit_breaker()

    # Test Durability Failure Breaker
    service.record_durability_failure()
    assert service.circuit_breaker_tripped
    assert "durability failure" in service._circuit_breaker_reason


def test_monitoring_service_latency_downgrade() -> None:
    """Test dynamic live capability route downgrades based on execution latency."""
    clock = DummyClock()
    config = create_test_config(
        latency_p95_limit_ms=100.0,
        latency_window_samples=10,
        latency_downgrade_duration_seconds=30,
    )
    sig_manager = OperationalSignalsManager(
        runbook_registry=config.monitoring.runbook_registry,
        escalation_chain=config.monitoring.escalation_chain,
        clock=clock,
    )

    service = MonitoringService(
        config=config,
        clock=clock,
        signals_manager=sig_manager,
    )

    assert service.current_capability == "full_live"

    # Record some fast latencies (e.g. 50ms)
    for _ in range(10):
        service.record_broker_success(50.0)
    assert service.current_capability == "full_live"

    # Record high latency (e.g. 200ms)
    service.record_broker_success(200.0)
    # High latency started tracking, but downgrade duration (30s) not elapsed
    assert service.current_capability == "full_live"

    # Advance clock (20s) - still below downgrade duration
    clock.advance(20.0)
    service.record_broker_success(200.0)
    assert service.current_capability == "full_live"

    # Advance clock further to cross 30s threshold
    clock.advance(15.0)
    service.record_broker_success(200.0)
    # Exceeded duration -> Downgrade to micro_live
    assert service.current_capability == "micro_live"

    # Restore latency below limit
    for _ in range(10):
        service.record_broker_success(40.0)
    # Restored to full_live
    assert service.current_capability == "full_live"


def test_monitoring_watchdog_and_heartbeat_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test monitoring service calls lost-order check and heartbeat emission."""
    clock = DummyClock()
    config = create_test_config()
    sig_manager = OperationalSignalsManager(
        runbook_registry=config.monitoring.runbook_registry,
        escalation_chain=config.monitoring.escalation_chain,
        clock=clock,
    )
    rec_service = DummyReconciliationService()

    # Success heartbeat mock
    def mock_ok(req: Any, timeout: float | None = None) -> MockResponse:
        _ = (req, timeout)
        return MockResponse(200)

    monkeypatch.setattr("urllib.request.urlopen", mock_ok)
    emitter = HeartbeatEmitter("http://localhost:8080/hb", clock=clock)

    service = MonitoringService(
        config=config,
        clock=clock,
        signals_manager=sig_manager,
        heartbeat_emitter=emitter,
    )

    # Lost-order delegation
    active_orders: list[dict[str, Any]] = [
        {
            "ticket": "t-1",
            "state": "NEW",
            "created_at": clock.now_utc() - timedelta(seconds=200),
        },
    ]
    stale = service.run_stale_order_check(
        active_orders=active_orders,
        reconciliation_service=rec_service,
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
    )
    assert len(stale) == 1
    assert rec_service.called

    # Heartbeat cycle delegation success
    assert service.run_heartbeat_cycle()

    # Heartbeat cycle delegation failure emits incident warning signal
    def mock_fail(req: Any, timeout: float | None = None) -> MockResponse:
        _ = (req, timeout)
        return MockResponse(500)

    monkeypatch.setattr("urllib.request.urlopen", mock_fail)
    assert not service.run_heartbeat_cycle()
    assert len(sig_manager.audit_log) == 1
    assert sig_manager.audit_log[0].incident_class == "heartbeat_failure"
    assert sig_manager.audit_log[0].severity == "warning"

    # If heartbeat emitter is None, run_heartbeat_cycle returns False cleanly
    service_no_emitter = MonitoringService(
        config=config,
        clock=clock,
        signals_manager=sig_manager,
        heartbeat_emitter=None,
    )
    assert not service_no_emitter.run_heartbeat_cycle()
