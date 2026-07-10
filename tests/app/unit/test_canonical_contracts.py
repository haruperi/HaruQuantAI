"""Unit tests for Phase 1.5 decentralized canonical contracts."""

from __future__ import annotations

from typing import Any

import pytest
from app.services.analytics.contracts.audit import (
    AuditEvent,
)
from app.services.analytics.contracts.portfolio import (
    AccountSnapshot,
    Position,
)
from app.services.data.contracts import (
    Bar,
    Contract,
    DataSlice,
    Spread,
    Symbol,
    Tick,
    Timeframe,
)
from app.services.risk.contracts import (
    PositionSizingResult,
    RiskAuditEvent,
    RiskDecision,
    RiskRejection,
)
from app.services.simulator.contracts import (
    BacktestConfig,
    BacktestResult,
)
from app.services.strategy.contracts import (
    StrategyInput,
    StrategySignal,
)
from app.services.trading.contracts import (
    BrokerCapabilities,
    ExecutionReport,
    Fill,
    OrderIntent,
    TradeRequest,
    TradeResult,
)
from pydantic import ValidationError

RiskDecision.model_rebuild()


def test_base_contract_serialization_and_hashing() -> None:
    """Test base Contract serialization, hashing, and tracing fields."""
    c1 = Contract(
        schema_version="1.0.0",
        request_id="req_123",
        workflow_id="wf_456",
        correlation_id="corr_789",
        metadata={"mt5.ticket": 98765},
    )

    json_str = c1.to_json()
    assert "schema_version" in json_str
    assert "request_id" in json_str
    assert "mt5.ticket" in json_str

    h1 = c1.contract_hash()
    assert isinstance(h1, str)
    assert len(h1) == 64  # SHA256 hex digest

    # Full hash requires identical created_at to match.
    c2 = Contract(
        schema_version="1.0.0",
        created_at=c1.created_at,
        request_id="req_123",
        workflow_id="wf_456",
        correlation_id="corr_789",
        metadata={"mt5.ticket": 98765},
    )
    assert c1.contract_hash() == c2.contract_hash()


def test_content_hash_stable_across_trace_fields() -> None:
    """content_hash() must match when only trace context differs."""
    base_args: dict[str, Any] = {
        "schema_version": "1.0.0",
        "metadata": {"mt5.ticket": 98765},
    }
    c_a = Contract(**base_args, request_id="req_A", created_at="2026-01-01T00:00:00")
    c_b = Contract(**base_args, request_id="req_B", created_at="2026-06-01T12:00:00")

    # Different trace context — full hashes must differ.
    assert c_a.contract_hash() != c_b.contract_hash()
    # Same business content — content hashes must match.
    assert c_a.content_hash() == c_b.content_hash()


def test_base_contract_compatibility() -> None:
    """Test schema version compatibility checking logic."""
    c = Contract(schema_version="1.2.0")
    # Same major, target minor is lower/equal -> compatible
    assert c.check_compatibility("1.0.0") is True
    assert c.check_compatibility("1.2.0") is True
    # Same major, target minor is higher -> incompatible
    assert c.check_compatibility("1.3.0") is False
    # Different major -> incompatible
    assert c.check_compatibility("2.0.0") is False
    assert c.check_compatibility("0.9.0") is False


def test_metadata_namespacing_and_secrets_rejection() -> None:
    """Test that metadata keys must be namespaced and reject secrets."""
    # Namespaced metadata key works
    Contract(metadata={"provider.field": "val"})

    # Non-namespaced key raises error
    with pytest.raises(ValidationError) as exc:
        Contract(metadata={"invalidkey": "val"})
    assert "namespaced" in str(exc.value)

    # Sensitive key is rejected
    with pytest.raises(ValidationError) as exc:
        Contract(metadata={"p.password": "sec"})  # pragma: allowlist secret
    assert "sensitive" in str(exc.value)


