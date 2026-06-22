"""Live monitoring, health checks, and incident recording.

Tracks tool health, stale state, workflow timeouts, ingestion health,
latency, cost budget, and operational incidents for the live runtime.
All monitoring events are emitted as structured JSON-safe payloads.

Ownership:
    - Owns live monitoring state, health snapshots, incident records,
      cost-budget enforcement, workflow-timeout detection, and
      monitoring event emission.
    - Does NOT own dashboard rendering, websocket transport, or UI.

Public exports:
    LiveMonitor, LiveHealthSnapshot, check_live_readiness,
    record_live_incident, emit_live_monitoring_event.

Side effects:
    None on import. Monitoring occurs only when called explicitly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.utils.errors import ValidationError
from app.utils.logger import logger

# Severity levels for live incidents.
_VALID_SEVERITIES = frozenset({"info", "warning", "error", "critical"})

# Tool health state values.
_VALID_HEALTH_STATES = frozenset(
    {"healthy", "degraded", "failed", "unknown"}
)

# Consecutive failure thresholds for tool health degradation.
_DEGRADED_THRESHOLD = 3
_FAILED_THRESHOLD = 5

# Maximum latency samples retained in memory.
_MAX_LATENCY_SAMPLES = 1000


@dataclass
class ToolHealthRecord:
    """Health record for a single exported live tool.

    Attributes:
        tool_name: Stable tool identifier.
        health_state: Current health state.
        last_success_at: UTC timestamp of the last successful call.
        last_failure_at: UTC timestamp of the last failure.
        consecutive_failure_count: Count of consecutive failures since
            the last success.
        timeout_count: Total timeout count since startup.
        dependency_status: Optional map of dependency health states.
    """

    tool_name: str
    health_state: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    consecutive_failure_count: int = 0
    timeout_count: int = 0
    dependency_status: dict[str, str] = field(default_factory=dict)


@dataclass
class LiveHealthSnapshot:
    """Snapshot of the overall live system health.

    Attributes:
        snapshot_id: Unique identifier for this snapshot.
        captured_at: UTC timestamp of the snapshot.
        overall_health: ``'healthy'``, ``'degraded'``, ``'critical'``,
            or ``'unknown'``.
        live_enabled: Whether live mutation is enabled.
        live_mode: Current live mode rung.
        session_active: Whether a live session is active.
        stale_state_detected: Whether any context is stale.
        ingestion_healthy: Whether required live inputs are arriving.
        cost_budget_ok: Whether the cost budget has not been exceeded.
        workflow_timeout_detected: Whether any workflow has exceeded its
            configured timeout.
        tool_health: Map of tool_name → ``ToolHealthRecord``.
        active_incidents: List of active incident identifiers.
        readiness_blocks: Human-readable readiness block messages.
        latency_p99_ms: 99th-percentile gate latency, or ``None``.
    """

    snapshot_id: str
    captured_at: datetime
    overall_health: str
    live_enabled: bool
    live_mode: str
    session_active: bool
    stale_state_detected: bool
    ingestion_healthy: bool
    cost_budget_ok: bool
    workflow_timeout_detected: bool
    tool_health: dict[str, ToolHealthRecord]
    active_incidents: list[str]
    readiness_blocks: list[str]
    latency_p99_ms: float | None = None


@dataclass
class LiveIncidentRecord:
    """Immutable record of a classified live incident.

    Attributes:
        incident_id: Unique incident identifier.
        incident_type: Stable incident type code.
        severity: ``'info'``, ``'warning'``, ``'error'``, or
            ``'critical'``.
        recorded_at: UTC timestamp.
        description: Human-readable description (no secrets).
        action_required: Optional operator action hint.
        context: Additional structured context (redacted).
        request_id: Trace identifier.
        resolved: Whether the incident has been resolved.
    """

    incident_id: str
    incident_type: str
    severity: str
    recorded_at: datetime
    description: str
    action_required: str | None
    context: dict[str, Any]
    request_id: str | None
    resolved: bool = False


@dataclass
class _WorkflowRecord:
    """Internal record of a tracked live workflow.

    Attributes:
        workflow_id: Unique workflow identifier.
        started_at: UTC timestamp when the workflow started.
        timeout_seconds: Configured timeout for this workflow.
        action: The action being executed.
    """

    workflow_id: str
    started_at: datetime
    timeout_seconds: float
    action: str


class LiveMonitor:
    """Stateful live monitoring tracker for the live runtime.

    Tracks tool health, latency samples, cost accrual, ingestion
    status, stale state detection, workflow timeouts, and active
    incidents. All state is in-memory; a production implementation
    would flush to the approved persistence port.

    Usage::

        monitor = LiveMonitor(live_enabled=True, live_mode="shadow")
        monitor.record_tool_success("check_live_readiness")
        snapshot = monitor.get_health_snapshot()
    """

    def __init__(
        self,
        *,
        live_enabled: bool = False,
        live_mode: str = "package_only",
        cost_budget_usd: float | None = None,
        session_active: bool = False,
    ) -> None:
        """Initialise the live monitor.

        Args:
            live_enabled: Whether live mutation is enabled.
            live_mode: Current live mode rung.
            cost_budget_usd: Optional session cost ceiling in USD.
            session_active: Whether a live session is currently active.
        """
        self._live_enabled = live_enabled
        self._live_mode = live_mode
        self._cost_budget_usd = cost_budget_usd
        self._session_active = session_active

        self._tool_health: dict[str, ToolHealthRecord] = {}
        self._incidents: list[LiveIncidentRecord] = []
        self._latency_samples: list[float] = []
        self._cost_accrued_usd: float = 0.0
        self._cost_budget_exceeded: bool = False
        self._ingestion_healthy: bool = True
        self._stale_state_detected: bool = False
        self._workflow_timeout_detected: bool = False
        self._active_workflows: dict[str, _WorkflowRecord] = {}
        self._snapshot_counter: int = 0

        logger.info(
            "live_monitor.initialized live_enabled=%r "
            "live_mode=%r cost_budget_usd=%r",
            live_enabled,
            live_mode,
            cost_budget_usd,
        )

    # ── Tool health ───────────────────────────────────────────────────

    def record_tool_success(
        self,
        tool_name: str,
        *,
        latency_ms: float | None = None,
    ) -> None:
        """Record a successful tool call and update health state.

        Args:
            tool_name: Stable tool identifier.
            latency_ms: Optional call latency in milliseconds.
        """
        now = datetime.now(UTC)
        record = self._tool_health.get(tool_name)
        if record is None:
            record = ToolHealthRecord(
                tool_name=tool_name, health_state="healthy"
            )
        record.health_state = "healthy"
        record.last_success_at = now
        record.consecutive_failure_count = 0
        self._tool_health[tool_name] = record

        if latency_ms is not None:
            self._latency_samples.append(float(latency_ms))
            if len(self._latency_samples) > _MAX_LATENCY_SAMPLES:
                self._latency_samples = (
                    self._latency_samples[-_MAX_LATENCY_SAMPLES:]
                )

    def record_tool_failure(
        self,
        tool_name: str,
        *,
        is_timeout: bool = False,
        error_code: str | None = None,
    ) -> None:
        """Record a tool failure and update health state.

        Degrades health to ``'degraded'`` after
        ``_DEGRADED_THRESHOLD`` consecutive failures and to
        ``'failed'`` after ``_FAILED_THRESHOLD``.

        Args:
            tool_name: Stable tool identifier.
            is_timeout: Whether the failure was a timeout.
            error_code: Optional error code for diagnostic logging.
        """
        now = datetime.now(UTC)
        record = self._tool_health.get(tool_name)
        if record is None:
            record = ToolHealthRecord(
                tool_name=tool_name, health_state="unknown"
            )
        record.last_failure_at = now
        record.consecutive_failure_count += 1
        if is_timeout:
            record.timeout_count += 1
        if record.consecutive_failure_count >= _FAILED_THRESHOLD:
            record.health_state = "failed"
        elif record.consecutive_failure_count >= _DEGRADED_THRESHOLD:
            record.health_state = "degraded"
        self._tool_health[tool_name] = record

        if error_code:
            logger.warning(
                "live_monitor.tool_failure tool_name=%r "
                "is_timeout=%r error_code=%r consecutive=%r",
                tool_name,
                is_timeout,
                error_code,
                record.consecutive_failure_count,
            )

    # ── Cost budget ───────────────────────────────────────────────────

    def record_cost(self, amount_usd: float) -> bool:
        """Accrue cost and check against the configured budget.

        Returns ``False`` when accrual would exceed the budget. Live
        mutation must be blocked when this returns ``False``.

        Args:
            amount_usd: Cost to accrue in USD. Must be non-negative.

        Returns:
            ``True`` if the budget is within limits after accrual,
            ``False`` if the budget has been exceeded.

        Raises:
            ValidationError: If ``amount_usd`` is negative.
        """
        if amount_usd < 0:
            raise ValidationError(
                "amount_usd must be non-negative.", code="INVALID_INPUT"
            )
        self._cost_accrued_usd += amount_usd
        if (
            self._cost_budget_usd is not None
            and self._cost_accrued_usd > self._cost_budget_usd
        ):
            self._cost_budget_exceeded = True
            logger.warning(
                "live_monitor.cost_budget_exceeded "
                "accrued=%r budget=%r",
                self._cost_accrued_usd,
                self._cost_budget_usd,
            )
            return False
        return True

    # ── Ingestion and stale state ─────────────────────────────────────

    def set_ingestion_status(self, healthy: bool) -> None:
        """Update the ingestion health flag.

        Args:
            healthy: ``True`` when required live inputs are arriving.
        """
        self._ingestion_healthy = healthy

    def set_stale_state(self, detected: bool) -> None:
        """Update the stale-state detection flag.

        Args:
            detected: ``True`` when any live context is stale.
        """
        self._stale_state_detected = detected

    # ── Workflow timeout tracking ─────────────────────────────────────

    def register_workflow(
        self,
        *,
        workflow_id: str,
        action: str,
        timeout_seconds: float,
    ) -> None:
        """Register an active workflow for timeout monitoring.

        Args:
            workflow_id: Unique workflow identifier.
            action: Action being executed by the workflow.
            timeout_seconds: Maximum allowed duration in seconds.
        """
        self._active_workflows[workflow_id] = _WorkflowRecord(
            workflow_id=workflow_id,
            started_at=datetime.now(UTC),
            timeout_seconds=timeout_seconds,
            action=action,
        )

    def deregister_workflow(self, workflow_id: str) -> None:
        """Remove a workflow from the active tracking set.

        Args:
            workflow_id: Identifier of the completed workflow.
        """
        self._active_workflows.pop(workflow_id, None)

    def check_workflow_timeouts(self) -> list[str]:
        """Identify workflows that have exceeded their timeout.

        Updates the ``workflow_timeout_detected`` flag when any
        overdue workflow is found.

        Returns:
            List of ``workflow_id`` strings for timed-out workflows.
        """
        now = datetime.now(UTC)
        timed_out: list[str] = []
        for wf_id, wf in list(self._active_workflows.items()):
            elapsed = (now - wf.started_at).total_seconds()
            if elapsed > wf.timeout_seconds:
                timed_out.append(wf_id)
                logger.warning(
                    "live_monitor.workflow_timeout "
                    "workflow_id=%r action=%r elapsed=%.1f "
                    "timeout=%.1f",
                    wf_id,
                    wf.action,
                    elapsed,
                    wf.timeout_seconds,
                )
        if timed_out:
            self._workflow_timeout_detected = True
        return timed_out

    # ── Incidents ─────────────────────────────────────────────────────

    def add_incident(self, incident: LiveIncidentRecord) -> None:
        """Add a pre-built incident record to the incident log.

        Args:
            incident: Validated ``LiveIncidentRecord`` to append.
        """
        self._incidents.append(incident)

    # ── Health snapshot ───────────────────────────────────────────────

    def get_health_snapshot(self) -> LiveHealthSnapshot:
        """Build a full health snapshot of the current monitor state.

        Returns:
            ``LiveHealthSnapshot`` reflecting all current health
            signals.
        """
        self.check_workflow_timeouts()

        self._snapshot_counter += 1
        snapshot_id = f"snap_{self._snapshot_counter:06d}"
        now = datetime.now(UTC)

        cost_ok = not self._cost_budget_exceeded and (
            self._cost_budget_usd is None
            or self._cost_accrued_usd <= self._cost_budget_usd
        )

        failed_tools = [
            name
            for name, rec in self._tool_health.items()
            if rec.health_state == "failed"
        ]

        readiness_blocks: list[str] = []
        if not self._session_active:
            readiness_blocks.append("No active live session.")
        if self._stale_state_detected:
            readiness_blocks.append("Stale state detected.")
        if not self._ingestion_healthy:
            readiness_blocks.append("Live input ingestion is unhealthy.")
        if not cost_ok:
            readiness_blocks.append("Cost budget exceeded.")
        if self._workflow_timeout_detected:
            readiness_blocks.append(
                "One or more live workflows have exceeded timeout."
            )
        for ft in failed_tools:
            readiness_blocks.append(f"Tool '{ft}' is in failed state.")

        # Derive overall health from structured boolean flags —
        # never from substring-matching of human-readable messages.
        if not readiness_blocks:
            overall = "healthy"
        elif not cost_ok or bool(failed_tools):
            overall = "critical"
        else:
            overall = "degraded"

        active_incident_ids = [
            inc.incident_id
            for inc in self._incidents
            if not inc.resolved
        ]

        latency_p99: float | None = None
        if self._latency_samples:
            sorted_samples = sorted(self._latency_samples)
            p99_idx = min(
                int(len(sorted_samples) * 0.99),
                len(sorted_samples) - 1,
            )
            latency_p99 = sorted_samples[p99_idx]

        return LiveHealthSnapshot(
            snapshot_id=snapshot_id,
            captured_at=now,
            overall_health=overall,
            live_enabled=self._live_enabled,
            live_mode=self._live_mode,
            session_active=self._session_active,
            stale_state_detected=self._stale_state_detected,
            ingestion_healthy=self._ingestion_healthy,
            cost_budget_ok=cost_ok,
            workflow_timeout_detected=self._workflow_timeout_detected,
            tool_health=dict(self._tool_health),
            active_incidents=active_incident_ids,
            readiness_blocks=readiness_blocks,
            latency_p99_ms=latency_p99,
        )


# ---------------------------------------------------------------------------
# Module-level live monitoring functions
# ---------------------------------------------------------------------------


def check_live_readiness(
    *,
    monitor: LiveMonitor,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Check all live health gates and return a readiness envelope.

    Returns a standard readiness envelope indicating whether the live
    runtime is ready for broker mutation. Never overstates readiness
    when context is partial or stale.

    Args:
        monitor: Active ``LiveMonitor`` instance.
        request_id: Trace identifier.

    Returns:
        Dict with keys ``ready``, ``overall_health``,
        ``readiness_blocks``, ``snapshot_id``, ``active_incidents``,
        ``cost_budget_ok``, ``latency_p99_ms``, and ``request_id``.
    """
    snapshot = monitor.get_health_snapshot()
    ready = len(snapshot.readiness_blocks) == 0

    result: dict[str, Any] = {
        "ready": ready,
        "overall_health": snapshot.overall_health,
        "readiness_blocks": snapshot.readiness_blocks,
        "snapshot_id": snapshot.snapshot_id,
        "active_incidents": snapshot.active_incidents,
        "cost_budget_ok": snapshot.cost_budget_ok,
        "workflow_timeout_detected": snapshot.workflow_timeout_detected,
        "latency_p99_ms": snapshot.latency_p99_ms,
        "request_id": request_id,
    }

    logger.info(
        "live_monitor.readiness_check ready=%r "
        "overall_health=%r block_count=%r request_id=%r",
        ready,
        snapshot.overall_health,
        len(snapshot.readiness_blocks),
        request_id,
    )
    return result


