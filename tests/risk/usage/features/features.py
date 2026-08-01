"""Executable Full-Domain Risk Pipeline usage program.

Connects all 15 registered package features (`FEAT-RISK-01` through `FEAT-RISK-15`)
into a single homogeneous, end-to-end operational pipeline.
Imports strictly from the public API boundary `app.services.risk`.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_account_state_snapshot,
    build_market_context_evidence,
)
from app.services.risk import (
    activate_allocation_budget,
    append_risk_audit_record,
    apply_kill_switch_command,
    assess_risk_regime,
    build_portfolio_risk_snapshot,
    calculate_position_size,
    check_risk_kill_switch,
    compute_config_hash,
    create_allocation_budget_activation_request,
    create_allocation_review_request,
    create_approval_attestation,
    create_approval_token_service,
    create_firm_mandate,
    create_kill_switch_command,
    create_kill_switch_state,
    create_portfolio_state,
    create_position_sizing_request,
    create_proposed_trade,
    create_risk_audit_chain,
    create_risk_audit_record,
    create_risk_config,
    create_risk_decision_package,
    create_risk_domain_error,
    create_risk_governor,
    create_scenario_definition,
    create_strategy_operational_eligibility_request,
    evaluate_market_context,
    evaluate_portfolio_limits,
    evaluate_single_day_profit_share,
    generate_risk_report,
    get_decision_state,
    get_risk_error_code,
    issue_risk_approval_token,
    revalidate_risk_decision,
    review_allocation_proposal,
    review_strategy_admission,
    review_trade_risk,
    revoke_risk_approval_scope,
    run_portfolio_risk_governor,
    run_risk_scenario_analysis,
    validate_market_context_evidence,
    validate_risk_approval_token,
    verify_risk_audit_chain,
)
from app.services.strategy import (
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_trade_intent_value,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.utils import canonical_json, create_auth_context, generate_id
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = generate_id("req")
WORKFLOW_ID = generate_id("wf")
CORRELATION_ID = generate_id("cor")
MARKET_REQUEST_ID = "req-cccccccc-cccc-4ccc-8ccc-cccccccccccc"
HASH_64 = "a" * 64


def _stage_banner(stage_num: int, title: str, feature_id: str) -> None:
    """Print stage header banner."""
    print(f"\n{'=' * 88}")
    print(f"Stage {stage_num}: {title} ({feature_id})")
    print(f"{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _ExampleStore:
    """Minimal in-memory store adapter for audit and token state."""

    def __init__(self) -> None:
        self.records: list[Any] = []
        self.tokens: dict[str, Any] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        del timeout_seconds
        return tuple(self.records)

    def save_issued(
        self, token: Any, *, timeout_seconds: Decimal | None
    ) -> Literal["saved", "already_saved", "conflict"]:
        del timeout_seconds
        self.tokens[token.token_id] = token
        return "saved"

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
        "consumed", "missing", "expired", "revoked", "already_consumed", "conflict"
    ]:
        del expected_signature, reservation_id, workflow_id, action, scope
        del now, timeout_seconds
        token = self.tokens.get(token_id)
        if token is None:
            return "missing"
        if token_id in self.revoked:
            return "revoked"
        if token_id in self.consumed:
            return "already_consumed"
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
        del reason, revoked_at, timeout_seconds
        count = 0
        for token_id, token in self.tokens.items():
            if token_id not in self.consumed and all(
                token.scope.get(k) == v for k, v in scope.items()
            ):
                self.revoked.add(token_id)
                count += 1
        return count


class _ExampleEligibilityStore:
    """Minimal idempotent eligibility decision store."""

    def __init__(self) -> None:
        self.decision: Any | None = None

    def save_if_absent(self, decision: Any, *, timeout_seconds: Decimal | None) -> bool:
        del timeout_seconds
        if self.decision is not None:
            return False
        self.decision = decision
        return True


class _ExampleAllocationStore:
    """Minimal allocation review and budget store."""

    def __init__(self) -> None:
        self.review: Any | None = None
        self.active: Any | None = None

    def save_review_if_absent(
        self, decision: Any, *, timeout_seconds: Decimal | None
    ) -> bool:
        del timeout_seconds
        if self.review is not None:
            return False
        self.review = decision
        return True

    def get_active(
        self, portfolio_id: str, *, timeout_seconds: Decimal | None
    ) -> Any | None:
        del timeout_seconds
        if self.active is not None and self.active.portfolio_id == portfolio_id:
            return self.active
        return None

    def activate_compare_and_swap(
        self,
        decision: Any,
        *,
        expected_predecessor_version: str | None,
        timeout_seconds: Decimal | None,
    ) -> bool:
        del timeout_seconds
        current = None if self.active is None else self.active.reviewed_version
        if current != expected_predecessor_version:
            return False
        self.active = decision
        return True


class _ExampleKillStore(_ExampleStore):
    """Minimal kill-switch state store."""

    def __init__(self) -> None:
        super().__init__()
        self.state: create_kill_switch_state | None = None

    def compare_and_swap_with_audit(
        self,
        state: create_kill_switch_state,
        record: Any,
        *,
        expected_version: int,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["committed", "already_committed", "conflict"]:
        del timeout_seconds, expected_version, expected_sequence, expected_previous_hash
        self.state = state
        self.records.append(record)
        return "committed"


def main() -> None:  # noqa: PLR0915
    """Run full Risk domain feature pipeline sequentially."""
    print("\n" + "=" * 88)
    print("HARUQUANT AI — RISK DOMAIN FULL-FEATURE PIPELINE EXECUTION")
    print("=" * 88)

    # -------------------------------------------------------------------------
    # Stage 1: Versioned Contracts & Domain Errors (FEAT-RISK-01)
    # -------------------------------------------------------------------------
    _stage_banner(1, "Versioned Contracts and Errors", "FEAT-RISK-01")
    account_snapshot = build_account_state_snapshot(
        account_id="acc-001",
        currency="USD",
        balances=(
            {"asset": "USD", "total": Decimal(10000), "available": Decimal(9500)},
        ),
        equity=Decimal(10000),
        margin_used=Decimal(500),
        margin_available=Decimal(9500),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
    )
    portfolio_state = create_portfolio_state(
        account_snapshot=account_snapshot,
        peak_equity=Decimal(10000),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
    )
    print(_format_result(portfolio_state))

    err = create_risk_domain_error(
        get_risk_error_code("INVALID_INPUT"), details="Pipeline contract check"
    )
    print(_format_result(err))

    # -------------------------------------------------------------------------
    # Stage 2: Risk Profile & Configuration Hashing (FEAT-RISK-02)
    # -------------------------------------------------------------------------
    _stage_banner(2, "Risk Profiles and Configuration", "FEAT-RISK-02")
    config_values = {
        "profile": "simulation",
        "execution_route": "sim",
        "policy_version": "policy-1",
        "base_currency": "USD",
        "pending_order_exposure_policy": "include_full_remaining_exposure",
        "evidence_max_age_seconds": {"portfolio": 60, "market": 30, "audit": 60},
        "clock_skew_tolerance_seconds": Decimal(0),
        "var_min_observations": 3,
        "var_lookback": 3,
        "regime_assessment_enabled": True,
        "approval_token_ttl_seconds": Decimal(60),
        "approval_signing_key_ref": "secrets/risk-key",
        "decision_ttl_seconds": Decimal(30),
        "kill_switch_activation_permissions": ("risk.kill.activate",),
        "kill_switch_clearance_permissions": ("risk.kill.clear",),
        "report_timeout_seconds": Decimal(5),
    }
    risk_config = create_risk_config(**config_values)
    config_hash = unwrap_risk_response(
        compute_config_hash(risk_config), operation="compute_config_hash"
    )
    print(_format_result(risk_config))
    print(f"Computed Config SHA256 Hash: {config_hash}")

    firm_mandate = create_firm_mandate(
        account_id="acc-001",
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal(10000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash=HASH_64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
        consistency_rule={
            "type": "max_single_day_share_of_profit",
            "value": Decimal("0.4"),
            "evaluated": "retrospective",
            "applies_in_phase": ("funded",),
        },
    )
    print(_format_result(firm_mandate))

    # -------------------------------------------------------------------------
    # Stage 3: Portfolio Risk Snapshot Computation (FEAT-RISK-03)
    # -------------------------------------------------------------------------
    _stage_banner(3, "Portfolio Risk Snapshot Computation", "FEAT-RISK-03")
    risk_snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(portfolio_state, risk_config, now=NOW),
        operation="build_portfolio_risk_snapshot",
    )
    print(_format_result(risk_snapshot))
    print(
        f"Snapshot -> equity={risk_snapshot.equity}, gross_exposure={risk_snapshot.gross_exposure}"
    )

    # -------------------------------------------------------------------------
    # Stage 4: Position Sizing Engine (FEAT-RISK-04)
    # -------------------------------------------------------------------------
    _stage_banner(4, "Position Sizing Engine", "FEAT-RISK-04")
    sizing_req = create_position_sizing_request(
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
        evidence_refs={"snapshot": risk_snapshot.snapshot_id},
        request_id=REQUEST_ID,
    )
    sizing_result = unwrap_risk_response(
        calculate_position_size(sizing_req, risk_snapshot, risk_config),
        operation="calculate_position_size",
    )
    print(_format_result(sizing_result))
    print(
        f"Sizing -> normalized_size={sizing_result.normalized_size}, approved={sizing_result.approved}"
    )

    # -------------------------------------------------------------------------
    # Stage 5: Tamper-Evident Risk Audit Chain (FEAT-RISK-05)
    # -------------------------------------------------------------------------
    _stage_banner(5, "Tamper-Evident Risk Audit Chain", "FEAT-RISK-05")
    audit_store = _ExampleKillStore()
    audit_chain = create_risk_audit_chain(
        risk_config, audit_store, lambda: NOW, canonical_json
    )
    unsealed_record = create_risk_audit_record(
        record_id="audit-rec-001",
        event_type="risk.pipeline_execution",
        payload={"stage": "5", "status": "active"},
        evidence_refs={"snapshot": risk_snapshot.snapshot_id},
        config_hash=config_hash,
        decision_id=None,
        occurred_at=NOW,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    sealed_record = unwrap_risk_response(
        append_risk_audit_record(audit_chain, unsealed_record),
        operation="append_risk_audit_record",
    )
    print(_format_result(sealed_record))
    is_valid = unwrap_risk_response(
        verify_risk_audit_chain(
            audit_chain, audit_store.read_all(timeout_seconds=None)
        ),
        operation="verify_risk_audit_chain",
    )
    print(f"Audit Chain Integrity Verified: {is_valid}")

    # -------------------------------------------------------------------------
    # Stage 6: Portfolio & Market Limit Evaluation (FEAT-RISK-06)
    # -------------------------------------------------------------------------
    _stage_banner(6, "Portfolio and Market Limit Evaluation", "FEAT-RISK-06")
    market_evidence = build_market_context_evidence(
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
        provenance={"source": "data"},
        missing_fields=(),
        request_id=MARKET_REQUEST_ID,
    )
    market_validation = unwrap_risk_response(
        validate_market_context_evidence(market_evidence, now=NOW),
        operation="validate_market_context_evidence",
    )
    print(f"Market Evidence Validated: {market_validation}")

    limit_results = unwrap_risk_response(
        evaluate_portfolio_limits(
            risk_snapshot, risk_config, now=NOW, mandate=firm_mandate
        ),
        operation="evaluate_portfolio_limits",
    )
    print(_format_result(limit_results[0]))
    print(f"Portfolio Limits Evaluated: count={len(limit_results)}")

    market_limits = unwrap_risk_response(
        evaluate_market_context(market_evidence, risk_config, now=NOW),
        operation="evaluate_market_context",
    )
    print(_format_result(market_limits[0]))
    print(f"Market Context Checks Evaluated: count={len(market_limits)}")

    profit_share_result = unwrap_risk_response(
        evaluate_single_day_profit_share(risk_snapshot, firm_mandate, now=NOW),
        operation="evaluate_single_day_profit_share",
    )
    print(_format_result(profit_share_result))

    # -------------------------------------------------------------------------
    # Stage 7: Risk Regime Assessment (FEAT-RISK-07)
    # -------------------------------------------------------------------------
    _stage_banner(7, "Risk Regime Assessment", "FEAT-RISK-07")
    regime_assessment = unwrap_risk_response(
        assess_risk_regime(risk_snapshot, market_evidence, risk_config, now=NOW),
        operation="assess_risk_regime",
    )
    print(_format_result(regime_assessment))
    print(f"Regime Assessed At: {regime_assessment.assessed_at}")

    # -------------------------------------------------------------------------
    # Stage 8: Strategy Operational Eligibility Review (FEAT-RISK-08)
    # -------------------------------------------------------------------------
    _stage_banner(8, "Strategy Operational Eligibility Review", "FEAT-RISK-08")
    validation_policy = create_strategy_validation_policy(
        policy_version="strategy-policy-1",
        approved_module_roots=("approved.strategies",),
        max_config_payload_bytes=4096,
        max_config_nesting_depth=8,
        max_config_string_length=256,
        max_config_collection_items=128,
    )
    manifest = create_strategy_manifest(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        owner_ref="team-alpha",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("bars",),
        required_indicators=(),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("SIMULATION"),),
        source_hash=HASH_64,
        artifact_hash=HASH_64,
        dependency_hash=HASH_64,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=100,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5,
    )
    validated_ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("SIMULATION"),
        policy_version=validation_policy.policy_version,
        validation_policy=validation_policy,
        registry_record_hash=HASH_64,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    eligibility_req = create_strategy_operational_eligibility_request(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        runtime_profile="simulation",
        execution_route="sim",
        policy_version="policy-1",
        registration_ref=HASH_64,
        evidence_refs={"market": MARKET_REQUEST_ID},
        approval_refs=(),
        requested_scope={"symbol": "EURUSD"},
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    eligibility_store = _ExampleEligibilityStore()
    eligibility_decision = unwrap_risk_response(
        review_strategy_admission(
            eligibility_req,
            validated_ref,
            market_evidence,
            risk_config,
            eligibility_store,
            audit_chain,
            now=NOW,
        ),
        operation="review_strategy_admission",
    )
    print(_format_result(eligibility_decision))

    # -------------------------------------------------------------------------
    # Stage 9: Allocation Proposal Review & Budget Activation (FEAT-RISK-09)
    # -------------------------------------------------------------------------
    _stage_banner(9, "Allocation Review and Budget Activation", "FEAT-RISK-09")
    alloc_req = create_allocation_review_request(
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
        eligibility_decision_refs=(eligibility_decision.decision_id,),
        account_evidence_ref=risk_snapshot.evidence_refs.get("account", REQUEST_ID),
        market_evidence_ref=MARKET_REQUEST_ID,
        fx_evidence_refs=(),
        evidence_hashes={"snapshot_config": config_hash},
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    alloc_store = _ExampleAllocationStore()
    alloc_decision = unwrap_risk_response(
        review_allocation_proposal(
            alloc_req,
            risk_snapshot,
            market_evidence,
            risk_config,
            alloc_store,
            audit_chain,
            now=NOW,
        ),
        operation="review_allocation_proposal",
    )
    print(_format_result(alloc_decision))

    inactive_kill_state = create_kill_switch_state(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )
    budget_act_req = create_allocation_budget_activation_request(
        portfolio_id="portfolio-1",
        allocation_version="allocation-v1",
        decision_id=alloc_decision.decision_id,
        scope={"portfolio_id": "portfolio-1"},
        effective_at=NOW,
        predecessor_version=None,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    active_alloc = unwrap_risk_response(
        activate_allocation_budget(
            budget_act_req,
            alloc_decision,
            (inactive_kill_state,),
            risk_config,
            alloc_store,
            audit_chain,
            now=NOW,
        ),
        operation="activate_allocation_budget",
    )
    print(_format_result(active_alloc))

    # -------------------------------------------------------------------------
    # Stage 10: Durable Approval-Token Lifecycle (FEAT-RISK-10)
    # -------------------------------------------------------------------------
    _stage_banner(10, "Risk Approval Token Lifecycle", "FEAT-RISK-10")
    approval_store = _ExampleStore()
    approval_service = create_approval_token_service(
        risk_config,
        approval_store,
        audit_chain,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    trade_decision_pkg = create_risk_decision_package(
        decision_id="decision-001",
        intent_id="intent-001",
        state=get_decision_state("APPROVE"),
        requested_size=Decimal(1),
        approved_size=Decimal(1),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={
            "portfolio": risk_snapshot.snapshot_id,
            "proposal": REQUEST_ID,
            "market": MARKET_REQUEST_ID,
        },
        config_hash=config_hash,
        concurrency_disclosure="risk_store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=120),
        token=None,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    attestation = create_approval_attestation(
        attestation_id="attestation-001",
        principal_id="operator-1",
        action="submit_order",
        scope={"account_id": "acc-001", "symbol": "EURUSD"},
        policy_ref=config_hash,
        policy_version=risk_config.policy_version,
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=120),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    approval_token = unwrap_risk_response(
        issue_risk_approval_token(
            approval_service, trade_decision_pkg, attestation, now=NOW
        ),
        operation="issue_risk_approval_token",
    )
    print(_format_result(approval_token))

    token_validation = unwrap_risk_response(
        validate_risk_approval_token(
            approval_service,
            approval_token,
            attestation,
            {
                "action": approval_token.action,
                "decision_id": approval_token.decision_id,
                "config_hash": approval_token.config_hash,
                "request_id": approval_token.request_id,
                "workflow_id": approval_token.workflow_id,
                "correlation_id": approval_token.correlation_id,
                **dict(approval_token.scope),
            },
            now=NOW,
        ),
        operation="validate_risk_approval_token",
    )
    print(_format_result(token_validation))

    revoked_count = unwrap_risk_response(
        revoke_risk_approval_scope(
            approval_service,
            {"symbol": "EURUSD"},
            reason="Pipeline revocation test",
            now=NOW,
        ),
        operation="revoke_risk_approval_scope",
    )
    print(f"Revoked Tokens Count: {revoked_count}")

    # -------------------------------------------------------------------------
    # Stage 11: Risk Decision Revalidation (FEAT-RISK-11)
    # -------------------------------------------------------------------------
    _stage_banner(11, "Risk Decision Revalidation", "FEAT-RISK-11")
    intent_value = create_trade_intent_value(
        intent_id="intent-001",
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
        lineage={"strategy_config": HASH_64},
    )
    proposed_trade = create_proposed_trade(
        intent=intent_value,
        account_id="acc-001",
        portfolio_id="portfolio-1",
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile=risk_config.profile,
        evidence_refs={"market": MARKET_REQUEST_ID},
        provenance={"source": "strategy"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )

    reval_result = unwrap_risk_response(
        revalidate_risk_decision(
            trade_decision_pkg, proposed_trade, risk_snapshot, risk_config, now=NOW
        ),
        operation="revalidate_risk_decision",
    )
    print(_format_result(reval_result))
    print(f"Revalidation Output: reusable={reval_result.reusable}")

    # -------------------------------------------------------------------------
    # Stage 12: Canonical Risk Governor Orchestration (FEAT-RISK-12)
    # -------------------------------------------------------------------------
    _stage_banner(12, "Canonical Risk Governor Orchestration", "FEAT-RISK-12")
    governor_inst = create_risk_governor(
        risk_config, approval_service, audit_chain, lambda: NOW
    )
    auth_ctx = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-1",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate", "risk.kill.clear"),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile=risk_config.profile,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )
    reviewed_trade_decision = unwrap_risk_response(
        review_trade_risk(
            governor_inst,
            proposed_trade,
            risk_snapshot,
            market_evidence,
            regime_assessment,
            (inactive_kill_state,),
            auth_ctx,
            attestation=attestation,
            now=NOW,
        ),
        operation="review_trade_risk",
    )
    print(_format_result(reviewed_trade_decision))

    portfolio_governor_decision = unwrap_risk_response(
        run_portfolio_risk_governor(
            governor_inst,
            risk_snapshot,
            market_evidence,
            regime_assessment,
            (inactive_kill_state,),
            auth_ctx,
            now=NOW,
        ),
        operation="run_portfolio_risk_governor",
    )
    print(_format_result(portfolio_governor_decision))

    # -------------------------------------------------------------------------
    # Stage 13: Kill-Switch Authority & State Governance (FEAT-RISK-13)
    # -------------------------------------------------------------------------
    _stage_banner(13, "Kill-Switch Authority and Block State", "FEAT-RISK-13")
    kill_cmd = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="Pipeline safety test",
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    updated_kill_state = unwrap_risk_response(
        apply_kill_switch_command(
            kill_cmd,
            inactive_kill_state,
            auth_ctx,
            approval_service,
            audit_chain,
            audit_store,
            risk_config,
            now=NOW,
        ),
        operation="apply_kill_switch_command",
    )
    print(_format_result(updated_kill_state))

    kill_check_result = unwrap_risk_response(
        check_risk_kill_switch(
            (updated_kill_state,),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            risk_config,
            auth_ctx,
            reconciled=True,
            now=NOW,
        ),
        operation="check_risk_kill_switch",
    )
    print(_format_result(kill_check_result))
    print(f"Kill Switch Check State: {kill_check_result.state.value}")

    # -------------------------------------------------------------------------
    # Stage 14: Advisory Scenario Stress Testing (FEAT-RISK-14)
    # -------------------------------------------------------------------------
    _stage_banner(14, "Advisory Scenario Stress Testing", "FEAT-RISK-14")
    scenarios_def = (
        create_scenario_definition(
            scenario_id="equity-stress",
            shocks={"equity": Decimal("-0.10")},
            randomized=True,
            seed=42,
            assumptions=("declared ten-percent equity shock",),
        ),
    )
    scenario_results = unwrap_risk_response(
        run_risk_scenario_analysis(risk_snapshot, scenarios_def, risk_config, now=NOW),
        operation="run_risk_scenario_analysis",
    )
    print(_format_result(scenario_results[0]))
    print(f"Scenario Analysis Results: count={len(scenario_results)}")

    # -------------------------------------------------------------------------
    # Stage 15: Risk Decision Summaries & Reporting (FEAT-RISK-15)
    # -------------------------------------------------------------------------
    _stage_banner(15, "Risk Report Generation", "FEAT-RISK-15")
    risk_report = unwrap_risk_response(
        generate_risk_report(risk_snapshot, "markdown", risk_config, now=NOW),
        operation="generate_risk_report",
    )
    print(_format_result(risk_report))
    print(f"Report Generated: format={risk_report.format}")

    print("\n" + "=" * 88)
    print("ALL 15 STAGES COMPLETED SUCCESSFULLY WITH GENUINE RISK DOMAIN EVIDENCE")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
