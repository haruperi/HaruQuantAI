"""Structured governance events and decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .models import CircuitBreakerState, GovernanceState, OverrideRecord

Decision = Literal["ACCEPT", "REJECT"]
Severity = Literal["warning", "breach"]


@dataclass(frozen=True)
class LimitEvent:
    """Explainable governance event suitable for later persistence."""

    event_type: str
    rule_key: str
    severity: Severity
    message: str
    observed_value: float | None = None
    threshold_value: float | None = None
    unit: str | None = None
    scope: str = "portfolio"
    scope_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    """Structured result from the policy engine."""

    decision: Decision
    reason: str
    breaches: list[LimitEvent] = field(default_factory=list)
    warnings: list[LimitEvent] = field(default_factory=list)
    overrides: list[OverrideRecord] = field(default_factory=list)
    governance_state: GovernanceState | None = None
    circuit_breaker_state: CircuitBreakerState | None = None

    @property
    def policy_events(self) -> list[LimitEvent]:
        return [*self.breaches, *self.warnings]