def test_symbol_contract_validation() -> None:
    """Test Symbol contract validations."""
    sym = Symbol(
        symbol="EURUSD",
        broker_symbol="EURUSD.m",
        asset_class="forex",
        quote_currency="USD",
        base_currency="EUR",
        precision=5,
        lot_step=0.01,
        lot_min=0.01,
        lot_max=100.0,
        tick_size=0.00001,
        tick_value=1.0,
        contract_size=100000.0,
    )
    assert sym.symbol == "EURUSD"

    # lot_min > lot_max is rejected
    with pytest.raises(ValidationError):
        Symbol(
            symbol="EURUSD",
            broker_symbol="EURUSD.m",
            asset_class="forex",
            quote_currency="USD",
            base_currency="EUR",
            precision=5,
            lot_step=0.01,
            lot_min=10.0,
            lot_max=1.0,
            tick_size=0.00001,
            tick_value=1.0,
            contract_size=100000.0,
        )


def test_timeframe_contract_validation() -> None:
    """Test Timeframe contract validations."""
    tf = Timeframe(name="M5", duration_seconds=300)
    assert tf.name == "M5"

    with pytest.raises(ValidationError):
        Timeframe(name="InvalidTF", duration_seconds=300)


def test_bar_contract_validation() -> None:
    """Test Bar price checks and timestamp formatting."""
    bar = Bar(
        timestamp="2026-06-18 10:00:00",
        open=1.1000,
        high=1.1050,
        low=1.0950,
        close=1.1020,
        volume=100.0,
        spread=2.0,
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
    )
    # Checks normalization
    assert "T" in bar.timestamp

    # Invalid high/low constraint
    with pytest.raises(ValidationError):
        Bar(
            timestamp="2026-06-18 10:00:00",
            open=1.1000,
            high=1.0900,  # High < Low
            low=1.0950,
            close=1.1020,
            symbol="EURUSD",
            timeframe="M5",
            source="mt5",
        )

    # Prices outside high/low range
    with pytest.raises(ValidationError):
        Bar(
            timestamp="2026-06-18 10:00:00",
            open=1.1200,  # Open > High
            high=1.1050,
            low=1.0950,
            close=1.1020,
            symbol="EURUSD",
            timeframe="M5",
            source="mt5",
        )


def test_tick_and_spread_contract_validation() -> None:
    """Test Tick and Spread pricing rules (ask >= bid)."""
    Tick(
        timestamp="2026-06-18 10:00:00",
        bid=1.1000,
        ask=1.1002,
        symbol="EURUSD",
        source="mt5",
    )

    with pytest.raises(ValidationError):
        Tick(
            timestamp="2026-06-18 10:00:00",
            bid=1.1005,
            ask=1.1000,  # Ask < Bid
            symbol="EURUSD",
            source="mt5",
        )

    Spread(
        timestamp="2026-06-18 10:00:00",
        bid=1.1000,
        ask=1.1002,
        spread_points=2.0,
        spread_price=0.0002,
        symbol="EURUSD",
        source="mt5",
    )

    with pytest.raises(ValidationError):
        Spread(
            timestamp="2026-06-18 10:00:00",
            bid=1.1005,
            ask=1.1000,  # Ask < Bid
            spread_points=5.0,
            spread_price=0.0005,
            symbol="EURUSD",
            source="mt5",
        )


