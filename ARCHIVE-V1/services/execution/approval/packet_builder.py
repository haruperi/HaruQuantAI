"""Approval packet builder helper.

Classes and functions:
    ApprovalPacketBuilder: Class. Provides ApprovalPacketBuilder behavior for execution workflows.
"""

from __future__ import annotations

from typing import Any

from app.services.execution.approval.models import ApprovalPacket, RiskClass


class ApprovalPacketBuilder:
    """Fluent builder for ApprovalPacket."""

    def __init__(self) -> None:
        self._action = ""
        self._reason = ""
        self._evidence: list[dict[str, Any]] = []
        self._confidence = 0.0
        self._uncertainty: dict[str, str] = {}
        self._policy_checks: list[str] = []
        self._risk_class = RiskClass.C
        self._alternatives: list[str] = []
        self._impact: dict[str, Any] = {}
        self._rollback = ""
        self._escalation: list[str] = []

    def action(self, value: str) -> ApprovalPacketBuilder:
        """Perform the action execution service operation."""
        self._action = value
        return self

    def reason(self, value: str) -> ApprovalPacketBuilder:
        """Perform the reason execution service operation."""
        self._reason = value
        return self

    def evidence(self, items: list[dict[str, Any]]) -> ApprovalPacketBuilder:
        """Perform the evidence execution service operation."""
        self._evidence = list(items)
        return self

    def confidence(self, value: float) -> ApprovalPacketBuilder:
        """Perform the confidence execution service operation."""
        self._confidence = value
        return self

    def uncertainty(self, items: dict[str, str]) -> ApprovalPacketBuilder:
        """Perform the uncertainty execution service operation."""
        self._uncertainty = dict(items)
        return self

    def policy_checks(self, items: list[str]) -> ApprovalPacketBuilder:
        """Perform the policy_checks execution service operation."""
        self._policy_checks = list(items)
        return self

    def risk_class(self, value: RiskClass) -> ApprovalPacketBuilder:
        """Perform the risk_class execution service operation."""
        self._risk_class = value
        return self

    def alternatives(self, items: list[str]) -> ApprovalPacketBuilder:
        """Perform the alternatives execution service operation."""
        self._alternatives = list(items)
        return self

    def expected_impact(self, value: dict[str, Any]) -> ApprovalPacketBuilder:
        """Perform the expected_impact execution service operation."""
        self._impact = dict(value)
        return self

    def rollback_plan(self, value: str) -> ApprovalPacketBuilder:
        """Perform the rollback_plan execution service operation."""
        self._rollback = value
        return self

    def escalation_triggers(self, items: list[str]) -> ApprovalPacketBuilder:
        """Perform the escalation_triggers execution service operation."""
        self._escalation = list(items)
        return self

    def build(self) -> ApprovalPacket:
        """Perform the build execution service operation."""
        return ApprovalPacket(
            action=self._action,
            reason=self._reason,
            evidence=self._evidence,
            confidence=self._confidence,
            uncertainty=self._uncertainty,
            policy_checks_passed=self._policy_checks,
            risk_class=self._risk_class,
            alternatives_considered=self._alternatives,
            expected_impact=self._impact,
            rollback_plan=self._rollback,
            escalation_triggers=self._escalation,
        )

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ApprovalPacketBuilder:
        """Create builder from dictionary."""
        b = ApprovalPacketBuilder()
        b.action(data.get("action", ""))
        b.reason(data.get("reason", ""))
        b.evidence(data.get("evidence", []))
        b.confidence(float(data.get("confidence", 0.0)))
        b.uncertainty(data.get("uncertainty", {}))
        b.policy_checks(data.get("policy_checks_passed", []))
        risk = data.get("risk_class", "C")
        b.risk_class(RiskClass(risk))
        b.alternatives(data.get("alternatives_considered", []))
        b.expected_impact(data.get("expected_impact", {}))
        b.rollback_plan(data.get("rollback_plan", ""))
        b.escalation_triggers(data.get("escalation_triggers", []))
        return b
