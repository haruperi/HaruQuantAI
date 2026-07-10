"""Unit tests for the session manager runtime module."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.trading.contracts import (
    TimeInForce,
    TradingRoute,
)
from app.services.trading.gates.kill_switch import OperationalMode
from app.services.trading.runtime.session_manager import (
    SessionManager,
    SessionState,
)
from app.services.trading.security.error_mapping import TradingValidationError


class MockClock:
    """Mock clock for deterministic tests."""

    def __init__(self, now: datetime) -> None:
        self._now = now
        self._monotonic = 0.0

    def now_utc(self) -> datetime:
        return self._now

    def now_ptp(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds


class MockStateStore:
    """Mock state snapshot store."""

    def __init__(self, data: dict | None = None) -> None:
        self.data = data or {}
        self.save_called = 0
        self.load_called = 0
        self.raise_error = False

    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: dict,
        expected_version: int | None,
    ) -> str:
        self.save_called += 1
        self.data[(route, tenant_id)] = snapshot
        return "snap-ref-1"

    def load_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot_id: str,
    ) -> dict | None:
        self.load_called += 1
        if self.raise_error:
            raise RuntimeError("Database connection lost.")
        return self.data.get((route, tenant_id))


class MockSignalsManager:
    """Mock signals manager."""

    def __init__(self) -> None:
        self.signals: list[tuple[str, str, str]] = []

    def emit_signal(self, incident_class: str, severity: str, message: str) -> None:
        self.signals.append((incident_class, severity, message))


@pytest.fixture(autouse=True)
def clean_registry() -> None:
    """Clean the active live sessions registry before each test."""
    SessionManager._active_live_sessions.clear()


def test_session_manager_initial_state() -> None:
    """Test initial attributes of the SessionManager."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )
    assert mgr.state == SessionState.STOPPED
    assert mgr.mode == OperationalMode.STOPPED
    assert not mgr.is_symbol_halted("EURUSD")


def test_session_manager_start_and_stop() -> None:
    """Test session startup, state restoration, and shutdown."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )

    # Starts successfully with defaults
    mgr.start_session()
    assert mgr.state == SessionState.RUNNING
    assert mgr.mode == OperationalMode.NORMAL
    assert store.load_called == 1

    # Stops successfully
    mgr.stop_session()
    assert mgr.state == SessionState.STOPPED
    assert mgr.mode == OperationalMode.STOPPED


def test_single_active_live_session() -> None:
    """Only one active live session is allowed per scope (TRD-FR-065)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()

    mgr1 = SessionManager(
        scope="acct-1",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
    )
    mgr2 = SessionManager(
        scope="acct-1",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
    )

    mgr1.start_session()

    # Second session on same scope raises ValidationError
    with pytest.raises(
        TradingValidationError, match="Active live session already exists"
    ):
        mgr2.start_session()

    # Different scope is allowed
    mgr3 = SessionManager(
        scope="acct-2",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
    )
    mgr3.start_session()

    # Stopping session removes it from registry
    mgr1.stop_session()
    mgr2.start_session()  # Now it can start


def test_session_state_restoration_failure() -> None:
    """If state restoration fails, session fails closed to read_only paused (TRD-FR-068)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    store.raise_error = True
    signals = MockSignalsManager()

    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
        signals_manager=signals,
    )

    mgr.start_session()
    assert mgr.state == SessionState.PAUSED
    assert mgr.mode == OperationalMode.READ_ONLY
    assert len(signals.signals) == 1
    assert "restoration_failed" in signals.signals[0][0]


def test_session_restoration_from_snapshot() -> None:
    """Test state restoration from snapshot loads mode and halts."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    store.save_state(
        route=TradingRoute.SIM,
        tenant_id="acct-1",
        snapshot={"mode": "close_only", "halted_symbols": ["EURUSD", "GBPUSD"]},
        expected_version=None,
    )

    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )

    mgr.start_session()
    assert mgr.state == SessionState.RUNNING
    assert mgr.mode == OperationalMode.CLOSE_ONLY
    assert mgr.is_symbol_halted("EURUSD")
    assert mgr.is_symbol_halted("GBPUSD")
    assert not mgr.is_symbol_halted("USDJPY")


def test_session_recovery_modes() -> None:
    """Recovery transitions session based on outcomes, sync, and logs (TRD-FR-066)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )

    # 1. Unresolved/failed recovery -> paused state
    mgr.recover_session(
        has_unknown_broker_outcomes=True,
        is_unreconciled=False,
        missing_audit_logs=False,
    )
    assert mgr.state == SessionState.PAUSED

    # 2. Perfect recovery -> running normal state
    mgr.recover_session(
        has_unknown_broker_outcomes=False,
        is_unreconciled=False,
        missing_audit_logs=False,
    )
    assert mgr.state == SessionState.RUNNING
    assert mgr.mode == OperationalMode.NORMAL


def test_reconnection_auto_resync() -> None:
    """Transition from Disconnected to Connected forces resync state (TRD-FR-072)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )
    mgr.start_session()
    assert mgr.mode == OperationalMode.NORMAL

    # Reconnection blocks mutations and sets mode to READ_ONLY + PAUSED
    mgr.update_connection_state(True)  # Disconnected -> Connected
    assert mgr.mode == OperationalMode.READ_ONLY
    assert mgr.state == SessionState.PAUSED

    # Returning to NORMAL requires completing reconciliation
    mgr.complete_reconciliation()
    assert mgr.mode == OperationalMode.NORMAL
    assert mgr.state == SessionState.RUNNING