def test_strategy_signal_rejections() -> None:
    """Test StrategySignal validation rules and direct broker mutation checks."""
    valid_signal = StrategySignal(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        parameter_hash="h_abc123",
        symbol="EURUSD",
        side="buy",
        confidence=0.85,
        validity_window=86400,
        reason="EMA Crossover",
        evidence_references=["ref_doc_1"],
        source_data_hash="data_h1",
    )
    assert valid_signal.side == "buy"

    # Rejects missing evidence references
    with pytest.raises(ValidationError):
        StrategySignal(
            strategy_id="trend_following",
            strategy_version="1.0.0",
            parameter_hash="h_abc123",
            symbol="EURUSD",
            side="buy",
            confidence=0.85,
            validity_window=86400,
            reason="EMA Crossover",
            evidence_references=[],  # Empty evidence
            source_data_hash="data_h1",
        )

    # Rejects an expired signal (validity_window=1 second, created 10s in the past)
    from datetime import UTC, datetime, timedelta

    past_created_at = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    with pytest.raises(ValidationError):
        StrategySignal(
            strategy_id="trend_following",
            strategy_version="1.0.0",
            parameter_hash="h_abc123",
            symbol="EURUSD",
            side="buy",
            confidence=0.85,
            validity_window=1,  # 1 second window
            reason="EMA Crossover",
            evidence_references=["ref_doc_1"],
            source_data_hash="data_h1",
            created_at=past_created_at,  # 10 seconds ago — expired
        )

    bad_args: dict[str, Any] = {
        "strategy_id": "trend_following",
        "strategy_version": "1.0.0",
        "parameter_hash": "h_abc123",
        "symbol": "EURUSD",
        "side": "buy",
        "confidence": 0.85,
        "validity_window": 86400,
        "reason": "EMA Crossover",
        "evidence_references": ["ref_doc_1"],
        "source_data_hash": "data_h1",
        "ticket": 12345,  # EXTRA/BROKER SPECIFIC FIELD
    }
    with pytest.raises(ValidationError):
        StrategySignal(**bad_args)


def test_risk_decision_validations() -> None:
    """Test RiskDecision consistency.

    Approved requires sizing, rejected requires rejection.
    """
    sizing = PositionSizingResult(
        requested_size=1.0,
        approved_size=1.0,
        sizing_method="fixed",
        risk_contribution=0.02,
    )
    RiskDecision(
        decision_id="dec_1",
        signal_id="sig_abc",
        approved=True,
        sizing=sizing,
    )

    rejection = RiskRejection(
        code="LIMIT_FAILED",
        severity="error",
        reason="Daily drawdown limit hit",
    )
    RiskDecision(
        decision_id="dec_2",
        signal_id="sig_abc",
        approved=False,
        rejection=rejection,
    )

    with pytest.raises(ValidationError):
        RiskDecision(
            decision_id="dec_3",
            signal_id="sig_abc",
            approved=True,
            rejection=rejection,
        )

    with pytest.raises(ValidationError):
        RiskDecision(
            decision_id="dec_4",
            signal_id="sig_abc",
            approved=False,
            rejection=None,
        )


def test_dataslice_timeframe_validation() -> None:
    """DataSlice must reject unsupported timeframe identifiers."""
    DataSlice(
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
        provider="mt5",
        retrieved_at="2026-06-18 10:00:00",
        normalized_at="2026-06-18 10:01:00",
    )

    with pytest.raises(ValidationError):
        DataSlice(
            symbol="EURUSD",
            timeframe="tick",  # Not in ALLOWED_TIMEFRAMES
            source="mt5",
            provider="mt5",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:01:00",
        )

    with pytest.raises(ValidationError):
        DataSlice(
            symbol="EURUSD",
            timeframe="INVALID",
            source="mt5",
            provider="mt5",
            retrieved_at="2026-06-18 10:00:00",
            normalized_at="2026-06-18 10:01:00",
        )


def test_timeframe_from_name_classmethod() -> None:
    """Timeframe.from_name() must derive duration_seconds automatically."""
    tf = Timeframe.from_name("M5")
    assert tf.name == "M5"
    assert tf.duration_seconds == 300

    tf_h4 = Timeframe.from_name("H4")
    assert tf_h4.duration_seconds == 14400

    with pytest.raises(ValueError, match="Unsupported timeframe"):
        Timeframe.from_name("INVALID")


def test_strategy_input_timestamp_normalization() -> None:
    """StrategyInput boundary times must be normalized to ISO 8601."""
    si = StrategyInput(
        start_time="2026-06-18 10:00:00",
        end_time="2026-06-18 11:00:00",
    )
    assert "T" in si.start_time
    assert "T" in si.end_time

    with pytest.raises(ValidationError):
        StrategyInput(start_time="not-a-date", end_time="2026-06-18 11:00:00")


