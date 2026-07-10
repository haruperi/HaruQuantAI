"""Session manager coordinating runtime states, heartbeats, and watchdogs.

Implements TRD-FR-064 through TRD-FR-072.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, cast

from app.services.trading.contracts import (
    JsonObject,
    TimeInForce,
    TradingRoute,
)
from app.services.trading.gates.kill_switch import OperationalMode
from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.state.ports import Clock, TradingStateStore


class SessionState(StrEnum):
    """Session lifecycle states."""

    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    RECOVERING = "recovering"


class SessionManager:
    """Manages trading session states, reconnection resyncs, and failsafes."""

    _active_live_sessions: ClassVar[dict[str, SessionManager]] = {}
    _registry_lock = threading.Lock()

    def __init__(
        self,
        *,
        scope: str,
        route: TradingRoute,
        state_store: TradingStateStore,
        clock: Clock,
        signals_manager: object = None,
    ) -> None:
        """Initialize the session manager.

        Args:
            scope: Configured trading scope (e.g. account ID).
            route: Trading route (live, sim, paper, shadow).
            state_store: Injected trading state store snapshot port.
            clock: Injected clock dependency.
            signals_manager: Injected incident/signals manager.
        """
        self.scope = scope
        self.route = route
        self.state_store = state_store
        self.clock = clock
        self.signals_manager = signals_manager

        self._state = SessionState.STOPPED
        self._mode = OperationalMode.STOPPED

        # Halted symbols set (TRD-FR-071)
        self._halted_symbols: set[str] = set()
        self._halted_lock = threading.Lock()

        # Connection state monitoring (TRD-FR-072)
        self._connected = False
        self._reconciliation_required = False

        # Cancel-on-Disconnect (CoD) heartbeat tracking (TRD-FR-067)
        self.cod_supported = True
        self.cod_timeout_seconds = 10.0
        self.last_connection_heartbeat = 0.0

        # Synthetic emulation monitoring (TRD-FR-070)
        self.synthetic_emulation_enabled = False
        self.synthetic_emulation_risk_acknowledged = False
        self.synthetic_emulation_heartbeat_last_seen = 0.0
        self.synthetic_emulation_heartbeat_ttl = 5.0
        self.synthetic_emulation_active_orders: set[str] = set()

    @property
    def state(self) -> SessionState:
        """Return the current session state."""
        return self._state

    @property
    def mode(self) -> OperationalMode:
        """Return the current session operational mode."""
        return self._mode

    def start_session(self) -> None:
        """Start the trading session and restore persisted state.

        Tracked requirements: TRD-FR-064, TRD-FR-065.
        """
        logger.info("Starting trading session for scope: {}.", self.scope)

        # Enforce single active live session per scope (TRD-FR-065)
        if self.route is TradingRoute.LIVE:
            with SessionManager._registry_lock:
                if self.scope in SessionManager._active_live_sessions:
                    msg = f"Active live session already exists for scope: {self.scope}"
                    raise TradingValidationError(msg)
                SessionManager._active_live_sessions[self.scope] = self

        self._state = SessionState.STARTING
        self.last_connection_heartbeat = self.clock.monotonic()
        self.synthetic_emulation_heartbeat_last_seen = self.clock.monotonic()

        # Restore persisted state from TradingStateStore (TRD-FR-068)
        try:
            snapshot = self.state_store.load_state(
                route=self.route,
                tenant_id=self.scope,
                snapshot_id="session_state",
            )
            if snapshot is None:
                logger.info(
                    "No persisted session snapshot found. Initializing defaults."
                )
                self._mode = OperationalMode.NORMAL
            else:
                mode_val = snapshot.get("mode")
                if isinstance(mode_val, str):
                    self._mode = OperationalMode(mode_val)
                else:
                    self._mode = OperationalMode.NORMAL

                # Restore halted symbols
                restored_halts = snapshot.get("halted_symbols")
                if isinstance(restored_halts, list):
                    symbols = [str(s) for s in restored_halts]
                    with self._halted_lock:
                        self._halted_symbols = set(symbols)

            self._state = SessionState.RUNNING

        except Exception as exc:  # noqa: BLE001
            # Ambiguous/failed restoration blocks live mutations,
            # and fails closed to read_only (TRD-FR-068).
            logger.error(
                "Restoration of session state failed or is ambiguous: {}. "
                "Failing closed.",
                exc,
            )
            self._mode = OperationalMode.READ_ONLY
            self._state = SessionState.PAUSED
            if self.signals_manager and hasattr(self.signals_manager, "emit_signal"):
                err_msg = (
                    f"Session state restoration failed for scope {self.scope}: {exc}"
                )
                self.signals_manager.emit_signal(
                    incident_class="session_restoration_failed",
                    severity="CRITICAL",
                    message=err_msg,
                )

    def stop_session(self) -> None:
        """Stop the trading session."""
        logger.info("Stopping trading session for scope: {}.", self.scope)
        self._state = SessionState.STOPPED
        self._mode = OperationalMode.STOPPED

        if self.route is TradingRoute.LIVE:
            with SessionManager._registry_lock:
                SessionManager._active_live_sessions.pop(self.scope, None)

    def recover_session(
        self,
        *,
        has_unknown_broker_outcomes: bool,
        is_unreconciled: bool,
        missing_audit_logs: bool,
    ) -> None:
        """Execute session recovery checks (TRD-FR-066).

        Recovery logic must start the session in a paused state if unknown broker
        outcomes, unreconciled state, or missing audit logs are detected.
        """
        logger.info("Running session recovery logic for scope: {}.", self.scope)
        self._state = SessionState.RECOVERING

        if has_unknown_broker_outcomes or is_unreconciled or missing_audit_logs:
            logger.warning(
                "Recovery conditions failed: "
                "outcomes={}, unreconciled={}, missing_logs={}. "
                "Pausing session.",
                has_unknown_broker_outcomes,
                is_unreconciled,
                missing_audit_logs,
            )
            self._state = SessionState.PAUSED
        else:
            self._state = SessionState.RUNNING
            self._mode = OperationalMode.NORMAL

    def update_connection_state(self, connected: bool) -> None:
        """Update connection state and handle reconnection auto-resync (TRD-FR-072)."""
        if not self._connected and connected:
            # Reconnection detected (Disconnected -> Connected)
            logger.warning(
                "Broker connection re-established for scope {}. "
                "Blocking live mutations for resync.",
                self.scope,
            )
            self._reconciliation_required = True
            self._mode = OperationalMode.READ_ONLY
            self._state = SessionState.PAUSED

        self._connected = connected
        if connected:
            self.last_connection_heartbeat = self.clock.monotonic()

    def complete_reconciliation(self) -> None:
        """Mark connection reconciliation as completed and restore normal mode."""
        if self._reconciliation_required:
            logger.info("Reconnection reconciliation complete. Restoring NORMAL mode.")
            self._reconciliation_required = False
            self._mode = OperationalMode.NORMAL
            self._state = SessionState.RUNNING

    def check_cod_failsafe(self) -> bool:
        """Check Cancel-on-Disconnect heartbeat failsafe (TRD-FR-067).

        Returns:
            bool: True if failsafe triggered (emergency cancel-all required).
        """
        if self.cod_supported or self.route is not TradingRoute.LIVE:
            return False

        # If connection is disconnected or heartbeat elapsed exceeds limit
        elapsed = self.clock.monotonic() - self.last_connection_heartbeat
        if elapsed > self.cod_timeout_seconds:
            logger.critical(
                "Cancel-on-Disconnect heartbeat failsafe triggered: "
                "no heartbeat for {}s (limit {}s).",
                elapsed,
                self.cod_timeout_seconds,
            )
            self._mode = OperationalMode.EMERGENCY_FLATTEN
            return True
        return False

    def check_synthetic_emulation(
        self,
        *,
        active_orders: set[str],
        heartbeat_received: bool,
    ) -> None:
        """Track and monitor synthetic stop/OCO order heartbeats (TRD-FR-070)."""
        if not self.synthetic_emulation_enabled:
            return

        self.synthetic_emulation_active_orders = active_orders

        if heartbeat_received:
            self.synthetic_emulation_heartbeat_last_seen = self.clock.monotonic()

        # Emit dedicated operational signal if synthetic orders are active
        if (
            active_orders
            and self.signals_manager
            and hasattr(self.signals_manager, "emit_signal")
        ):
            sig_msg = f"Synthetic stop/OCO order monitoring is active: {active_orders}"
            self.signals_manager.emit_signal(
                incident_class="synthetic_orders_active",
                severity="WARNING",
                message=sig_msg,
            )

        # Check loop timeout
        elapsed = self.clock.monotonic() - self.synthetic_emulation_heartbeat_last_seen
        if elapsed > self.synthetic_emulation_heartbeat_ttl:
            logger.error(
                "Synthetic monitoring loop heartbeat elapsed: {}s. "
                "Transitioning to CLOSE_ONLY.",
                elapsed,
            )
            self._mode = OperationalMode.CLOSE_ONLY

    def run_expiry_watchdog(self, working_orders: list[JsonObject]) -> list[str]:
        """Cancel expired GTD/DAY working orders when native expiry is unsupported.

        Tracked requirements: TRD-FR-069.

        Args:
            working_orders: Active working orders list.

        Returns:
            list[str]: Order IDs cancelled by the watchdog.
        """
        cancelled_ids: list[str] = []
        now = self.clock.now_utc()

        for order in working_orders:
            tif = order.get("tif")
            if tif not in (TimeInForce.GTD, TimeInForce.DAY):
                continue

            # Check if broker lacks native expiry support for this profile/order
            native_expiry_supported = order.get("native_expiry_supported", True)
            if native_expiry_supported:
                continue

            expire_time_str = order.get("expiration_utc")
            if not isinstance(expire_time_str, str):
                continue

            try:
                expire_time = datetime.fromisoformat(expire_time_str)
                if expire_time.tzinfo is None:
                    expire_time = expire_time.replace(tzinfo=UTC)
            except ValueError:
                continue

            if now > expire_time:
                order_id = str(order.get("order_id", "unknown"))
                logger.warning(
                    "Expiry watchdog: Order {} (TIF={}) expired at {}. "
                    "Triggering cancellation.",
                    order_id,
                    tif,
                    expire_time,
                )
                cancelled_ids.append(order_id)

        return cancelled_ids

    # Real-time halts state set implementation (TRD-FR-071)
    def halt_symbol(self, symbol: str) -> None:
        """Add symbol to halted symbols set."""
        with self._halted_lock:
            self._halted_symbols.add(symbol)
            logger.info("Symbol {} halted.", symbol)

    def resume_symbol(self, symbol: str) -> None:
        """Remove symbol from halted symbols set."""
        with self._halted_lock:
            self._halted_symbols.discard(symbol)
            logger.info("Symbol {} resumed.", symbol)

    def is_symbol_halted(self, symbol: str) -> bool:
        """Return True if symbol is currently halted."""
        with self._halted_lock:
            return symbol in self._halted_symbols

    def save_session_state(self) -> str:
        """Persist current session state to TradingStateStore.

        Returns:
            str: Persisted snapshot reference.
        """
        with self._halted_lock:
            halts_list = list(self._halted_symbols)

        snapshot = cast(
            "JsonObject",
            {
                "mode": self._mode.value,
                "halted_symbols": halts_list,
            },
        )
        return self.state_store.save_state(
            route=self.route,
            tenant_id=self.scope,
            snapshot=snapshot,
            expected_version=None,
        )
