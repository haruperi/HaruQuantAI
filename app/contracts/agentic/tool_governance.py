"""Public contract for Agentic tool governance and typed human actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.contracts.agentic.mandate import FirmMandate
from app.contracts.workspace.models import ManageAccountsRequest


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    tool_id: str
    version: int
    receiver_capability: str
    request_schema: str
    result_schema: str
    permission_class: str
    side_effect_class: str
    environments: tuple[str, ...]
    egress_class: str
    idempotency_mode: str
    max_cost: Decimal
    timeout_seconds: float
    result_trust: str
    receiver_generation: int


@dataclass(frozen=True, slots=True)
class ToolLease:
    lease_id: str
    workspace_path: Path
    tool_id: str
    principal_id: str
    role_id: str
    account_id: str
    run_id: str
    request_hash: str
    receiver_generation: int
    environment: str
    max_cost: Decimal
    expires_at: datetime
    nonce: str
    policy_ref: str


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    lease: ToolLease
    mandate: FirmMandate
    asset_id: str
    session_request: ManageAccountsRequest
    payload: dict[str, object]
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_id: str
    payload: dict[str, object]
    observed_cost: Decimal | None
    trust_class: str
    provenance_ref: str


@dataclass(frozen=True, slots=True)
class HumanActionRequest:
    action_id: str
    workspace_path: Path
    account_id: str
    principal_id: str
    action_kind: str
    object_hash: str
    expires_at: datetime
    nonce: str


@dataclass(frozen=True, slots=True)
class HumanActionDecision:
    request: HumanActionRequest
    approved: bool
    decided_at: datetime


@runtime_checkable
class ToolReceiver(Protocol):
    async def invoke(self, payload: dict[str, object], *, idempotency_key: str) -> ToolResult: ...
    async def reconcile(self, idempotency_key: str) -> ToolResult | None: ...


@runtime_checkable
class ToolGovernanceCapability(Protocol):
    async def register_tool(self, descriptor: ToolDescriptor, receiver: ToolReceiver) -> str: ...
    async def issue_lease(self, lease: ToolLease, mandate: FirmMandate, asset_id: str) -> ToolLease: ...
    async def invoke(self, request: ToolInvocation) -> ToolResult: ...
    async def decide_human_action(self, decision: HumanActionDecision) -> HumanActionDecision: ...


__all__ = ["HumanActionDecision", "HumanActionRequest", "ToolDescriptor", "ToolGovernanceCapability", "ToolInvocation", "ToolLease", "ToolReceiver", "ToolResult"]
