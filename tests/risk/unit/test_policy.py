"""Unit tests for Risk Policy resolution and override token validation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.risk.config import load_risk_config
from app.services.risk.models import (
    PolicyRule,
    PolicyScope,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionStatus,
    RiskMode,
)
from app.services.risk.policy import (
    resolve_policy,
    validate_override_token,
    validate_risk_budget_gates,
)
from app.utils.normalization import utc_now


@pytest.fixture
def base_config() -> RiskConfig:
    """Load default base risk config."""
    return load_risk_config("default")


def test_resolve_policy_default_no_rules(base_config: RiskConfig) -> None:
    """Test policy resolution when no rules are applied."""
    context = {"environment": "local", "mode": RiskMode.SIMULATION}
    result = resolve_policy(base_config, [], context)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_daily_loss_pct == base_config.max_daily_loss_pct
    assert result.policy_hash == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4"  # pragma: allowlist secret
        "649b934ca495991b7852b855"  # pragma: allowlist secret
    )  # sha256 of empty str


def test_resolve_policy_with_matching_rules(base_config: RiskConfig) -> None:
    """Test policy resolution with scoped rules matching the context."""
    rules = [
        PolicyRule(
            rule_id="r1",
            scope=PolicyScope(strategy_id="mean-reversion-v1"),
            overrides={"max_daily_loss_pct": 0.08},
        ),
        PolicyRule(
            rule_id="r2",
            scope=PolicyScope(symbol="EURUSD"),
            overrides={"max_effective_leverage": 20.0},
        ),
    ]

    # Context matching both rules
    context = {
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "environment": "local",
    }
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_daily_loss_pct == Decimal("0.08")
    assert result.resolved_config.max_effective_leverage == Decimal("20.0")


def test_resolve_policy_precedence(base_config: RiskConfig) -> None:
    """Test that policy precedence works correctly (more specific overrides win)."""
    # symbol scope is more specific than strategy, which is more specific than account
    rules = [
        PolicyRule(
            rule_id="r_acc",
            scope=PolicyScope(account_id="acc-123"),
            overrides={"max_daily_loss_pct": 0.06},
        ),
        PolicyRule(
            rule_id="r_strat",
            scope=PolicyScope(strategy_id="mean-reversion-v1"),
            overrides={"max_daily_loss_pct": 0.07},
        ),
        PolicyRule(
            rule_id="r_sym",
            scope=PolicyScope(symbol="EURUSD"),
            overrides={"max_daily_loss_pct": 0.08},
        ),
    ]

    context = {
        "account_id": "acc-123",
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "environment": "local",
    }
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.APPROVE
    # Symbol wins precedence
    assert result.resolved_config.max_daily_loss_pct == Decimal("0.08")


def test_resolve_policy_expiry(base_config: RiskConfig) -> None:
    """Test that expired rules are ignored during resolution."""
    now = utc_now()
    rules = [
        PolicyRule(
            rule_id="expired_rule",
            scope=PolicyScope(strategy_id="expired-strat"),
            overrides={"max_daily_loss_pct": 0.08},
            expiry_time=now - timedelta(seconds=1),
        ),
        PolicyRule(
            rule_id="valid_rule",
            scope=PolicyScope(strategy_id="expired-strat"),
            overrides={"max_effective_leverage": 15.0},
            expiry_time=now + timedelta(hours=1),
        ),
    ]

    context = {"strategy_id": "expired-strat", "environment": "local"}
    result = resolve_policy(base_config, rules, context)
    # Expired override ignored
    assert result.resolved_config.max_daily_loss_pct == base_config.max_daily_loss_pct
    # Valid override applied
    assert result.resolved_config.max_effective_leverage == Decimal("15.0")


def test_resolve_policy_ceiling_violation(base_config: RiskConfig) -> None:
    """Test that resolving overrides exceeding ceilings fails closed (rejection)."""
    rules = [
        PolicyRule(
            rule_id="unsafe_override",
            scope=PolicyScope(strategy_id="unsafe-strat"),
            overrides={"max_daily_loss_pct": 0.25},  # Hard ceiling is 0.20
        ),
    ]

    context = {"strategy_id": "unsafe-strat", "environment": "local"}
    result = resolve_policy(base_config, rules, context)
    assert result.status == RiskDecisionStatus.REJECT
    assert len(result.breaches) > 0


def test_resolve_policy_live_sensitive_blocked(base_config: RiskConfig) -> None:
    """Test that live sensitive modes block configs without live authorization."""
    context = {"environment": "production", "mode": RiskMode.FULL_LIVE}
    # base_config loaded from "default" has allow_live_execution=False
    result = resolve_policy(base_config, [], context)
    assert result.status == RiskDecisionStatus.BLOCK
    assert "Execution blocked" in result.reason


def test_validate_override_token() -> None:
    """Test validation checks on RiskApprovalToken limit overrides."""
    now = utc_now()
    cfg_hash = "cfg_hash_123"

    token = RiskApprovalToken(
        token_id="tok-001",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override_limits",
        approver="risk_manager",
        expiry_time=now + timedelta(minutes=30),
        config_hash=cfg_hash,
        decision_hash="dec-1",
        scope={"symbol": "EURUSD", "environment": "staging"},
        nonce="nonce-1",
        signature="sig-1",
    )

    # Valid check
    assert validate_override_token(token, {"symbol": "EURUSD"}, cfg_hash) is True

    # Expired token check
    expired_token = token.model_copy(update={"expiry_time": now - timedelta(seconds=1)})
    assert (
        validate_override_token(expired_token, {"symbol": "EURUSD"}, cfg_hash) is False
    )

    # Config hash mismatch check
    assert (
        validate_override_token(token, {"symbol": "EURUSD"}, "different_hash") is False
    )

    # Scope mismatch check
    assert validate_override_token(token, {"symbol": "GBPUSD"}, cfg_hash) is False

    # Live override role verification check (only authorized roles)
    unauthorized_token = token.model_copy(update={"approver": "strategy_developer"})
    assert (
        validate_override_token(unauthorized_token, {"symbol": "EURUSD"}, cfg_hash)
        is False
    )


def test_validate_risk_budget_gates(base_config: RiskConfig) -> None:
    """Test risk budget gate validation logic."""
    assert (
        validate_risk_budget_gates("strat-1", Decimal("1000.00"), base_config) is True
    )

    # Check that negative or zero limits fail
    invalid_config = base_config.model_copy(
        update={"max_risk_per_trade": Decimal("-0.01")}
    )
    assert (
        validate_risk_budget_gates("strat-1", Decimal("1000.00"), invalid_config)
        is False
    )


def test_risk_policy_engine_resolution(base_config: RiskConfig) -> None:
    """Test RiskPolicyEngine matching and resolution with bundle and policies."""
    from app.services.risk.models import PolicyRule, PolicyScope
    from app.services.risk.policy import (
        PolicyBundle,
        PolicyResolutionQuery,
        PolicyVersion,
        RiskPolicy,
        RiskPolicyEngine,
    )

    version = PolicyVersion(version_id="v1.0.0", author="compliance_officer")
    policy = RiskPolicy(
        policy_id="pol-001",
        profile_name="default",
        rules=[
            PolicyRule(
                rule_id="rule-leverage",
                scope=PolicyScope(
                    environment="production", mode=RiskMode.FULL_LIVE, symbol="EURUSD"
                ),
                overrides={
                    "max_effective_leverage": Decimal("10.0"),
                    "allow_live_execution": True,
                },
            )
        ],
    )
    bundle = PolicyBundle(bundle_id="bundle-1", version=version, policies=[policy])
    engine = RiskPolicyEngine(bundle=bundle)

    query = PolicyResolutionQuery(
        environment="production",
        mode="full_live",
        symbol="EURUSD",
    )
    # Resolve config with overrides, version metadata, and scope metadata
    result = engine.resolve(query, base_config)
    assert result.status == RiskDecisionStatus.APPROVE
    assert result.resolved_config.max_effective_leverage == Decimal("10.0")
    assert result.policy_version == "v1.0.0"
    assert result.policy_scope is not None
    assert result.policy_scope.get("environment") == "production"


def test_check_policy_permission_scenarios() -> None:
    """Test check_policy_permission role constraints by environment."""
    from app.services.risk.policy import check_policy_permission

    # In production/staging, only admin, compliance_officer, risk_manager are allowed
    assert check_policy_permission("admin", "override_limits", "production") is True
    assert (
        check_policy_permission("compliance_officer", "override_limits", "staging")
        is True
    )
    assert (
        check_policy_permission("risk_manager", "override_limits", "production") is True
    )
    assert (
        check_policy_permission("developer", "override_limits", "production") is False
    )
    assert check_policy_permission("operator", "override_limits", "production") is False

    # force_resume requires admin or compliance_officer in prod/staging
    assert check_policy_permission("admin", "force_resume", "production") is True
    assert (
        check_policy_permission("compliance_officer", "force_resume", "production")
        is True
    )
    assert (
        check_policy_permission("risk_manager", "force_resume", "production") is False
    )

    # In local/simulation, developers and operators are allowed
    assert check_policy_permission("developer", "override_limits", "local") is True
    assert check_policy_permission("operator", "override_limits", "local") is True
    assert check_policy_permission("visitor", "override_limits", "local") is False


def test_policy_override_request_validation() -> None:
    """Test PolicyOverrideRequest validation structure."""
    from datetime import timedelta

    from app.services.risk.policy import PolicyOverrideRequest

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok-002",
        request_id="req-2",
        workflow_id="wf-2",
        approved_action="override_limits",
        approver="compliance_officer",
        expiry_time=now + timedelta(minutes=30),
        config_hash="hash_123",
        decision_hash="dec-2",
        scope={"symbol": "EURUSD"},
        nonce="nonce-2",
        signature="sig-2",
    )

    req = PolicyOverrideRequest(
        request_id="req-2",
        token=token,
        target_overrides={"max_effective_leverage": 15.0},
    )
    assert req.request_id == "req-2"
    assert req.token.token_id == "tok-002"
    assert req.target_overrides["max_effective_leverage"] == 15.0


def test_validate_policy_scope_scenarios() -> None:
    """Test validate_policy_scope scenarios.

    Covers valid, empty, and malformed fields.
    """
    from app.services.risk.policy import validate_policy_scope

    # Empty scope
    empty_scope = PolicyScope()
    res = validate_policy_scope(empty_scope)
    assert res["valid"] is False
    assert res["code"] == "EMPTY_SCOPE"

    # Malformed field
    malformed_scope = PolicyScope(environment=" ")
    res2 = validate_policy_scope(malformed_scope)
    assert res2["valid"] is False
    assert res2["code"] == "MALFORMED_SCOPE_FIELD"

    # Valid scope
    valid_scope = PolicyScope(environment="production", symbol="EURUSD")
    res3 = validate_policy_scope(valid_scope)
    assert res3["valid"] is True
    assert res3["code"] == "OK"


def test_resolve_effective_policy_and_expiry(base_config: RiskConfig) -> None:
    """Test resolution of effective policies and policy expiry behavior."""
    from app.services.risk.policy import (
        RiskPolicy,
        ValidationError,
        resolve_effective_policy,
    )

    now = utc_now()

    # Expired policy
    expired_policy = RiskPolicy(
        policy_id="pol-expired",
        profile_name="default",
        expiry_time=now - timedelta(seconds=1),
        scope=PolicyScope(strategy_id="strat-1"),
    )
    with pytest.raises(ValidationError, match="no active risk policy resolved"):
        resolve_effective_policy({"strategy_id": "strat-1"}, [expired_policy])

    # Valid policy
    active_policy = RiskPolicy(
        policy_id="pol-active",
        profile_name="default",
        scope=PolicyScope(strategy_id="strat-1"),
        rules=[
            PolicyRule(
                rule_id="r1",
                scope=PolicyScope(strategy_id="strat-1"),
                overrides={"max_daily_loss_pct": 0.08},
            )
        ],
    )
    effective = resolve_effective_policy(
        {"strategy_id": "strat-1", "environment": "local", "mode": RiskMode.SIMULATION},
        [active_policy],
    )
    assert effective.policy_id == "pol-active"
    assert effective.resolved_config.max_daily_loss_pct == Decimal("0.08")
    assert effective.policy_hash != ""

    # Specificity sorting: Strategy policy overrides Global policy
    global_policy = RiskPolicy(
        policy_id="pol-global",
        profile_name="default",
        scope=None,  # Global
    )
    effective_sorted = resolve_effective_policy(
        {"strategy_id": "strat-1", "environment": "local", "mode": RiskMode.SIMULATION},
        [global_policy, active_policy],
    )
    # The more specific active_policy (strategy_id scope) should be resolved
    assert effective_sorted.policy_id == "pol-active"


def test_resolve_effective_policy_failures() -> None:
    """Test fail-closed scenarios in resolve_effective_policy."""
    from app.services.risk.policy import (
        RiskPolicy,
        ValidationError,
        resolve_effective_policy,
    )

    # Safety ceilings violation
    violating_policy = RiskPolicy(
        policy_id="pol-violating",
        profile_name="default",
        rules=[
            PolicyRule(
                rule_id="r_bad",
                scope=PolicyScope(strategy_id="strat-1"),
                overrides={"max_daily_loss_pct": 0.35},  # Ceiling is 0.20
            )
        ],
    )
    with pytest.raises(ValidationError, match="violates safety ceilings"):
        resolve_effective_policy(
            {"strategy_id": "strat-1", "environment": "local"},
            [violating_policy],
        )

    # Live sensitive execution blocked
    live_blocked_policy = RiskPolicy(
        policy_id="pol-live-blocked",
        profile_name="default",  # Default profile has allow_live_execution=False
    )
    with pytest.raises(ValidationError, match="live execution is disabled"):
        resolve_effective_policy(
            {"environment": "production", "mode": "full_live"},
            [live_blocked_policy],
        )

    # Non-existent profile load failure
    bad_profile_policy = RiskPolicy(
        policy_id="pol-bad-profile",
        profile_name="non-existent-profile-xyz",
    )
    with pytest.raises(ValidationError, match="Failed to load risk configuration"):
        resolve_effective_policy(
            {"environment": "local"},
            [bad_profile_policy],
        )


def test_evaluate_risk_budget_scenarios(base_config: RiskConfig) -> None:
    """Test evaluate_risk_budget behavior across validation gates."""
    from app.services.risk.models import ProposedAllocation, RiskAssessmentRequest
    from app.services.risk.policy import EffectiveRiskPolicy, evaluate_risk_budget

    policy = EffectiveRiskPolicy(
        policy_id="pol-1",
        resolved_config=base_config,
        policy_hash="hash-1",
        provenance={"policy_version": "v2.0.0", "policy_scope": {}},
    )

    from app.services.risk.models import PortfolioState

    portfolio_state = PortfolioState(
        account_id="acc-1",
        balance=Decimal("10000.0"),
        equity=Decimal("10000.0"),
        margin_used=Decimal("0.0"),
        free_margin=Decimal("10000.0"),
        floating_pnl=Decimal("0.0"),
        realized_pnl=Decimal("0.0"),
        currency="USD",
        as_of=utc_now(),
    )

    # Missing strategy_id
    req_no_strat = RiskAssessmentRequest(
        strategy_id="",
        proposed_action=ProposedAllocation(
            allocations={"": Decimal("500.0")}, as_of=utc_now()
        ),
        portfolio_state=portfolio_state,
        risk_config=base_config,
    )
    res = evaluate_risk_budget(policy, req_no_strat)
    assert res.status == RiskDecisionStatus.REJECT
    assert "Missing strategy_id" in res.reason

    # Invalid budget
    req_bad_budget = RiskAssessmentRequest(
        strategy_id="strat-1",
        proposed_action=ProposedAllocation(
            allocations={"strat-1": Decimal("-10.0")}, as_of=utc_now()
        ),
        portfolio_state=portfolio_state,
        risk_config=base_config,
    )
    res2 = evaluate_risk_budget(policy, req_bad_budget)
    assert res2.status == RiskDecisionStatus.REJECT
    assert "Invalid budget" in res2.reason

    # Exceeds max risk per trade
    base_config_low_risk = base_config.model_copy(
        update={"max_risk_per_trade": Decimal("0.001")}
    )
    policy_low_risk = policy.model_copy(
        update={"resolved_config": base_config_low_risk}
    )
    req_exceeds = RiskAssessmentRequest(
        strategy_id="strat-1",
        proposed_action=ProposedAllocation(
            allocations={"strat-1": Decimal("50.0")}, as_of=utc_now()
        ),
        portfolio_state=portfolio_state,
        risk_config=base_config_low_risk,
    )
    res3 = evaluate_risk_budget(policy_low_risk, req_exceeds)
    assert res3.status == RiskDecisionStatus.REJECT
    assert "exceeds maximum risk" in res3.reason

    # Advisory exceeds hard drawdown limit
    base_config_bad_drawdown = base_config.model_copy(
        update={
            "max_total_loss_pct": Decimal("0.05"),
            "max_total_loss_pct_advisory": Decimal("0.06"),
            "drawdown": base_config.drawdown.model_copy(
                update={"total_drawdown_hard_limit": Decimal("0.05")}
            ),
        }
    )
    policy_bad_drawdown = policy.model_copy(
        update={"resolved_config": base_config_bad_drawdown}
    )
    req_ok = RiskAssessmentRequest(
        strategy_id="strat-1",
        proposed_action=ProposedAllocation(
            allocations={"strat-1": Decimal("0.0001")}, as_of=utc_now()
        ),
        portfolio_state=portfolio_state,
        risk_config=base_config_bad_drawdown,
    )
    res4 = evaluate_risk_budget(policy_bad_drawdown, req_ok)
    assert res4.status == RiskDecisionStatus.REJECT
    assert "Advisory loss limit exceeds" in res4.reason


def test_validate_token_config_compatibility_scenarios() -> None:
    """Test token config compatibility validation under scope bypass."""
    from app.services.risk.policy import validate_token_config_compatibility

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok-01",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override",
        approver="risk_manager",
        expiry_time=now + timedelta(hours=1),
        config_hash="expected_hash",
        decision_hash="dec-1",
        nonce="nonce-1",
        signature="sig-1",
        scope={},
    )

    # Perfect match
    assert validate_token_config_compatibility(token, "expected_hash")["valid"] is True

    # Hash mismatch
    res = validate_token_config_compatibility(token, "different_hash")
    assert res["valid"] is False
    assert res["code"] == "CONFIG_HASH_MISMATCH"

    # Hash mismatch bypass explicitly allowed in scope
    token_bypass = token.model_copy(
        update={
            "scope": {"compatible_config_hashes": ["different_hash", "another_hash"]}
        }
    )
    assert (
        validate_token_config_compatibility(token_bypass, "different_hash")["valid"]
        is True
    )


def test_requires_override_approval_scenarios(base_config: RiskConfig) -> None:
    """Test override request approval verification rules."""
    from app.services.risk.policy import (
        EffectiveRiskPolicy,
        RiskOverrideRequest,
        requires_override_approval,
    )

    policy = EffectiveRiskPolicy(
        policy_id="pol-1",
        resolved_config=base_config,
        policy_hash="hash-1",
        provenance={"policy_scope": {"environment": "local"}},
    )

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok-01",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override",
        approver="risk_manager",
        expiry_time=now + timedelta(hours=1),
        config_hash="hash-1",
        decision_hash="dec-1",
        nonce="nonce-1",
        signature="sig-1",
        scope={},
    )

    req = RiskOverrideRequest(
        request_id="req-1",
        token=token,
        target_overrides={"max_daily_loss_pct": Decimal("0.02")},
    )

    # 1. Live environment staging/production requires approval
    policy_staging = policy.model_copy(
        update={"provenance": {"policy_scope": {"environment": "staging"}}}
    )
    assert requires_override_approval(req, policy_staging) is True

    # 2. Matching applied rule explicitly flags approval requirement
    policy_flagged = policy.model_copy(
        update={
            "applied_rules": [
                PolicyRule(
                    rule_id="r1",
                    scope=PolicyScope(strategy_id="strat-1"),
                    requires_approval=True,
                )
            ]
        }
    )
    assert requires_override_approval(req, policy_flagged) is True

    # 3. Request relaxing limit (looser value) requires approval
    # Base config max_daily_loss_pct is 0.04. Requesting override to 0.05 (looser)
    req_looser = req.model_copy(
        update={"target_overrides": {"max_daily_loss_pct": Decimal("0.05")}}
    )
    assert requires_override_approval(req_looser, policy) is True

    # Overriding to same/tighter value does not require approval
    req_tighter = req.model_copy(
        update={"target_overrides": {"max_daily_loss_pct": Decimal("0.03")}}
    )
    assert requires_override_approval(req_tighter, policy) is False


def test_validate_risk_override_request_scenarios(base_config: RiskConfig) -> None:
    """Test full verification of override requests including ceilings and authority."""
    from app.services.risk.policy import (
        EffectiveRiskPolicy,
        RiskOverrideRequest,
        validate_risk_override_request,
    )

    policy = EffectiveRiskPolicy(
        policy_id="pol-1",
        resolved_config=base_config,
        policy_hash="hash-1",
        provenance={"policy_scope": {"environment": "local"}},
    )

    now = utc_now()
    token = RiskApprovalToken(
        token_id="tok-01",
        request_id="req-1",
        workflow_id="wf-1",
        approved_action="override",
        approver="risk_manager",
        expiry_time=now + timedelta(hours=1),
        config_hash="",
        decision_hash="dec-1",
        nonce="nonce-1",
        signature="sig-1",
        scope={},
    )

    req = RiskOverrideRequest(
        request_id="req-1",
        token=token,
        target_overrides={"max_daily_loss_pct": Decimal("0.04")},
    )

    # 1. Config compatibility failure
    res_compat = validate_risk_override_request(req, policy)
    assert res_compat["valid"] is False
    assert res_compat["code"] == "CONFIG_HASH_MISMATCH"

    # Fix token config hash for next checks
    token_ok_hash = token.model_copy(update={"config_hash": base_config.content_hash()})
    req_ok_hash = req.model_copy(update={"token": token_ok_hash})

    # 2. Token expired
    token_expired = token_ok_hash.model_copy(
        update={"expiry_time": now - timedelta(seconds=1)}
    )
    req_expired = req.model_copy(update={"token": token_expired})
    res_expired = validate_risk_override_request(req_expired, policy)
    assert res_expired["valid"] is False
    assert res_expired["code"] == "TOKEN_EXPIRED"

    # 3. Scope mismatch
    token_scope = token_ok_hash.model_copy(update={"scope": {"symbol": "EURUSD"}})
    req_scope = req.model_copy(update={"token": token_scope})
    policy_scope_mismatch = policy.model_copy(
        update={"provenance": {"policy_scope": {"symbol": "GBPUSD"}}}
    )
    res_scope = validate_risk_override_request(req_scope, policy_scope_mismatch)
    assert res_scope["valid"] is False
    assert res_scope["code"] == "SCOPE_MISMATCH"

    # 4. Insufficient authority in live environment
    token_unauth = token_ok_hash.model_copy(
        update={"approver": "developer", "scope": {"environment": "production"}}
    )
    req_unauth = req.model_copy(update={"token": token_unauth})
    policy_prod = policy.model_copy(
        update={"provenance": {"policy_scope": {"environment": "production"}}}
    )
    res_unauth = validate_risk_override_request(req_unauth, policy_prod)
    assert res_unauth["valid"] is False
    assert res_unauth["code"] == "INSUFFICIENT_AUTHORITY"

    # 5. Overriding exceeds hard safety ceiling
    req_ceiling = req_ok_hash.model_copy(
        update={
            "target_overrides": {"max_daily_loss_pct": Decimal("0.25")}
        }  # Ceiling is 0.20
    )
    res_ceiling = validate_risk_override_request(req_ceiling, policy)
    assert res_ceiling["valid"] is False
    assert res_ceiling["code"] == "CEILING_BREACH"

    # 6. Invalid numeric format
    req_bad_format = req_ok_hash.model_copy(
        update={"target_overrides": {"max_daily_loss_pct": "not-a-decimal"}}
    )
    res_format = validate_risk_override_request(req_bad_format, policy)
    assert res_format["valid"] is False
    assert res_format["code"] == "INVALID_NUMERIC_FORMAT"

    # 7. Valid override check passes
    res_valid = validate_risk_override_request(req_ok_hash, policy)
    assert res_valid["valid"] is True
    assert res_valid["code"] == "OK"
