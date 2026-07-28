"""Data-to-Risk-to-Trading economic-news governance integration."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data import (
    EconomicEvent,
    EventImpact,
    MarketContextEvidence,
    populate_market_context_calendar,
)
from app.services.risk import (
    DecisionState,
    KillSwitchState,
    LimitStatus,
    RiskConfig,
    RiskDecisionPackage,
    evaluate_market_context,
)
from app.services.trading import (
    RouteSnapshot,
    TradingRequest,
    assess_execution_readiness,
)

_NOW = datetime(2026, 7, 26, 12, tzinfo=UTC)
_REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
_WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
_CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _risk_config() -> RiskConfig:
    """Build the deterministic simulation Risk policy."""
    return RiskConfig.model_validate(
        {
            "profile": "simulation",
            "execution_route": "sim",
            "policy_version": "policy-1",
            "base_currency": "USD",
            "pending_order_exposure_policy": "include_full_remaining_exposure",
            "evidence_max_age_seconds": {"portfolio": 60, "market": 30},
            "clock_skew_tolerance_seconds": Decimal(0),
            "var_min_observations": 3,
            "var_lookback": 3,
            "regime_assessment_enabled": False,
            "approval_token_ttl_seconds": Decimal(60),
            "approval_signing_key_ref": "secrets/risk-key",
            "decision_ttl_seconds": Decimal(30),
            "kill_switch_activation_permissions": ("risk.kill.activate",),
            "kill_switch_clearance_permissions": ("risk.kill.clear",),
            "report_timeout_seconds": Decimal(5),
            "session_timezone": "UTC",
            "missing_calendar_mode": "block",
            "max_spread": {"EURUSD@points": Decimal(2)},
        }
    )


def _market() -> MarketContextEvidence:
    """Build complete market evidence with calendar acquisition pending."""
    return MarketContextEvidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state=None,
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=_NOW,
        expires_at=_NOW + timedelta(minutes=1),
        provenance={"source": "integration"},
        missing_fields=("calendar",),
        request_id=_REQUEST_ID,
    )


def _event() -> EconomicEvent:
    """Build one high-impact USD release five minutes ahead."""
    return EconomicEvent(
        id="provider-event-1",
        provider="demo",
        name="CPI",
        category="inflation",
        country="US",
        currency="USD",
        scheduled_at=_NOW + timedelta(minutes=5),
        impact=EventImpact.HIGH,
        forecast=Decimal("3.2"),
        forecast_raw="3.2%",
        unit="%",
    )


def _trading_request() -> TradingRequest:
    """Build a governed order request referencing the Risk decision."""
    return TradingRequest(
        request_id=_REQUEST_ID,
        workflow_id=_WORKFLOW_ID,
        correlation_id=_CORRELATION_ID,
        route="sim",
        action="submit_order",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="risk-calendar-block",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-absent",
        idempotency_key="calendar-integration-001",
        canonical_material_version="v1",
        system_time=_NOW,
        valid_until=_NOW + timedelta(minutes=5),
    )


def _route() -> RouteSnapshot:
    """Build fresh simulation route evidence."""
    return RouteSnapshot(
        route="sim",
        provider_id=None,
        account_id="account-001",
        symbol="EURUSD",
        facts={"permission": "allowed"},
        source_id="data-source-001",
        authority_id="simulator",
        observed_at=_NOW,
        expires_at=_NOW + timedelta(minutes=1),
        available=True,
        fresh=True,
        capabilities=("submit_order",),
    )


def _switch() -> KillSwitchState:
    """Build fresh inactive Risk kill-switch evidence."""
    return KillSwitchState(
        state_id="switch-001",
        scope_level="global",
        scope={},
        state="inactive",
        reason="integration",
        version=1,
        updated_at=_NOW,
    )


def test_high_impact_event_blocks_risk_and_trading_readiness() -> None:
    """Risk consumes Data calendar evidence and Trading consumes only Risk."""
    evidence = populate_market_context_calendar(_market(), events=[_event()])
    limit_response = evaluate_market_context(evidence, _risk_config(), now=_NOW)
    assert limit_response.status == "success"
    assert limit_response.data is not None
    limit_results = limit_response.data
    calendar = next(result for result in limit_results if result.limit_id == "calendar")
    assert calendar.status is LimitStatus.BLOCKED

    decision = RiskDecisionPackage(
        decision_id="risk-calendar-block",
        intent_id="intent-001",
        state=DecisionState.REJECT,
        requested_size=Decimal("1.00"),
        approved_size=None,
        ordered_checks=limit_results,
        primary_failure_limit="calendar",
        composite_breach_flags=("calendar",),
        evidence_refs={"market": evidence.request_id},
        config_hash="a" * 64,
        concurrency_disclosure="risk-store",
        recommendations=("wait_until_calendar_open",),
        issued_at=_NOW,
        expires_at=_NOW + timedelta(minutes=1),
        token=None,
        request_id=_REQUEST_ID,
        workflow_id=_WORKFLOW_ID,
        correlation_id=_CORRELATION_ID,
    )
    assessment = assess_execution_readiness(
        _trading_request(),
        _route(),
        decision,
        _switch(),
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": (_NOW + timedelta(minutes=1)).isoformat(),
        },
        {
            "route_snapshot": Decimal(30),
            "risk_decision": Decimal(30),
            "kill_switch": Decimal(30),
        },
    )

    assert assessment.passed is False
    assert "RISK_NOT_APPROVED" in assessment.failed_check_codes
