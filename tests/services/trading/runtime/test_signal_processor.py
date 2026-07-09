"""Unit tests for the signal processor runtime module."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.contracts import (
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    TradingAction,
    TradingRequestEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.gates.pipeline import GatePipelineDecision
from app.services.trading.runtime.signal_processor import SignalProcessor
from app.services.trading.security.error_mapping import TradingValidationError


class MockPipelineRunner:
    """Mock gate pipeline runner."""

    def __init__(self, status: TradingStatus = TradingStatus.ACCEPTED) -> None:
        self.status = status
        self.called_with: TradingRequestEnvelope | None = None

    def __call__(self, envelope: TradingRequestEnvelope) -> GatePipelineDecision:
        self.called_with = envelope
        return GatePipelineDecision(
            status=self.status,
            steps=(),
            total_latency_ms=Decimal("1.2"),
        )


def test_signal_processor_valid_signal_translation() -> None:
    """Verify SignalProcessor converts a valid signal to envelope and runs pipeline (TRD-FR-080, TRD-FR-082)."""
    processor = SignalProcessor()
    runner = MockPipelineRunner()

    signal = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-123",
        "correlation_id": "corr-456",
        "symbol": "EURUSD",
        "strategy_id": "strat-abc",
        "payload": {"volume": 1.5},
    }

    envelope, decision = processor.process_strategy_signal(
        signal=signal,
        gate_pipeline_runner=runner,
    )

    assert envelope.route == TradingRoute.SIM
    assert envelope.action == TradingAction.SUBMIT_ORDER
    assert envelope.promotion_stage == PromotionStage.SIMULATION
    assert envelope.mutation_capability == MutationCapability.READ_ONLY
    assert envelope.request_id == "req-123"
    assert envelope.correlation_id == "corr-456"
    assert envelope.symbol == "EURUSD"
    assert envelope.payload["strategy_id"] == "strat-abc"
    assert envelope.payload["volume"] == 1.5

    assert runner.called_with is envelope
    assert decision.status == TradingStatus.ACCEPTED


def test_signal_processor_missing_attributes() -> None:
    """Verify SignalProcessor raises error if required attributes are missing (TRD-FR-081)."""
    processor = SignalProcessor()
    runner = MockPipelineRunner()

    # 1. Missing route
    signal1 = {
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-1",
        "correlation_id": "corr-1",
    }
    with pytest.raises(TradingValidationError, match="missing required 'route'"):
        processor.process_strategy_signal(signal=signal1, gate_pipeline_runner=runner)

    # 2. Missing promotion_stage
    signal_no_stage = {
        "route": "sim",
        "action": "submit_order",
        "mutation_capability": "read_only",
        "request_id": "req-1",
        "correlation_id": "corr-1",
    }
    with pytest.raises(
        TradingValidationError, match="missing required 'promotion_stage'"
    ):
        processor.process_strategy_signal(
            signal=signal_no_stage, gate_pipeline_runner=runner
        )

    # 3. Missing mutation_capability
    signal_no_cap = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "request_id": "req-1",
        "correlation_id": "corr-1",
    }
    with pytest.raises(
        TradingValidationError, match="missing required 'mutation_capability'"
    ):
        processor.process_strategy_signal(
            signal=signal_no_cap, gate_pipeline_runner=runner
        )

    # 4. Missing action
    signal_no_action = {
        "route": "sim",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-1",
        "correlation_id": "corr-1",
    }
    with pytest.raises(TradingValidationError, match="missing required 'action'"):
        processor.process_strategy_signal(
            signal=signal_no_action, gate_pipeline_runner=runner
        )

    # 5. Missing request_id
    signal_no_req = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "correlation_id": "corr-1",
    }
    with pytest.raises(TradingValidationError, match="missing required 'request_id'"):
        processor.process_strategy_signal(
            signal=signal_no_req, gate_pipeline_runner=runner
        )

    # 6. Missing correlation_id
    signal2 = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-1",
    }
    with pytest.raises(
        TradingValidationError, match="missing required 'correlation_id'"
    ):
        processor.process_strategy_signal(signal=signal2, gate_pipeline_runner=runner)


def test_signal_processor_invalid_enum_values() -> None:
    """Verify ValueError during enum coercion yields TradingValidationError."""
    processor = SignalProcessor()
    runner = MockPipelineRunner()

    base_signal = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-1",
        "correlation_id": "corr-1",
    }

    # Invalid route value
    sig = dict(base_signal, route="invalid-route")
    with pytest.raises(TradingValidationError, match="Invalid route value"):
        processor.process_strategy_signal(signal=sig, gate_pipeline_runner=runner)

    # Invalid stage value
    sig = dict(base_signal, promotion_stage="invalid-stage")
    with pytest.raises(TradingValidationError, match="Invalid promotion stage value"):
        processor.process_strategy_signal(signal=sig, gate_pipeline_runner=runner)

    # Invalid capability value
    sig = dict(base_signal, mutation_capability="invalid-capability")
    with pytest.raises(
        TradingValidationError, match="Invalid mutation capability value"
    ):
        processor.process_strategy_signal(signal=sig, gate_pipeline_runner=runner)

    # Invalid action value
    sig = dict(base_signal, action="invalid-action")
    with pytest.raises(TradingValidationError, match="Invalid action value"):
        processor.process_strategy_signal(signal=sig, gate_pipeline_runner=runner)


def test_signal_processor_live_mutation_constraints() -> None:
    """Verify live mutations enforce risk_decision_id, approvals, and quote snapshots (TRD-FR-081)."""
    processor = SignalProcessor()
    runner = MockPipelineRunner()

    signal = {
        "route": "live",
        "action": "submit_order",
        "promotion_stage": "micro_live",
        "mutation_capability": "micro_live",
        "request_id": "req-1",
        "correlation_id": "corr-1",
        "symbol": "EURUSD",
    }

    # 1. Missing risk_decision_id -> Fail
    with pytest.raises(TradingValidationError, match="require a 'risk_decision_id'"):
        processor.process_strategy_signal(signal=signal, gate_pipeline_runner=runner)

    # Add risk_decision_id
    signal["risk_decision_id"] = "risk-dec-abc"

    # 2. Missing approvals -> Fail
    with pytest.raises(TradingValidationError, match="require 'approvals' evidence"):
        processor.process_strategy_signal(signal=signal, gate_pipeline_runner=runner)

    # Add approvals
    signal["approvals"] = ()

    # 3. Missing quote snapshot -> Fail
    with pytest.raises(
        TradingValidationError, match="require a valid 'quote_snapshot'"
    ):
        processor.process_strategy_signal(signal=signal, gate_pipeline_runner=runner)

    # 4. Malformed quote snapshot dictionary -> Fail
    signal["quote_snapshot"] = {"symbol": "EURUSD", "bid": "not-a-number"}
    with pytest.raises(TradingValidationError, match="Malformed 'quote_snapshot'"):
        processor.process_strategy_signal(signal=signal, gate_pipeline_runner=runner)

    # 5. Correct quote snapshot dictionary format -> Succeeds
    signal["quote_snapshot"] = {
        "symbol": "EURUSD",
        "bid": 1.1000,
        "ask": 1.1002,
        "spread": 0.0002,
        "timestamp": "2026-07-09T10:00:00Z",
        "source": "test",
        "freshness_age_ms": 10,
    }

    envelope, decision = processor.process_strategy_signal(
        signal=signal,
        gate_pipeline_runner=runner,
    )
    assert envelope.quote_snapshot is not None
    assert envelope.quote_snapshot.symbol == "EURUSD"
    assert envelope.payload["risk_decision_id"] == "risk-dec-abc"

    # 6. Pass QuoteSnapshot instance directly
    signal["quote_snapshot"] = envelope.quote_snapshot
    envelope2, decision2 = processor.process_strategy_signal(
        signal=signal,
        gate_pipeline_runner=runner,
    )
    assert envelope2.quote_snapshot is signal["quote_snapshot"]


def test_signal_processor_non_live_quote_handling() -> None:
    """Verify quote snapshot dictionary conversion on non-live routes."""
    processor = SignalProcessor()
    runner = MockPipelineRunner()

    signal = {
        "route": "sim",
        "action": "submit_order",
        "promotion_stage": "simulation",
        "mutation_capability": "read_only",
        "request_id": "req-1",
        "correlation_id": "corr-1",
        "quote_snapshot": {
            "symbol": "EURUSD",
            "bid": 1.1000,
            "ask": 1.1002,
            "spread": 0.0002,
            "timestamp": "2026-07-09T10:00:00Z",
            "source": "test",
            "freshness_age_ms": 10,
        },
    }

    # 1. Valid dict -> Parse to QuoteSnapshot
    envelope, _ = processor.process_strategy_signal(
        signal=signal, gate_pipeline_runner=runner
    )
    assert isinstance(envelope.quote_snapshot, QuoteSnapshot)

    # 2. Malformed dict -> Silently ignore (set to None) for non-live
    signal["quote_snapshot"] = {"invalid": "dict"}
    envelope, _ = processor.process_strategy_signal(
        signal=signal, gate_pipeline_runner=runner
    )
    assert envelope.quote_snapshot is None
