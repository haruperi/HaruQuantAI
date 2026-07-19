"""Runnable usage examples for canonical Risk decision APIs."""

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, cast

from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    KillSwitchCommand,
    KillSwitchState,
    PortfolioRiskSnapshot,
    ProposedTrade,
    RegimeAssessment,
)
from app.services.risk.decisions import (
    RiskGovernor,
    apply_kill_switch_command,
    check_risk_kill_switch,
    revalidate_risk_decision,
)
from app.services.strategy import TradeIntent
from app.utils import AuthContext, generate_id

from tests.risk.usage import test_usage_approvals as approval_examples
from tests.risk.usage import test_usage_policy as policy_examples

if TYPE_CHECKING:
    from app.services.risk.audit import RiskAuditChain

NOW = policy_examples.NOW
REQUEST_ID = generate_id("req")
WORKFLOW_ID = generate_id("wf")
CORRELATION_ID = generate_id("cor")


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

        Args:
            state: New canonical state.
            expected_version: Required predecessor version.
            timeout_seconds: Configured receiver timeout.

        Returns:
            Whether the version-exact state write succeeded.
        """
        del timeout_seconds
        current = expected_version if self.state is None else self.state.version
        if current != expected_version:
            return False
        self.state = state
        return True


def _config() -> RiskConfig:
    """Return a complete deterministic simulation governor policy."""
    return policy_examples._config()


def _auth(config: RiskConfig, *, clearance: bool = False) -> AuthContext:
    """Build exact authenticated governor trace and permissions.

    Args:
        config: Active Risk policy.
        clearance: Whether to include kill-switch clearance permission.

    Returns:
        Immutable authenticated context.
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
    """Build one immutable Strategy risk-increase intent."""
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
    """Build an exactly bound non-executable Risk proposal."""
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
        evidence_refs={"market": policy_examples.MARKET_REQUEST_ID},
        provenance={"source": "strategy"},
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )


def _snapshot(config: RiskConfig) -> PortfolioRiskSnapshot:
    """Build healthy portfolio evidence with exact governor trace."""
    return policy_examples._snapshot(config).model_copy(
        update={
            "request_id": REQUEST_ID,
            "workflow_id": WORKFLOW_ID,
            "exposure_by_dimension": {},
            "contributions": {},
        }
    )


def _regime() -> RegimeAssessment:
    """Build one fully known normal regime assessment."""
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
        evidence_refs=("snapshot-1", policy_examples.MARKET_REQUEST_ID),
        missing_fields=(),
        assessed_at=NOW,
    )


def _inactive_state(
    level: Literal["global", "portfolio", "strategy", "symbol"] = "global",
) -> KillSwitchState:
    """Build one inactive applicable canonical kill-switch state.

    Args:
        level: Canonical scope level.

    Returns:
        Inactive exact state.
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
) -> tuple[RiskGovernor, ApprovalTokenService, policy_examples._Audit]:
    """Build fully injected approval and governor example services."""
    audit = policy_examples._Audit()
    token_store = approval_examples._TokenStore()
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
    """Build exact authorized trade approval evidence."""
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


def test_usage_governor_create() -> None:
    """Create a governor with explicit approval, audit, and clock dependencies."""
    governor, _, _ = _services(_config())
    assert isinstance(governor, RiskGovernor)


def test_usage_governor_trade_review() -> None:
    """Review one proposal and attach only an authenticated durable token."""
    config = _config()
    governor, _, _ = _services(config)
    decision = governor.review_trade_risk(
        _proposal(config),
        _snapshot(config),
        policy_examples._market(),
        _regime(),
        (_inactive_state(),),
        _auth(config),
        attestation=_attestation(config),
        now=NOW,
    )
    assert decision.token is not None


def test_usage_governor_portfolio() -> None:
    """Review current compliance without changing execution controls."""
    config = _config()
    governor, _, _ = _services(config)
    decision = governor.run_portfolio_risk_governor(
        _snapshot(config),
        policy_examples._market(),
        _regime(),
        (_inactive_state(),),
        _auth(config),
        now=NOW,
    )
    assert decision.approved_size is None


def test_usage_validity_revalidate() -> None:
    """Revalidate unchanged evidence without granting action authority."""
    config = _config()
    governor, _, _ = _services(config)
    proposal = _proposal(config)
    snapshot = _snapshot(config)
    decision = governor.review_trade_risk(
        proposal,
        snapshot,
        policy_examples._market(),
        _regime(),
        (_inactive_state(),),
        _auth(config),
        attestation=_attestation(config),
        now=NOW,
    )
    result = revalidate_risk_decision(decision, proposal, snapshot, config, now=NOW)
    assert result.reusable is True


def test_usage_kill_switch_apply() -> None:
    """Activate canonical state and revoke affected outstanding approvals."""
    config = _config()
    _, approvals, audit = _services(config)
    command = KillSwitchCommand(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    state = apply_kill_switch_command(
        command,
        _inactive_state(),
        _auth(config),
        approvals,
        cast("object", audit),  # type: ignore[arg-type]
        _KillStore(),
        config,
        now=NOW,
    )
    assert state.state == "active"


def test_usage_kill_switch_check() -> None:
    """Check recovery only after all applicable scopes are inactive."""
    config = _config()
    decision = check_risk_kill_switch(
        (_inactive_state(),),
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        _auth(config),
        reconciled=True,
        now=NOW,
    )
    assert decision.state.value == "approve"