def test_cancel_on_disconnect_heartbeat_failsafe() -> None:
    """CoD failsafe triggers emergency flatten when local heartbeat drops (TRD-FR-067)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
    )
    mgr.start_session()
    mgr.cod_supported = False
    mgr.cod_timeout_seconds = 5.0

    # Under timeout limit
    clock.advance(3.0)
    assert not mgr.check_cod_failsafe()

    # Over timeout limit
    clock.advance(3.0)
    assert mgr.check_cod_failsafe()
    assert mgr.mode == OperationalMode.EMERGENCY_FLATTEN


def test_synthetic_emulation_heartbeat_and_alerts() -> None:
    """Synthetic stop/OCO monitoring loop triggers CLOSE_ONLY on heartbeat drop (TRD-FR-070)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    signals = MockSignalsManager()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.LIVE,
        state_store=store,
        clock=clock,
        signals_manager=signals,
    )
    mgr.start_session()
    mgr.synthetic_emulation_enabled = True
    mgr.synthetic_emulation_heartbeat_ttl = 4.0

    # 1. Orders active -> Emits signal
    mgr.check_synthetic_emulation(active_orders={"order-1"}, heartbeat_received=True)
    assert len(signals.signals) == 1
    assert "synthetic_orders_active" in signals.signals[0][0]

    # 2. Heartbeat within limit
    clock.advance(2.0)
    mgr.check_synthetic_emulation(active_orders={"order-1"}, heartbeat_received=False)
    assert mgr.mode == OperationalMode.NORMAL

    # 3. Heartbeat lost -> Transitions to CLOSE_ONLY
    clock.advance(3.0)  # Total 5s elapsed since last heartbeat (ttl=4s)
    mgr.check_synthetic_emulation(active_orders={"order-1"}, heartbeat_received=False)
    assert mgr.mode == OperationalMode.CLOSE_ONLY


def test_expiry_watchdog() -> None:
    """Watchdog cancels expired GTD/DAY orders when broker lacks native support (TRD-FR-069)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )

    now = clock.now_utc()
    expiry_past = (now - timedelta(minutes=5)).isoformat()
    expiry_future = (now + timedelta(minutes=5)).isoformat()

    orders = [
        # GTD, native expiry is unsupported, expired -> CANCEL
        {
            "order_id": "ord-1",
            "tif": TimeInForce.GTD,
            "native_expiry_supported": False,
            "expiration_utc": expiry_past,
        },
        # GTD, native expiry is supported, expired -> SKIP (broker manages it)
        {
            "order_id": "ord-2",
            "tif": TimeInForce.GTD,
            "native_expiry_supported": True,
            "expiration_utc": expiry_past,
        },
        # GTD, native expiry is unsupported, future -> SKIP
        {
            "order_id": "ord-3",
            "tif": TimeInForce.GTD,
            "native_expiry_supported": False,
            "expiration_utc": expiry_future,
        },
        # GTC, native expiry unsupported -> SKIP (GTC does not expire)
        {
            "order_id": "ord-4",
            "tif": TimeInForce.GTC,
            "native_expiry_supported": False,
            "expiration_utc": expiry_past,
        },
    ]

    cancelled = mgr.run_expiry_watchdog(orders)
    assert cancelled == ["ord-1"]


def test_halt_and_resume_symbols() -> None:
    """Verify symbol halting sets updates correctly (TRD-FR-071)."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )

    mgr.halt_symbol("EURUSD")
    assert mgr.is_symbol_halted("EURUSD")

    mgr.resume_symbol("EURUSD")
    assert not mgr.is_symbol_halted("EURUSD")


def test_save_session_state() -> None:
    """Verify session save state writes snapshot to state store."""
    clock = MockClock(datetime.now(UTC))
    store = MockStateStore()
    mgr = SessionManager(
        scope="acct-1",
        route=TradingRoute.SIM,
        state_store=store,
        clock=clock,
    )
    mgr.start_session()
    mgr.halt_symbol("GBPUSD")

    snapshot_ref = mgr.save_session_state()
    assert snapshot_ref == "snap-ref-1"
    assert store.save_called == 1

    saved = store.data[(TradingRoute.SIM, "acct-1")]
    assert saved["mode"] == "normal"
    assert "GBPUSD" in saved["halted_symbols"]
