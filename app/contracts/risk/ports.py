"""Public capability protocols (ports) for Risk capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.risk.errors import RiskFailure
    from app.contracts.risk.models import (
        AuditRiskDecisionsRequest,
        AuditRiskDecisionsSuccess,
        CalculateRiskRequest,
        CalculateRiskSuccess,
        ControlKillSwitchRequest,
        ControlKillSwitchSuccess,
        DefineRiskContractsRequest,
        DefineRiskContractsSuccess,
        GovernAdmissionRequest,
        GovernAdmissionSuccess,
        GovernAllocationsRequest,
        GovernAllocationsSuccess,
        ManageApprovalsRequest,
        ManageApprovalsSuccess,
    )


@runtime_checkable
class DefineRiskContractsCapability(Protocol):
    """Capability protocol for risk profile, mandate, and evidence contracts."""

    async def define_risk_contracts(
        self,
        request: DefineRiskContractsRequest,
    ) -> DefineRiskContractsSuccess | RiskFailure:
        """Define and validate risk profiles, mandates, and evidence.

        Args:
            request: Operation-discriminated profile, mandate, and
                evidence request.

        Returns:
            The declared profile or mandate version, or the validated
            evidence reference on success, otherwise a structured risk
            failure.
        """
        ...


@runtime_checkable
class CalculateRiskCapability(Protocol):
    """Capability protocol for snapshot, sizing, stop, and scenario risk."""

    async def calculate_risk(
        self,
        request: CalculateRiskRequest,
    ) -> CalculateRiskSuccess | RiskFailure:
        """Calculate current-state risk snapshots and bounded sizing.

        Args:
            request: Operation-discriminated snapshot, sizing, stop,
                scenario, and report request.

        Returns:
            The snapshot, sizing recommendation, stop assessment,
            scenario result, or report artifact identity on success,
            otherwise a structured risk failure.
        """
        ...


@runtime_checkable
class ControlKillSwitchCapability(Protocol):
    """Capability protocol for kill-switch authority and recovery."""

    async def control_kill_switch(
        self,
        request: ControlKillSwitchRequest,
    ) -> ControlKillSwitchSuccess | RiskFailure:
        """Check, activate, clear, and recover hierarchical kill scopes.

        Args:
            request: Operation-discriminated kill-switch command and
                check request.

        Returns:
            The current kill-switch state or the recorded transition on
            success, otherwise a structured risk failure.
        """
        ...


@runtime_checkable
class GovernAdmissionCapability(Protocol):
    """Capability protocol for proposed-action admission and governor."""

    async def govern_admission(
        self,
        request: GovernAdmissionRequest,
    ) -> GovernAdmissionSuccess | RiskFailure:
        """Bind proposed actions and return deterministic decisions.

        Args:
            request: Operation-discriminated admission and governor
                request.

        Returns:
            The bound action, canonical risk decision, or typed NO_TRADE
            outcome on success, otherwise a structured risk failure. The
            governor never mutates Trading or Broker state and its
            recommendations are never execution authority.
        """
        ...


@runtime_checkable
class ManageApprovalsCapability(Protocol):
    """Capability protocol for human approval and token lifecycle."""

    async def manage_approvals(
        self,
        request: ManageApprovalsRequest,
    ) -> ManageApprovalsSuccess | RiskFailure:
        """Bind human approval requests and signed token lifecycle.

        Args:
            request: Operation-discriminated approval and token lifecycle
                request.

        Returns:
            The bound approval request or the issued, consumed, or
            revoked token on success, otherwise a structured risk
            failure.
        """
        ...


@runtime_checkable
class GovernAllocationsCapability(Protocol):
    """Capability protocol for capacity, eligibility, and allocations."""

    async def govern_allocations(
        self,
        request: GovernAllocationsRequest,
    ) -> GovernAllocationsSuccess | RiskFailure:
        """Reserve capacity and govern strategy and portfolio budgets.

        Args:
            request: Operation-discriminated capacity and allocation
                governance request.

        Returns:
            The reservation, allocation review, or authoritative budget on
            success, otherwise a structured risk failure.
        """
        ...


@runtime_checkable
class AuditRiskDecisionsCapability(Protocol):
    """Capability protocol for hash-chained risk audit records."""

    async def audit_risk_decisions(
        self,
        request: AuditRiskDecisionsRequest,
    ) -> AuditRiskDecisionsSuccess | RiskFailure:
        """Append, verify, and export the tamper-evident audit chain.

        Args:
            request: Operation-discriminated audit-chain request.

        Returns:
            The appended record or the chain verification verdict on
            success, otherwise a structured risk failure.
        """
        ...
