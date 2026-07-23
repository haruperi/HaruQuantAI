"""Integration tests for Risk receiver-owned dependency contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.evidence.market_context_contracts import (
    MarketContextEvidence,
)
from app.services.risk.contracts import ProposedTrade, validate_market_context_evidence
from app.services.strategy import TradeIntent

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_risk_embeds_the_exact_strategy_intent() -> None:
    """Preserve the complete Strategy object at the Risk boundary."""
    intent = TradeIntent(
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
    proposal = ProposedTrade(
        intent=intent,
        account_id="account-1",
        portfolio_id=None,
        requested_size=Decimal(1),
        current_price=Decimal("1.10"),
        stop_distance=Decimal("0.01"),
        market_as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        risk_profile="paper",
        evidence_refs={"market": "market-1"},
        provenance={"source": "strategy"},
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    assert proposal.intent is intent


def test_risk_consumes_the_data_market_contract() -> None:
    """Validate Data evidence directly without a Risk duplicate model."""
    evidence = MarketContextEvidence(
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
