"""Declare severity signals taxonomy, rate limiting, and escalation runbooks.

This module implements:
- Severity signal tiers (TRD-FR-173)
- Rate limiting and deduplication of incident alerts (TRD-FR-173)
- Confirmed runbook verification (TRD-FR-174)
- Escalation chain tracking for unacknowledged incidents (TRD-FR-173)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.services.trading.state.ports import Clock
from loguru import logger


@dataclass
class IncidentSignal:
    """Represents an operational monitoring incident signal."""

    incident_id: str
    incident_class: str
    severity: str
    message: str
    timestamp: datetime
    runbook_id: str
    acknowledged: bool = False
    escalation_step: int = 0


class OperationalSignalsManager:
    """Manages emission, rate limiting, and escalation of incident signals."""

    def __init__(
        self,
        runbook_registry: dict[str, str],
        escalation_chain: dict[str, list[str]],
        clock: Clock,
        rate_limit_seconds: float = 60.0,
    ) -> None:
        """Initialize the signals manager.

        Args:
            runbook_registry: Registry mapping incident class to runbook ID.
            escalation_chain: Escalation stages mapping severity to channels.
            clock: Clock source.
            rate_limit_seconds: Rate limit duration per incident class.
        """
        self._runbook_registry = runbook_registry
        self._escalation_chain = escalation_chain
        self._clock = clock
        self._rate_limit_seconds = rate_limit_seconds

        # Track last emission timestamp per incident class to prevent spamming
        self._last_emitted: dict[str, datetime] = {}
        # Track unacknowledged signals for escalation check
        self._active_incidents: dict[str, IncidentSignal] = {}
        # Audit log of all signals emitted
        self._audit_log: list[IncidentSignal] = []

    def emit_signal(
        self,
        incident_id: str,
        incident_class: str,
        severity: str,
        message: str,
    ) -> IncidentSignal | None:
        """Emit an operational signal with rate limiting and runbook lookup.

        Args:
            incident_id: Unique identifier for the incident instance.
            incident_class: Class of the incident (e.g. stale_order).
            severity: Severity tier ('info', 'warning', 'high', 'critical').
            message: Detail description text.

        Returns:
            IncidentSignal | None: The created signal if emitted, or None if
                rate-limited.
        """
        now = self._clock.now_utc()

        # Enforce rate-limiting/deduplication per incident class
        if incident_class in self._last_emitted:
            elapsed = (now - self._last_emitted[incident_class]).total_seconds()
            if elapsed < self._rate_limit_seconds:
                logger.info(
                    "Incident class {} rate-limited. Skipping emission.",
                    incident_class,
                )
                return None

        # Resolve runbook ID (TRD-FR-174)
        runbook_id = self._runbook_registry.get(incident_class, "")
        if not runbook_id:
            logger.warning(
                "Emitting incident class {} with no registered runbook ID.",
                incident_class,
            )
            # Emit a warning signal to alert about missing runbook definition
            # but still allow the original signal to carry a default runbook
            runbook_id = "RB-UNKNOWN-001"

        signal = IncidentSignal(
            incident_id=incident_id,
            incident_class=incident_class,
            severity=severity.lower(),
            message=message,
            timestamp=now,
            runbook_id=runbook_id,
        )

        self._last_emitted[incident_class] = now
        self._audit_log.append(signal)

        # Track high/critical for escalation chains
        if signal.severity in ("high", "critical"):
            self._active_incidents[incident_id] = signal

        logger.warning(
            "Emitted operational signal [{}]: {} (Runbook: {})",
            signal.severity.upper(),
            signal.message,
            signal.runbook_id,
        )
        return signal

    def acknowledge_incident(self, incident_id: str) -> bool:
        """Acknowledge a pending active incident, stopping the escalation chain.

        Args:
            incident_id: Incident identifier.

        Returns:
            bool: True if acknowledged, False if not found.
        """
        if incident_id in self._active_incidents:
            self._active_incidents[incident_id].acknowledged = True
            del self._active_incidents[incident_id]
            logger.info("Incident {} successfully acknowledged.", incident_id)
            return True
        return False

    def check_escalations(self, window_seconds: float = 60.0) -> list[dict[str, Any]]:
        """Scan active unacknowledged high/critical incidents for escalation.

        Args:
            window_seconds: Time interval threshold before next escalation step.

        Returns:
            list[dict[str, Any]]: Escalation actions triggered during this pass.
        """
        now = self._clock.now_utc()
        escalated_actions: list[dict[str, Any]] = []

        for incident_id, signal in list(self._active_incidents.items()):
            elapsed = (now - signal.timestamp).total_seconds()
            # If elapsed time exceeds window multiplied by current escalation step
            threshold = window_seconds * (signal.escalation_step + 1)

            if elapsed >= threshold:
                channels = self._escalation_chain.get(signal.severity, [])
                if signal.escalation_step < len(channels):
                    target_channel = channels[signal.escalation_step]
                    signal.escalation_step += 1
                    action = {
                        "incident_id": incident_id,
                        "severity": signal.severity,
                        "channel": target_channel,
                        "step": signal.escalation_step,
                        "timestamp": now,
                    }
                    escalated_actions.append(action)
                    logger.error(
                        "Incident {} escalated to step {} (Channel: {})",
                        incident_id,
                        signal.escalation_step,
                        target_channel,
                    )
                else:
                    # Chain fully exhausted
                    logger.critical(
                        "Incident {} escalation chain exhausted with no ack.",
                        incident_id,
                    )

        return escalated_actions

    @property
    def audit_log(self) -> list[IncidentSignal]:
        """Return full audit log.

        Returns:
            list[IncidentSignal]: Full signals audit log.
        """
        return self._audit_log
