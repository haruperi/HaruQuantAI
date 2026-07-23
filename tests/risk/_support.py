"""Shared test support helpers and fixtures for Risk tests."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal, cast

from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
)
from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    AllocationReviewRequest,
    AllocationRiskDecision,
    ApprovalAttestation,
    DecisionState,
    KillSwitchState,
    PortfolioRiskSnapshot,
    PositionSizingRequest,
    ProposedTrade,
    RegimeAssessment,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    StrategyOperationalEligibilityDecision,
)
from app.services.risk.governor import RiskGovernor
from app.services.risk.sizing import calculate_position_size
from app.services.strategy import (
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    TradeIntent,
    ValidatedStrategyRef,
)
from app.utils import AuthContext, canonical_json

NOW = datetime(2026, 7, 19, 5, tzinfo=UTC)
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
HASH_A = "a" * 64
HASH_B = "b" * 64
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


class _Audit:
    """Example audit receiver that captures material events."""

    def __init__(self) -> None:
        """Initialize empty captured events."""
        self.records: list[RiskAuditRecord] = []

    def append(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Capture one unsealed event.

        Args:
            record: Material event to capture.

        Returns:
            Captured event.
        """
        self.records.append(record)
        return record


class _AuditStore:
    """Minimal durable audit adapter for examples."""

    def __init__(self) -> None:
        """Initialize empty example audit state."""
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the current example audit head.

        Returns:
            Latest sealed example record, or None when the chain is empty.
        """
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Append one exactly ordered example record.

        Returns:
            The literal "appended" on success, or "conflict" when the sequence or
            previous hash does not match the current head.
        """
        del timeout_seconds
        head = self.records[-1] if self.records else None
        sequence = 0 if head is None else int(head.sequence or 0) + 1
        previous = "0" * 64 if head is None else str(head.record_hash)
        if sequence != expected_sequence or previous != expected_previous_hash:
            return "conflict"
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return all example audit records.

        Returns:
            Every example audit record in ascending sequence order.
        """
        del timeout_seconds
        return tuple(self.records)


class _EligibilityStore:
    """Example receiver-owned eligibility decision store."""

    def __init__(self) -> None:
        """Initialize without a saved decision."""
        self.decision: StrategyOperationalEligibilityDecision | None = None

    def save_if_absent(
        self,
        decision: StrategyOperationalEligibilityDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Save the first example decision.

        Returns:
            True when this call stored the decision, False when one was already present.
        """
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


