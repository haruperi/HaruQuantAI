"""Unit tests for the canonical Trading live gate sequence."""

# ruff: noqa: ARG005, INP001
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerFeatureFlags,
)
from app.services.risk import (
    ActionPolicyVerdict,
    DecisionState,
    KillSwitchState,
    RiskApprovalToken,
    RiskDecisionPackage,
)
from app.services.trading.contracts import TradingRequest, TradingRoute
from app.services.trading.live import LiveSession, evaluate_live_gate
from app.services.trading.state import IdempotencyReservation, TradingStateStore
from app.services.trading.validation import ReadinessAssessment
from app.utils import AuditEvent, AuthContext, logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        Asyncio backend name.
    """
    logger.debug("Selecting asyncio for live-gate tests")
    return "asyncio"


async def _passed() -> bool:
    """Return a successful lifecycle step.

    Returns:
        Always ``True``.
    """
    logger.debug("Running live-gate lifecycle test step")
    return True


class _Store:
    """Minimal atomic idempotency store for live-gate tests."""

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Return a new exact-material reservation.

        Args:
            key: Caller idempotency key.
            material_hash: Canonical material digest.
            material_version: Canonical material version.
            reserved_at: Injected creation time.
            expires_at: Reservation expiry.

        Returns:
            New reservation bound to supplied material.
        """
        logger.debug("Reserving live-gate test idempotency material")
        return IdempotencyReservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )

    def complete_idempotency(self, *args: object, **kwargs: object) -> None:
        """Accept completion outside this gate-focused test."""
        del args, kwargs


def _request() -> TradingRequest:
    """Build one complete governed live request.

    Returns:
        Canonical live request.
    """
    logger.debug("Building live-gate request fixture")
    return TradingRequest(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route=TradingRoute.LIVE,
        action="submit_order",
        provider_id="test-broker",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        quantity=Decimal(1),
        risk_decision_id="risk-decision-001",
        action_policy_verdict_id="policy-verdict-001",
        approval_token_ref="token-001",
        idempotency_key="idempotency-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
        instrument_min_quantity=Decimal("0.01"),
        instrument_max_quantity=Decimal(10),
        instrument_quantity_step=Decimal("0.01"),
    )


