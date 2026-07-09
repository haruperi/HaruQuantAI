"""Monitoring and Health Coordination Service.

This module implements:
- Aggregated status metrics collection (TRD-FR-167)
- Multi-trigger automatic operational circuit breakers (TRD-FR-168)
- Dynamic latency route capability downgrades and recovery (TRD-FR-169)
"""

from collections import deque
from datetime import datetime
from typing import Any, Literal

from loguru import logger

from app.services.trading.config.models import TradingRuntimeConfig
from app.services.trading.contracts import TradingRoute
from app.services.trading.monitoring.heartbeat_watchdog import HeartbeatEmitter
from app.services.trading.monitoring.operational_signals import (
    OperationalSignalsManager,
)
from app.services.trading.monitoring.timeouts_and_staleness import (
    LatencyTracker,
    LostOrderWatchdog,
    ReconciliationService,
)
from app.services.trading.monitoring.tool_health import ToolHealthMonitor
from app.services.trading.state.ports import Clock


class MonitoringService:
    """Coordinates trading health monitoring, heartbeats, and circuit breakers."""

    def __init__(
        self,
        config: TradingRuntimeConfig,
        clock: Clock,
        signals_manager: OperationalSignalsManager,
        heartbeat_emitter: HeartbeatEmitter | None = None,
    ) -> None:
        """Initialize the monitoring service.

        Args:
            config: Active trading runtime configuration.
            clock: Injected clock source.
            signals_manager: Manager for alerts and escalation runbooks.
            heartbeat_emitter: Heartbeat emitter (dead man's switch).
        """
        self._config = config
        self._clock = clock
        self._signals_manager = signals_manager
        self._heartbeat_emitter = heartbeat_emitter

        # Sub-trackers
        m_cfg = config.monitoring
        self._latency_tracker = LatencyTracker(max_samples=m_cfg.latency_window_samples)
        self._lost_order_watchdog = LostOrderWatchdog(
            life_to_live_seconds=m_cfg.life_to_live_seconds,
            clock=clock,
        )
        self._tool_health_monitor = ToolHealthMonitor(
            failure_threshold=m_cfg.tool_health_consecutive_failures_limit
        )

        # Operational status state
        self._circuit_breaker_tripped = False
        self._circuit_breaker_reason = ""
        self._current_capability: Literal["full_live", "micro_live", "read_only"] = (
            "full_live"
        )

        # Circuit breaker trigger counters
        self._consecutive_rejects = 0
        self._unknown_outcomes: deque[datetime] = deque(
            maxlen=m_cfg.unknown_outcomes_limit * 2
        )

        # Latency downgrade state
        self._high_latency_started_at: datetime | None = None
        self._last_evaluated_p95: float = 0.0

        # Operational metrics audit
        self._total_rejects = 0
        self._total_unknown_outcomes = 0
        self._total_stream_gaps = 0
        self._total_durability_failures = 0

    def record_broker_success(self, latency_ms: float) -> None:
        """Record a successful broker action, updating health metrics.

        Args:
            latency_ms: Action execution latency in milliseconds.
        """
        self._consecutive_rejects = 0
        self._latency_tracker.record_latency(latency_ms)
        self._tool_health_monitor.record_success()
        self._evaluate_latency_downgrade()

    def record_broker_reject(self) -> None:
        """Record a broker command rejection.

        Increments consecutive count and evaluates the rejects circuit breaker.
        """
        self._consecutive_rejects += 1
        self._total_rejects += 1

        limit = self._config.monitoring.consecutive_rejects_limit
        if self._consecutive_failures_breached():
            self._trip_circuit_breaker(
                f"Consecutive broker rejects ({self._consecutive_rejects}) "
                f"exceeded limit ({limit})."
            )

    def record_unknown_outcome(self) -> None:
        """Record a transaction resulting in an unknown outcome.

        Updates rolling window queue and evaluates unknown outcomes breaker.
        """
        now = self._clock.now_utc()
        self._unknown_outcomes.append(now)
        self._total_unknown_outcomes += 1
        self._tool_health_monitor.record_failure("Unknown outcome encountered.")

        # Filter outcomes in rolling window
        m_cfg = self._config.monitoring
        window = m_cfg.unknown_outcomes_window_seconds
        outcomes_in_window = [
            t for t in self._unknown_outcomes if (now - t).total_seconds() <= window
        ]

        if len(outcomes_in_window) >= m_cfg.unknown_outcomes_limit:
            self._trip_circuit_breaker(
                f"Unknown outcomes count ({len(outcomes_in_window)}) in rolling "
                f"window ({window}s) exceeded limit ({m_cfg.unknown_outcomes_limit})."
            )

    def record_reconciliation_mismatch(self, details: str = "") -> None:
        """Record a reconciliation state mismatch breach.

        Trips the circuit breaker immediately.

        Args:
            details: Error mismatch description details.
        """
        self._trip_circuit_breaker(f"Reconciliation drift limits exceeded: {details}")

    def record_stream_gap(self) -> None:
        """Record a stream or sequence gap incident.

        Trips the circuit breaker immediately.
        """
        self._total_stream_gaps += 1
        self._trip_circuit_breaker("Execution event stream or sequence gap detected.")

    def record_durability_failure(self) -> None:
        """Record a persistence or audit write durability failure.

        Trips the circuit breaker immediately.
        """
        self._total_durability_failures += 1
        self._trip_circuit_breaker("Audit sink or trade store durability failure.")

    def run_stale_order_check(
        self,
        active_orders: list[dict[str, Any]],
        reconciliation_service: ReconciliationService,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
    ) -> list[str]:
        """Verify active orders for staleness and transition status.

        Args:
            active_orders: Working orders representation list.
            reconciliation_service: Sync service.
            route: Action route context.
            tenant_id: Tenant ID.
            account_id: Account ID.

        Returns:
            list[str]: Stale tickets.
        """
        return self._lost_order_watchdog.check_stale_orders(
            active_orders=active_orders,
            reconciliation_service=reconciliation_service,
            route=route,
            tenant_id=tenant_id,
            account_id=account_id,
        )

    def run_heartbeat_cycle(self) -> bool:
        """Trigger dead man's switch heartbeat emission to external node.

        Returns:
            bool: True if heartbeat successfully emitted.
        """
        if self._heartbeat_emitter is not None:
            # Emit heartbeat with current circuit breaker status
            status = "FAILED" if self._circuit_breaker_tripped else "HEALTHY"
            success = self._heartbeat_emitter.send_heartbeat(status=status)
            if not success:
                self._signals_manager.emit_signal(
                    incident_id=f"hb-fail-{int(self._clock.now_utc().timestamp())}",
                    incident_class="heartbeat_failure",
                    severity="warning",
                    message="External heartbeat emission failed.",
                )
            return success
        return False

    def reset_circuit_breaker(self) -> None:
        """Reset operational circuit breaker and reset counts."""
        if self._circuit_breaker_tripped:
            logger.info("Resetting operational circuit breaker.")
        self._circuit_breaker_tripped = False
        self._circuit_breaker_reason = ""
        self._consecutive_rejects = 0
        self._unknown_outcomes.clear()

    def get_monitoring_status(self) -> dict[str, Any]:
        """Aggregate status metrics into a structured health status event.

        Collects tool health status, timeouts, stale states, and
        latency metrics.

        Returns:
            dict[str, Any]: Aggregated health metrics mapping.
        """
        p95 = self._latency_tracker.get_p95_latency()
        return {
            "timestamp": self._clock.now_utc().isoformat(),
            "circuit_breaker_tripped": self._circuit_breaker_tripped,
            "circuit_breaker_reason": self._circuit_breaker_reason,
            "tool_health_status": self._tool_health_monitor.status,
            "current_capability": self._current_capability,
            "metrics": {
                "consecutive_rejects": self._consecutive_rejects,
                "unknown_outcomes_rolling": len(self._unknown_outcomes),
                "p95_latency_ms": p95,
                "total_rejects": self._total_rejects,
                "total_unknown_outcomes": self._total_unknown_outcomes,
                "total_stream_gaps": self._total_stream_gaps,
                "total_durability_failures": self._total_durability_failures,
            },
        }

    def _consecutive_failures_breached(self) -> bool:
        """Check if consecutive broker rejects count has breached limits.

        Returns:
            bool: True if breached.
        """
        limit = self._config.monitoring.consecutive_rejects_limit
        return self._consecutive_rejects >= limit

    def _trip_circuit_breaker(self, reason: str) -> None:
        """Trip operational circuit breaker and alert operator.

        Args:
            reason: Description of the trigger event.
        """
        if not self._circuit_breaker_tripped:
            self._circuit_breaker_tripped = True
            self._circuit_breaker_reason = reason
            logger.critical("CIRCUIT BREAKER TRIPPED: {}", reason)

            # Emit a critical level alert signal with operator runbook ID
            self._signals_manager.emit_signal(
                incident_id=f"cb-{int(self._clock.now_utc().timestamp())}",
                incident_class="circuit_breaker",
                severity="critical",
                message=reason,
            )

    def _evaluate_latency_downgrade(self) -> None:
        """Evaluate broker execution p95 latency for dynamic capability changes.

        Downgrades session capability to micro_live or read_only if p95
        persistently exceeds limit. Restores when p95 falls below limit.
        """
        p95 = self._latency_tracker.get_p95_latency()
        self._last_evaluated_p95 = p95
        m_cfg = self._config.monitoring
        limit = m_cfg.latency_p95_limit_ms
        now = self._clock.now_utc()

        if p95 > limit:
            if self._high_latency_started_at is None:
                self._high_latency_started_at = now
            else:
                elapsed = (now - self._high_latency_started_at).total_seconds()
                if (
                    elapsed >= m_cfg.latency_downgrade_duration_seconds
                    and self._current_capability == "full_live"
                ):
                    # Exceeded latency threshold duration: Downgrade routes
                    self._current_capability = "micro_live"
                    logger.warning(
                        "P95 execution latency ({:.2f}ms) exceeded threshold "
                        "({:.2f}ms) for {}s. Downgrading to micro_live.",
                        p95,
                        limit,
                        elapsed,
                    )
                    self._signals_manager.emit_signal(
                        incident_id=f"lat-down-{int(now.timestamp())}",
                        incident_class="latency_downgrade",
                        severity="high",
                        message=(
                            f"Execution latency high ({p95:.1f}ms). "
                            "Route downgraded."
                        ),
                    )
        else:
            # Latency recovered or stayed within bounds
            self._high_latency_started_at = None
            if self._current_capability != "full_live":
                logger.info(
                    "P95 execution latency ({:.2f}ms) stabilized. "
                    "Restoring capability to full_live.",
                    p95,
                )
                self._current_capability = "full_live"

    @property
    def circuit_breaker_tripped(self) -> bool:
        """Check if circuit breaker is tripped.

        Returns:
            bool: True if tripped.
        """
        return self._circuit_breaker_tripped

    @property
    def current_capability(self) -> str:
        """Get current route execution capability.

        Returns:
            str: "full_live", "micro_live", or "read_only".
        """
        return self._current_capability