def test_all_other_models_instantiation() -> None:
    """Verify other models instantiate without issue and trace formatting works."""
    DataSlice(
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
        provider="mt5",
        retrieved_at="2026-06-18 10:00:00",
        normalized_at="2026-06-18 10:01:00",
    )

    StrategyInput(
        start_time="2026-06-18 10:00:00",
        end_time="2026-06-18 11:00:00",
    )

    intent = OrderIntent(
        intent_id="intent_1",
        symbol="EURUSD",
        action="buy",
        volume=1.0,
        order_type="market",
        risk_decision_id="dec_1",
    )

    TradeRequest(
        execution_request_id="req_1",
        order_intent=intent,
        submitted_at="2026-06-18 10:00:00",
        execution_provider="mt5",
        account_id="acc_123",
    )

    TradeResult(
        trade_id="trd_1",
        execution_request_id="req_1",
        status="filled",
    )

    Fill(
        fill_id="f_1",
        order_id="ticket_1",
        symbol="EURUSD",
        price=1.1000,
        quantity=1.0,
        provider_deal_id="deal_1",
        timestamp="2026-06-18 10:00:00",
    )

    req = TradeRequest(
        execution_request_id="req_1",
        order_intent=intent,
        submitted_at="2026-06-18 10:00:00",
        execution_provider="mt5",
        account_id="acc_123",
    )
    assert req.request_id is None
    assert req.execution_request_id == "req_1"

    ExecutionReport(
        report_id="rep_1",
        order_id="ticket_1",
        symbol="EURUSD",
        action="buy",
        status="filled",
        price=1.1000,
        quantity=1.0,
        cumulative_quantity=1.0,
        leaves_quantity=0.0,
        provider_order_id="po_1",
        timestamp="2026-06-18 10:00:00",
    )

    BrokerCapabilities(
        margin_mode="cross",
        hedging_netting_mode="netting",
    )

    AccountSnapshot(
        equity=10000.0,
        balance=10000.0,
        margin=0.0,
        free_margin=10000.0,
        currency="USD",
        leverage=100,
        timestamp="2026-06-18 10:00:00",
    )

    Position(
        position_id="pos_1",
        symbol="EURUSD",
        side="buy",
        quantity=1.0,
        average_price=1.1000,
        unrealized_pnl=50.0,
        provider_position_id="ticket_pos_1",
        opened_at="2026-06-18 10:00:00",
        updated_at="2026-06-18 10:05:00",
    )

    BacktestConfig(
        cost_model="standard",
        fill_model="close",
        calendar="continuous",
        split_policy="walk",
    )

    BacktestResult(
        run_id="run_1",
        config_hash="cfg_hash",
        journal_ref="URI1",
        equity_curve_ref="URI2",
        metrics_ref="URI3",
    )

    AuditEvent(
        event_id="evt_1",
        event_type="auth",
        severity="info",
        actor="operator",
        subject="admin",
        action="login",
    )

    RiskAuditEvent(
        event_id="evt_2",
        decision_id="dec_1",
        policy_name="drawdown",
        action_taken="approve",
        payload_hash="hash123",
        severity="info",
    )


def test_contract_round_trip_serialization() -> None:
    """Prove serialize → deserialize → re-serialize produces identical hashes."""
    import json

    original = Bar(
        timestamp="2026-06-18T10:00:00+00:00",
        open=1.10001,
        high=1.10500,
        low=1.09500,
        close=1.10200,
        volume=100.0,
        symbol="EURUSD",
        timeframe="M5",
        source="mt5",
    )

    json_str = original.to_json()

    raw_dict = json.loads(json_str)
    reconstructed = Bar.model_validate(raw_dict)

    assert original.contract_hash() == reconstructed.contract_hash(), (
        "contract_hash() changed after serialize → deserialize round-trip"
    )

    assert json_str == reconstructed.to_json(), (
        "to_json() output changed after serialize → deserialize round-trip"
    )
