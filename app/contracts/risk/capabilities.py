"""Risk domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.risk.ports import (
        AuditRiskDecisionsCapability,
        CalculateRiskCapability,
        ControlKillSwitchCapability,
        DefineRiskContractsCapability,
        GovernAdmissionCapability,
        GovernAllocationsCapability,
        ManageApprovalsCapability,
    )

DEFINE_RISK_CONTRACTS_CAPABILITY: CapabilityKey[DefineRiskContractsCapability] = (
    CapabilityKey(
        name="risk.define-risk-contracts",
        major=1,
    )
)

CALCULATE_RISK_CAPABILITY: CapabilityKey[CalculateRiskCapability] = CapabilityKey(
    name="risk.calculate-risk",
    major=1,
)

CONTROL_KILL_SWITCH_CAPABILITY: CapabilityKey[ControlKillSwitchCapability] = (
    CapabilityKey(
        name="risk.control-kill-switch",
        major=1,
    )
)

GOVERN_ADMISSION_CAPABILITY: CapabilityKey[GovernAdmissionCapability] = CapabilityKey(
    name="risk.govern-admission",
    major=1,
)

MANAGE_APPROVALS_CAPABILITY: CapabilityKey[ManageApprovalsCapability] = CapabilityKey(
    name="risk.manage-approvals",
    major=1,
)

GOVERN_ALLOCATIONS_CAPABILITY: CapabilityKey[GovernAllocationsCapability] = (
    CapabilityKey(
        name="risk.govern-allocations",
        major=1,
    )
)

AUDIT_RISK_DECISIONS_CAPABILITY: CapabilityKey[AuditRiskDecisionsCapability] = (
    CapabilityKey(
        name="risk.audit-risk-decisions",
        major=1,
    )
)