def _policy() -> ActionPolicyVerdict:
    """Build exact current action-policy evidence.

    Returns:
        Allowed Risk-owned action policy.
    """
    logger.debug("Building live-gate action policy")
    return ActionPolicyVerdict(
        verdict_id="policy-verdict-001",
        action="submit_order",
        scope={"account_id": "account-001"},
        policy_version="policy-v1",
        attestation_id="attestation-001",
        decision_id="risk-decision-001",
        reservation_id="reservation-001",
        allowed=True,
        reasons=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _risk_decision() -> RiskDecisionPackage:
    """Build exact current Risk approval with token evidence.

    Returns:
        Approved Risk decision package.
    """
    logger.debug("Building live-gate Risk decision")
    token = RiskApprovalToken(
        token_id="token-001",
        decision_id="risk-decision-001",
        config_hash="a" * 64,
        action="submit_order",
        scope={"account_id": "account-001"},
        approver_id="approver-001",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        nonce="nonce-001",
        signature="signature-001",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    return RiskDecisionPackage(
        decision_id="risk-decision-001",
        intent_id="intent-001",
        state=DecisionState.APPROVE,
        requested_size=Decimal(1),
        approved_size=Decimal(1),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"account": "snapshot-001"},
        config_hash="a" * 64,
        concurrency_disclosure="serialized",
        recommendations=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        token=token,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _inactive_switch() -> KillSwitchState:
    """Build current inactive global kill-switch evidence.

    Returns:
        Inactive Risk switch state.
    """
    logger.debug("Building inactive live-gate kill switch")
    return KillSwitchState(
        state_id="switch-001",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )


def _inactive_hierarchy(
    global_state: KillSwitchState | None = None,
) -> tuple[KillSwitchState, ...]:
    """Build all exact applicable inactive switch scopes."""
    return (
        global_state or _inactive_switch(),
        KillSwitchState(
            state_id="switch-strategy",
            scope_level="strategy",
            scope={"strategy_id": "strategy-001"},
            state="inactive",
            reason="normal operation",
            version=1,
            updated_at=NOW,
        ),
        KillSwitchState(
            state_id="switch-symbol",
            scope_level="symbol",
            scope={"symbol": "EURUSD"},
            state="inactive",
            reason="normal operation",
            version=1,
            updated_at=NOW,
        ),
    )


def _auth_context() -> AuthContext:
    """Build exact authenticated context for pre-mutation audit."""
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="trading-test",
        principal_type="SERVICE_ACCOUNT",
        roles=("trading",),
        permissions=("trading.execute",),
        scopes=("account-001",),
        tenant_or_environment="test",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=NOW,
    )


def _capability() -> dict[str, object]:
    """Build normalized approved adapter capability evidence.

    Returns:
        Complete capability mapping.
    """
    logger.debug("Building live-gate adapter capability")
    return {
        "provider_id": "test-broker",
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "v1",
        "supported_actions": ["submit_order"],
        "supported_order_types": ["MARKET"],
        "security_profile": "approved",
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "external",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }


def _session(
    *,
    risk_decision: RiskDecisionPackage | None = None,
    kill_switches: tuple[KillSwitchState, ...] = (),
    pre_audit_sink: Callable[[AuditEvent], None] | None = None,
) -> LiveSession:
    """Build a mutation-enabled session with injected Risk evidence.

    Args:
        risk_decision: Optional typed Risk approval.
        kill_switches: Applicable Risk switch hierarchy.
        pre_audit_sink: Optional observable canonical audit sink.

    Returns:
        Started-capable LiveSession fixture.
    """
    logger.debug("Building live-gate session fixture")
    connection = cast(
        "BrokerConnectionConfig",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
            provider_enabled=True,
        ),
    )
    adapter = cast(
        "BrokerAdapter",
        SimpleNamespace(contract_version="v1", schema_id="brokers.adapter.v1"),
    )
    flags = cast(
        "BrokerFeatureFlags",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
        ),
    )
    return LiveSession(
        store=cast("TradingStateStore", _Store()),
        connection=connection,
        broker_adapter=adapter,
        feature_flags=flags,
        risk_decision_source=lambda request: risk_decision,
        action_policy_source=lambda request: _policy(),
        kill_switch_source=lambda request: kill_switches,
        readiness_source=lambda request, evidence: ReadinessAssessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"test": "ready"},
            assessed_at=NOW,
        ),
        adapter_capability_source=lambda request: _capability(),
        auth_context_source=lambda request: _auth_context(),
        pre_audit_sink=pre_audit_sink or (lambda evidence: None),
        event_sink=lambda event: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )


@pytest.mark.anyio
async def test_real_risk_decision_is_mandatory() -> None:
    """Reject caller evidence when the typed Risk source has no decision."""
    logger.debug("Testing mandatory real Risk decision gate")
    session = _session()
    await session.start(
        {
            "RUNTIME_PROFILE": "live",
            "EXECUTION_ROUTE": "live",
            "ALLOW_LIVE_MUTATIONS": True,
            "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
            "SHUTDOWN_BUDGET_SECONDS": "5",
            "IDEMPOTENCY_RETENTION_SECONDS": 600,
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
            "MAX_STALENESS_SECONDS": {
                "route_snapshot": "30",
                "risk_decision": "30",
                "kill_switch": "30",
            },
            "DATA_AUTHORITY_ID": "data-authority-001",
        },
        {
            "data_authority_id": "data-authority-001",
            "adapter_security_profile": "approved",
            "startup_evidence_fresh": True,
        },
    )
    blocked = await evaluate_live_gate(
        _request(),
        {"caller_claimed_risk_approval": True},
        session,
    )
    assert blocked.status == "error"
    assert blocked.error is not None
    assert blocked.error.code == "GATE_BLOCKED"


