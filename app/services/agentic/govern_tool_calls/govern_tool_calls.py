"""Agentic tool registration, leases, invocation enforcement, and result filtering."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import re

from app.contracts.agentic.mandate import BudgetEnvelope, CheckMandateScopeRequest, MandateCapability, MandateOutcome
from app.contracts.agentic.operations import AgenticOperationsCapability, ReadinessQuery, ReadinessStatus
from app.contracts.agentic.roles import RoleEligibilityRequest, RolesCapability
from app.contracts.agentic.tool_governance import HumanActionDecision, ToolDescriptor, ToolInvocation, ToolLease, ToolReceiver, ToolResult
from app.contracts.orchestration.resources import AdmissionStatus, FiniteResourceProfile, ResourceAdmissionPort, ResourceAdmissionRequest
from app.contracts.workspace.manage_accounts import ManageAccountsCapability
from app.contracts.workspace.models import ManageAccountsSuccess

_FORBIDDEN = {"broker_credentials", "order_construction", "order_execution", "risk_approval", "kill_switch_clear", "live_deployment", "unrestricted_shell", "receiver_authority", "receiver_bypass"}
_SECRET = re.compile(r"(?i)(authorization|password|secret|token|api[_-]?key)")


class GovernToolCallsService:
    """Fail-closed mediation layer; denied calls never reach receivers."""

    def __init__(self, mandate: MandateCapability, roles: RolesCapability, operations: AgenticOperationsCapability, accounts: ManageAccountsCapability, resources: ResourceAdmissionPort, max_result_bytes: int) -> None:
        self._mandate = mandate; self._roles = roles; self._operations = operations; self._accounts = accounts; self._resources = resources; self._max = max_result_bytes
        self._tools: dict[str, tuple[ToolDescriptor, ToolReceiver, str]] = {}; self._leases: dict[str, ToolLease] = {}; self._used_nonces: set[str] = set(); self._human: dict[str, HumanActionDecision] = {}; self._closed = False

    async def register_tool(self, descriptor: ToolDescriptor, receiver: ToolReceiver) -> str:
        self._ensure_open()
        if descriptor.version < 1 or descriptor.receiver_generation < 1 or descriptor.side_effect_class in _FORBIDDEN or descriptor.permission_class in _FORBIDDEN:
            raise ValueError("AGENTIC_TOOL_STRUCTURALLY_FORBIDDEN")
        if not descriptor.max_cost.is_finite() or descriptor.max_cost < 0 or descriptor.timeout_seconds <= 0:
            raise ValueError("AGENTIC_TOOL_LIMIT_INVALID")
        digest = hashlib.sha256(json.dumps({"tool_id":descriptor.tool_id,"version":descriptor.version,"receiver":descriptor.receiver_capability,"request_schema":descriptor.request_schema,"result_schema":descriptor.result_schema,"permission":descriptor.permission_class,"side_effect":descriptor.side_effect_class,"environments":descriptor.environments,"egress":descriptor.egress_class,"idempotency":descriptor.idempotency_mode,"max_cost":str(descriptor.max_cost),"timeout":descriptor.timeout_seconds,"trust":descriptor.result_trust,"generation":descriptor.receiver_generation}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        existing = self._tools.get(descriptor.tool_id)
        if existing is not None and existing[2] != digest: raise ValueError("AGENTIC_TOOL_IDENTITY_CONFLICT")
        self._tools[descriptor.tool_id] = (descriptor, receiver, digest); return digest

    async def issue_lease(self, lease: ToolLease, mandate: object, asset_id: str) -> ToolLease:
        self._ensure_open(); descriptor = self._descriptor(lease.tool_id)
        if lease.expires_at.tzinfo is None or datetime.now(timezone.utc) >= lease.expires_at: raise PermissionError("TOOL_LEASE_EXPIRED")
        if lease.receiver_generation != descriptor.receiver_generation or lease.environment not in descriptor.environments or lease.max_cost > descriptor.max_cost or not lease.max_cost.is_finite(): raise PermissionError("TOOL_LEASE_SCOPE_DENIED")
        zero = BudgetEnvelope(0,0,0,1,lease.max_cost)
        decision = await self._mandate.enforce_mandate(CheckMandateScopeRequest(mandate, "FEAT-AGT-GOVERN_TOOL_CALLS", lease.role_id, lease.environment, lease.account_id, asset_id, zero))
        if getattr(decision, "outcome", None) is not MandateOutcome.ALLOWED: raise PermissionError("TOOL_MANDATE_DENIED")
        if lease.nonce in self._used_nonces: raise PermissionError("TOOL_NONCE_REPLAY")
        self._leases[lease.lease_id] = lease; return lease

    async def invoke(self, request: ToolInvocation) -> ToolResult:
        self._ensure_open(); lease = request.lease; descriptor, receiver, _digest = self._tools.get(lease.tool_id, (None, None, None))
        if descriptor is None or receiver is None or self._leases.get(lease.lease_id) != lease: raise PermissionError("TOOL_LEASE_UNKNOWN")
        if datetime.now(timezone.utc) >= lease.expires_at or lease.nonce in self._used_nonces: raise PermissionError("TOOL_LEASE_EXPIRED_OR_USED")
        payload_hash = hashlib.sha256(json.dumps(request.payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
        if payload_hash != lease.request_hash or descriptor.receiver_generation != lease.receiver_generation: raise PermissionError("TOOL_REQUEST_OR_GENERATION_STALE")
        session = await self._accounts.manage_accounts(request.session_request)
        if not isinstance(session, ManageAccountsSuccess) or request.session_request.operation != "ME" or request.session_request.account_id != lease.account_id: raise PermissionError("TOOL_SESSION_NOT_CURRENT")
        role = await self._roles.resolve_role(RoleEligibilityRequest(lease.role_id, request.mandate, "FEAT-AGT-GOVERN_TOOL_CALLS", lease.environment, lease.account_id, request.asset_id, datetime.now(timezone.utc)))
        if not role.eligible: raise PermissionError("TOOL_ROLE_NOT_ELIGIBLE")
        readiness = await self._operations.readiness(ReadinessQuery(lease.workspace_path, lease.account_id))
        if readiness.status is not ReadinessStatus.READY: raise PermissionError("TOOL_AGENTIC_NOT_READY")
        admission = await self._resources.admit(ResourceAdmissionRequest(request_id="tool:"+lease.lease_id, owner_id="FEAT-AGT-GOVERN_TOOL_CALLS", work_id=lease.run_id, idempotency_key="tool:"+request.idempotency_key, profile=FiniteResourceProfile(memory_bytes=min(self._max, 1024*1024))))
        if admission.status is not AdmissionStatus.ADMITTED or admission.lease is None: raise PermissionError("TOOL_RESOURCE_NOT_ADMITTED")
        try:
            self._used_nonces.add(lease.nonce)
            try:
                result = await receiver.invoke(request.payload, idempotency_key=request.idempotency_key)
            except Exception:
                reconciled = await receiver.reconcile(request.idempotency_key)
                if reconciled is None: raise
                result = reconciled
            return self._filter(descriptor, result, lease)
        finally:
            await self._resources.release(admission.lease.lease_id, admission.lease.generation)

    async def decide_human_action(self, decision: HumanActionDecision) -> HumanActionDecision:
        self._ensure_open(); request = decision.request
        if request.expires_at.tzinfo is None or decision.decided_at.tzinfo is None or decision.decided_at >= request.expires_at: raise ValueError("HUMAN_ACTION_EXPIRED")
        if request.nonce in self._used_nonces: raise ValueError("HUMAN_ACTION_NONCE_REPLAY")
        prior = self._human.get(request.action_id)
        if prior is not None and prior != decision: raise ValueError("HUMAN_ACTION_CONFLICT")
        self._used_nonces.add(request.nonce); self._human[request.action_id] = decision; return decision

    def _filter(self, descriptor: ToolDescriptor, result: ToolResult, lease: ToolLease) -> ToolResult:
        if result.tool_id != descriptor.tool_id: raise ValueError("TOOL_RESULT_IDENTITY_INVALID")
        encoded = json.dumps(result.payload, default=str).encode()
        if len(encoded) > self._max: raise ValueError("TOOL_RESULT_OVERSIZED")
        if any(_SECRET.search(str(key)) for key in result.payload): raise ValueError("TOOL_RESULT_SECRET_BEARING")
        if result.observed_cost is None or not result.observed_cost.is_finite() or result.observed_cost < 0 or result.observed_cost > lease.max_cost: raise ValueError("TOOL_RESULT_COST_INVALID")
        return ToolResult(result.tool_id, result.payload, result.observed_cost, descriptor.result_trust, result.provenance_ref)

    def _descriptor(self, tool_id: str) -> ToolDescriptor:
        item = self._tools.get(tool_id)
        if item is None: raise KeyError("TOOL_NOT_REGISTERED")
        return item[0]

    def _ensure_open(self) -> None:
        if self._closed: raise RuntimeError("govern-tool-calls service is closed")

    def close(self) -> None:
        self._closed = True; self._tools.clear(); self._leases.clear(); self._used_nonces.clear(); self._human.clear()