def record_live_incident(
    *,
    monitor: LiveMonitor,
    incident_type: str,
    severity: str,
    description: str,
    action_required: str | None = None,
    context: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> LiveIncidentRecord:
    """Record a classified live incident in the monitor's incident log.

    Args:
        monitor: Active ``LiveMonitor`` instance.
        incident_type: Stable incident type code.
        severity: Incident severity — one of ``'info'``,
            ``'warning'``, ``'error'``, or ``'critical'``.
        description: Human-readable description (must not contain
            secrets).
        action_required: Optional operator action hint.
        context: Optional structured context (must not contain
            secrets).
        request_id: Trace identifier.

    Returns:
        ``LiveIncidentRecord`` with a unique incident ID, now appended
        to the monitor's incident log.

    Raises:
        ValidationError: If ``incident_type`` is empty or ``severity``
            is not one of the approved values.
    """
    if not isinstance(incident_type, str) or not incident_type.strip():
        raise ValidationError(
            "incident_type must be a non-empty string.",
            code="INVALID_INPUT",
        )
    if severity not in _VALID_SEVERITIES:
        raise ValidationError(
            f"severity must be one of {sorted(_VALID_SEVERITIES)}.",
            code="INVALID_INPUT",
        )

    now = datetime.now(UTC)
    digest = hashlib.sha256(
        f"{now.isoformat()}{incident_type}{request_id}".encode()
    ).hexdigest()[:10]
    incident_id = f"inc_{digest}"

    incident = LiveIncidentRecord(
        incident_id=incident_id,
        incident_type=incident_type.strip(),
        severity=severity,
        recorded_at=now,
        description=description,
        action_required=action_required,
        context=context or {},
        request_id=request_id,
    )
    # Use the public method to avoid accessing private state directly.
    monitor.add_incident(incident)

    logger.warning(
        "live_monitor.incident_recorded incident_id=%r "
        "incident_type=%r severity=%r request_id=%r",
        incident_id,
        incident.incident_type,
        severity,
        request_id,
    )
    return incident


def emit_live_monitoring_event(
    *,
    event_type: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """Emit a structured JSON-safe live monitoring event.

    Packages and returns a monitoring event envelope. In a production
    implementation this would publish to an approved event bus.
    Dashboard/UI rendering and websocket transport are strictly out of
    scope.

    Args:
        event_type: Stable event type identifier.
        payload: Structured event data (must be JSON-safe and
            redacted).
        request_id: Trace identifier.

    Returns:
        Structured monitoring event dict with ``event_type``,
        ``timestamp``, ``payload``, and ``request_id``.

    Raises:
        ValidationError: If ``event_type`` is empty.
    """
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValidationError(
            "event_type must be a non-empty string.",
            code="INVALID_INPUT",
        )

    event: dict[str, Any] = {
        "event_type": event_type.strip(),
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
        "request_id": request_id,
    }

    logger.info(
        "live_monitor.event_emitted event_type=%r request_id=%r",
        event_type,
        request_id,
    )
    return event