@pytest.mark.anyio
async def test_gate_passes_every_typed_authority_in_order() -> None:
    """Authorize dispatch only after every typed mandatory gate passes."""
    logger.debug("Testing complete live-gate success path")
    session = _session(
        risk_decision=_risk_decision(),
        kill_switches=_inactive_hierarchy(),
    )
    await session.start(
        {
            "RUNTIME_PROFILE": "live",
            "EXECUTION_ROUTE": "live",
            "ALLOW_LIVE_MUTATIONS": True,
            "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
            "SHUTDOWN_BUDGET_SECONDS": "5",
            "IDEMPOTENCY_RETENTION_SECONDS": 600,
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
            "MAX_STALENESS_SECONDS": {
                "route_snapshot": "30",
                "risk_decision": "30",
                "kill_switch": "30",
            },
            "DATA_AUTHORITY_ID": "data-authority-001",
        },
        {
            "data_authority_id": "data-authority-001",
            "adapter_security_profile": "approved",
            "startup_evidence_fresh": True,
        },
    )
    result = await evaluate_live_gate(_request(), {"route": "fresh"}, session)
    assert result.status == "success"
    assert result.data is not None
    assert result.data["dispatch_allowed"] is True


@pytest.mark.anyio
async def test_gate_emits_exact_utils_audit_event() -> None:
    """The live pre-mutation boundary emits the shared typed AuditEvent."""
    audits: list[AuditEvent] = []
    session = _session(
        risk_decision=_risk_decision(),
        kill_switches=_inactive_hierarchy(),
        pre_audit_sink=audits.append,
    )
    await session.start(
        {
            "RUNTIME_PROFILE": "live",
            "EXECUTION_ROUTE": "live",
            "ALLOW_LIVE_MUTATIONS": True,
            "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
            "SHUTDOWN_BUDGET_SECONDS": "5",
            "IDEMPOTENCY_RETENTION_SECONDS": 600,
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
            "MAX_STALENESS_SECONDS": {
                "route_snapshot": "30",
                "risk_decision": "30",
                "kill_switch": "30",
            },
            "DATA_AUTHORITY_ID": "data-authority-001",
        },
        {
            "data_authority_id": "data-authority-001",
            "adapter_security_profile": "approved",
            "startup_evidence_fresh": True,
        },
    )

    await evaluate_live_gate(_request(), {"route": "fresh"}, session)

    assert len(audits) == 1
    assert isinstance(audits[0], AuditEvent)
    assert audits[0].principal_id == _auth_context().principal_id
    assert audits[0].request_id == _auth_context().request_id


@pytest.mark.anyio
async def test_stale_kill_switch_evidence_blocks_dispatch() -> None:
    """Inactive but stale kill-switch evidence cannot authorize mutation."""
    logger.debug("Testing live-gate kill-switch freshness")
    stale_switch = _inactive_switch().model_copy(
        update={"updated_at": NOW - timedelta(seconds=31)}
    )
    session = _session(
        risk_decision=_risk_decision(),
        kill_switches=_inactive_hierarchy(stale_switch),
    )
    await session.start(
        {
            "RUNTIME_PROFILE": "live",
            "EXECUTION_ROUTE": "live",
            "ALLOW_LIVE_MUTATIONS": True,
            "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
            "SHUTDOWN_BUDGET_SECONDS": "5",
            "IDEMPOTENCY_RETENTION_SECONDS": 600,
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
            "MAX_STALENESS_SECONDS": {
                "route_snapshot": "30",
                "risk_decision": "30",
                "kill_switch": "30",
            },
            "DATA_AUTHORITY_ID": "data-authority-001",
        },
        {
            "data_authority_id": "data-authority-001",
            "adapter_security_profile": "approved",
            "startup_evidence_fresh": True,
        },
    )
    assert stale_switch.state == "inactive"
    blocked = await evaluate_live_gate(_request(), {"route": "fresh"}, session)
    assert blocked.status == "error"
    assert blocked.error is not None
    assert blocked.error.code == "KILL_SWITCH_STALE"
