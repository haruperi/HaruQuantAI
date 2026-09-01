"""Integration tests for Risk receiver-owned dependency contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data import (
    build_account_state_snapshot,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_context_evidence,
)
from app.services.risk import create_proposed_trade, validate_market_context_evidence
from app.services.strategy import create_trade_intent_value

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_risk_embeds_the_exact_strategy_intent() -> None:
    """Preserve the complete Strategy object at the Risk boundary."""
    intent = create_trade_intent_value(
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
        lineage={"config_hash": "a" * 64},
    )
    proposal = create_proposed_trade(
        intent=intent,
        account_id="account-1",
        portfolio_id=None,
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile="demo",
        evidence_refs={"market": "market-1"},
        provenance={"source": "strategy"},
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    assert proposal.intent is intent


def test_risk_consumes_the_data_market_contract() -> None:
    """Validate Data evidence directly without a Risk duplicate model."""
    evidence = build_market_context_evidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal("0.0001"),
        spread_unit="price",
        liquidity=Decimal(100),
        volatility=Decimal("0.10"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=(),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    validate_market_context_evidence(evidence, now=NOW)


def test_risk_consumes_data_account_and_fx_contracts() -> None:
    """Validate Data account state snapshot and FX conversion evidence at the Risk boundary."""
    account = build_account_state_snapshot(
        account_id="acc-1",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal(100000),
                "available": Decimal(100000),
            },
        ),
        equity=Decimal(100000),
        margin_used=Decimal(0),
        margin_available=Decimal(100000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    assert account.account_id == "acc-1"
    assert account.currency == "USD"

    leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.0850"),
        source_id="fx-source-1",
        provider_symbol="EURUSD",
        as_of=NOW,
        provenance={"source": "data"},
    )
    fx = build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="USD",
        legs=(leg,),
        composite_rate=Decimal("1.0850"),
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        path_policy_id="direct",
        path_policy_version="1",
        provenance={"source": "data"},
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    assert fx.source_currency == "EUR"
    assert fx.composite_rate == Decimal("1.0850")


def test_risk_consumes_utils_auth_context_contract() -> None:
    """Validate Utils auth context at the Risk boundary."""
    from app.contracts.common.models import create_auth_context

    auth = create_auth_context(
        principal_id="user-1",
        principal_type="USER",
        roles=("risk_admin",),
        permissions=("kill_switch:activate", "kill_switch:clear"),
        scopes=("global",),
        tenant_or_environment="dev",
        issued_at=NOW,
        request_id="req-12345678-1234-4234-8234-123456789abc",
        workflow_id="wf-12345678-1234-4234-8234-123456789abc",
        correlation_id="cor-12345678-1234-4234-8234-123456789abc",
    )
    assert auth.principal_id == "user-1"
    assert "risk_admin" in auth.roles