class _AllocationStore:
    """Example receiver-owned allocation review and active-budget store."""

    def __init__(self) -> None:
        """Initialize empty review and active state."""
        self.review: AllocationRiskDecision | None = None
        self.active: AllocationRiskDecision | None = None

    def save_review_if_absent(
        self,
        decision: AllocationRiskDecision,
        *,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Save the first example allocation review.

        Returns:
            True when this call stored the review decision, False when one was
            already present.
        """
        del timeout_seconds
        if self.review is not None:
            return False
        self.review = decision
        return True

    def get_active(
        self, portfolio_id: str, *, timeout_seconds: Decimal | None
    ) -> AllocationRiskDecision | None:
        """Return the active example budget.

        Returns:
            Active example allocation decision, or None when no budget is active.
        """
        del timeout_seconds
        if self.active is not None and self.active.portfolio_id == portfolio_id:
            return self.active
        return None

    def activate_compare_and_swap(
        self,
        decision: AllocationRiskDecision,
        *,
        expected_predecessor_version: str | None,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Activate when the expected predecessor matches.

        Returns:
            True when the expected predecessor matched and activation occurred,
            False otherwise.
        """
        del timeout_seconds
        current = None if self.active is None else self.active.reviewed_version
        if current != expected_predecessor_version:
            return False
        self.active = decision
        return True


class _TokenStore:
    """Minimal single-process durable token adapter for examples."""

    def __init__(self) -> None:
        """Initialize empty example token state."""
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
        """Save one issued example token.

        Returns:
            The literal "saved" on first issue, "already_saved" for an identical
            token, or "conflict".
        """
        del timeout_seconds
        current = self.tokens.get(token.token_id)
        if current is None:
            self.tokens[token.token_id] = token
            return "saved"
        return "already_saved" if current == token else "conflict"

    def consume_if_active(
        self,
        token_id: str,
        *,
        expected_signature: str,
        reservation_id: str,
        workflow_id: str,
        action: str,
        scope: Mapping[str, str],
        now: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal[
        "consumed",
        "missing",
        "expired",
        "revoked",
        "already_consumed",
        "conflict",
    ]:
        """Consume one active exact example token.

        Returns:
            Exact consumption outcome for the supplied token and reservation.
        """
        del reservation_id, timeout_seconds
        token = self.tokens.get(token_id)
        if token is None:
            return "missing"
        if token_id in self.revoked:
            return "revoked"
        if token_id in self.consumed:
            return "already_consumed"
        if now >= token.expires_at:
            return "expired"
        if (
            token.signature != expected_signature
            or token.workflow_id != workflow_id
            or token.action != action
            or dict(token.scope) != dict(scope)
        ):
            return "conflict"
        self.consumed.add(token_id)
        return "consumed"

    def revoke_intersecting(
        self,
        scope: Mapping[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        """Revoke outstanding tokens matching an example scope.

        Returns:
            Count of outstanding example tokens revoked by the supplied scope.
        """
        del reason, revoked_at, timeout_seconds
        selected = {
            token_id
            for token_id, token in self.tokens.items()
            if token_id not in self.consumed
            and all(token.scope.get(key) == value for key, value in scope.items())
        }
        new = selected - self.revoked
        self.revoked.update(new)
        return len(new)


class _KillStore:
    """Minimal version-exact canonical state adapter for examples."""

    def __init__(self) -> None:
        """Initialize without a persisted resulting state."""
        self.state: KillSwitchState | None = None

    def compare_and_swap(
        self,
        state: KillSwitchState,
        *,
        expected_version: int,
        timeout_seconds: Decimal | None,
    ) -> bool:
        """Persist when the supplied predecessor version is current.

        Returns:
            True when the supplied predecessor version was current and the state was
            replaced, False otherwise.
        """
        del timeout_seconds
        current = expected_version if self.state is None else self.state.version
        if current != expected_version:
            return False
        self.state = state
        return True


def _config() -> RiskConfig:
    """Build a complete simulation Policy configuration.

    Returns:
        Complete simulation-profile Risk configuration.
    """
    return RiskConfig(
        profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _market() -> MarketContextEvidence:
    """Build complete fresh market evidence.

    Returns:
        Fresh complete market-context evidence.
    """
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "example"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )


def _snapshot(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build a healthy example portfolio snapshot.

    Returns:
        Healthy example portfolio risk snapshot.
    """
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(100),
        total_loss=Decimal(200),
        gross_exposure=Decimal(1000),
        net_exposure=Decimal(1000),
        drawdown=Decimal("0.02"),
        margin_utilization=Decimal("0.10"),
        effective_leverage=Decimal("0.10"),
        historical_var=Decimal(50),
        historical_cvar=Decimal(70),
        volatility=Decimal("0.01"),
        portfolio_correlation=Decimal("0.10"),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash=compute_config_hash(config),
        evidence_refs={"account": "account-evidence-1"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )


def _registration() -> ValidatedStrategyRef:
    """Build an approved simulation Strategy reference.

    Returns:
        Approved simulation Strategy registration reference.
    """
    validation = StrategyValidationPolicy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = StrategyManifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=StrategyTimingPolicy.EVENT_DRIVEN,
        permitted_environments=(StrategyEnvironment.SIMULATION,),
        source_hash=HASH_A,
        artifact_hash=HASH_A,
        dependency_hash=HASH_A,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    return ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.SIMULATION,
        policy_version=validation.policy_version,
        validation_policy=validation,
        registry_record_hash=HASH_B,
        request_id="strategy-request-1",
        correlation_id="correlation-1",
    )


def _allocation_request(config: RiskConfig) -> AllocationReviewRequest:
    """Build a self-contained within-cap allocation review request.

    Returns:
        Self-contained allocation review request within the configured caps.
    """
    return AllocationReviewRequest(
        projection_kind="construction",
        portfolio_id="portfolio-1",
        portfolio_version="allocation-v1",
        result_id="construction-1",
        plan_id=None,
        ordered_components=(
            {
                "component_id": "component-1",
                "dimension": "symbol:EURUSD",
                "weight": "0.05",
            },
        ),
        eligibility_decision_refs=("eligibility-1",),
        account_evidence_ref="account-evidence-1",
        market_evidence_ref=MARKET_REQUEST_ID,
        fx_evidence_refs=(),
        evidence_hashes={"snapshot_config": compute_config_hash(config)},
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=NOW,
        request_id="allocation-request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def _auth(config: RiskConfig, *, clearance: bool = False) -> AuthContext:
    """Build exact authenticated governor trace and permissions.

    Returns:
        Authenticated context carrying exact governor trace and permissions.
    """
    permissions = ["risk.kill.activate"]
    if clearance:
        permissions.append("risk.kill.clear")
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-1",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=tuple(permissions),
        scopes=("risk",),
        tenant_or_environment=config.profile,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )


def _intent() -> TradeIntent:
    """Build one immutable Strategy risk-increase intent.

    Returns:
        Immutable Strategy risk-increase trade intent.
    """
    return TradeIntent(
        intent_id="intent-1",
        decision_id="strategy-decision-1",
        idempotency_key="intent-key-1",
        strategy_id="strategy-1",
        strategy_version="1.0.0",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode="fixed_risk",
        quantity_hint=Decimal(1),
        notional_hint=None,
        signal_timestamp=NOW,
        decision_timestamp=NOW,
        parent_intent_id=None,
        stop_loss=Decimal("1.09"),
        take_profit=None,
        expiration=NOW + timedelta(minutes=1),
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref=None,
        lineage={"strategy_config": "a" * 64},
    )


def _proposal(config: RiskConfig) -> ProposedTrade:
    """Build an exactly bound ProposedTrade.

    Returns:
        Risk-owned proposal bound exactly to the embedded trade intent.
    """
    return ProposedTrade(
        intent=_intent(),
        account_id="account-1",
        portfolio_id="portfolio-1",
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile=config.profile,
        evidence_refs={"market": MARKET_REQUEST_ID},
        provenance={"source": "strategy"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def _snapshot_governor(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build healthy portfolio evidence with exact governor trace.

    Returns:
        Healthy portfolio snapshot carrying exact governor trace identifiers.
    """
    return _snapshot(config).model_copy(
        update={
            "request_id": REQUEST_ID,
            "workflow_id": WORKFLOW_ID,
            "exposure_by_dimension": {},
            "contributions": {},
        }
    )


def _regime() -> RegimeAssessment:
    """Build one fully known normal regime assessment.

    Returns:
        Fully known normal regime assessment.
    """
    states = dict.fromkeys(
        (
            "volatility",
            "liquidity",
            "correlation",
            "drawdown",
            "crisis",
            "news",
            "session",
        ),
        "normal",
    )
    return RegimeAssessment(
        assessment_id="regime-1",
        states=states,
        previous_states=states,
        transitions=(),
        modifiers={},
        evidence_refs=("snapshot-1", MARKET_REQUEST_ID),
        missing_fields=(),
        assessed_at=NOW,
    )


def _inactive_state(
    level: Literal["global", "portfolio", "strategy", "symbol"] = "global",
) -> KillSwitchState:
    """Build one inactive applicable canonical kill-switch state.

    Returns:
        Inactive applicable canonical kill-switch state.
    """
    scopes = {
        "global": {},
        "portfolio": {"portfolio_id": "portfolio-1"},
        "strategy": {"strategy_id": "strategy-1"},
        "symbol": {"symbol": "EURUSD"},
    }
    return KillSwitchState(
        state_id=f"{level}-state-1",
        scope_level=level,
        scope=scopes[level],
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )


def _services(
    config: RiskConfig,
) -> tuple[RiskGovernor, ApprovalTokenService, _Audit]:
    """Build fully injected approval and governor example services.

    Returns:
        Governor, approval-token service, and audit chain wired together.
    """
    audit = _Audit()
    token_store = _TokenStore()
    approvals = ApprovalTokenService(
        config,
        token_store,
        cast("RiskAuditChain", audit),
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    governor = RiskGovernor(
        config,
        approvals,
        cast("RiskAuditChain", audit),
        lambda: NOW,
    )
    return governor, approvals, audit


def _attestation(config: RiskConfig) -> ApprovalAttestation:
    """Build exact authorized trade approval evidence.

    Returns:
        Authorized trade approval evidence bound to the decision.
    """
    return ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="operator-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=compute_config_hash(config),
        policy_version=config.policy_version,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def _values(
    *, live: bool = False
) -> tuple[
    ApprovalTokenService,
    _TokenStore,
    RiskDecisionPackage,
    ApprovalAttestation,
]:
    """Build a complete independently runnable approval helper.

    Returns:
        Token service, token store, decision, and attestation for one run.
    """
    config = RiskConfig(
        profile="live" if live else "research",
        execution_route="live" if live else "none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"audit": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3 if live else None,
        var_lookback=3 if live else None,
        missing_calendar_mode="block" if live else None,
        audit_timeout_seconds=Decimal(5) if live else None,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        token_state_timeout_seconds=Decimal(5) if live else None,
        decision_ttl_seconds=Decimal(120),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
        double_spend_owner="risk_store" if live else None,
    )
    token_store = _TokenStore()
    audit = RiskAuditChain(config, _AuditStore(), lambda: NOW, canonical_json)
    service = ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "approver-1",
    )
    config_hash = compute_config_hash(config)
    decision = RiskDecisionPackage(
        decision_id="decision-1",
        intent_id="intent-1",
        state=DecisionState.APPROVE,
        requested_size=Decimal(10),
        approved_size=Decimal(8),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-1"},
        config_hash=config_hash,
        concurrency_disclosure="risk_store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=120),
        token=None,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    attestation = ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="approver-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=config_hash,
        policy_version=config.policy_version,
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=120),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    return service, token_store, decision, attestation


def _expected(token: RiskApprovalToken) -> dict[str, str]:
    """Build the exact documented execution-side expectation mapping.

    Returns:
        Exact execution-side expectation mapping for token validation.
    """
    return {
        "action": token.action,
        "decision_id": token.decision_id,
        "config_hash": token.config_hash,
        "request_id": token.request_id,
        "workflow_id": token.workflow_id,
        "correlation_id": token.correlation_id,
        **dict(token.scope),
    }


def run_position_size_test() -> None:
    """Calculate an explicit fixed monetary-risk recommendation.

    Raises:
        AssertionError: Normalized size is not one lot, or the result claims
            approval.
    """
    snapshot = _snapshot(_config())
    request = PositionSizingRequest(
        method="fixed_risk",
        requested_size=None,
        fixed_lot=None,
        risk_amount=Decimal(1000),
        risk_fraction=None,
        stop_distance=Decimal(100),
        unit_value=Decimal(10),
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"snapshot": snapshot.snapshot_id},
        request_id="request-1",
    )
    result = calculate_position_size(request, snapshot, _config())
    if result.normalized_size != Decimal(1):
        raise AssertionError("Fixed-risk example size did not normalize to one lot")
    if result.approved:
        raise AssertionError("Sizing result must never claim approval")
