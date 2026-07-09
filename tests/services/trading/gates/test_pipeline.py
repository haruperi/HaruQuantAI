"""Unit tests for the canonical live-route gate pipeline orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import QuoteSnapshot, TradingRoute, TradingStatus
from app.services.trading.execution.broker_capability_validation import (
    BrokerCapabilityProfile,
)
from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    GateStepStatus,
    blocked_step,
    passed_step,
)
from app.services.trading.gates.pipeline import (
    ComplianceEvidence,
    MarketTurbulenceMonitor,
    compute_effective_deadline,
    evaluate_adapter_permission_gate,
    evaluate_compliance_gate,
    evaluate_seam_gate,
    run_gate_pipeline,
)


class MutableClock:
    """Test clock with independently controllable UTC/monotonic values."""

    def __init__(self, *, now: datetime, monotonic_value: float = 0.0) -> None:
        """Initialize the clock at a fixed UTC time and monotonic value."""
        self._now = now
        self._monotonic = monotonic_value

    def now_utc(self) -> datetime:
        """Return the current fixed UTC timestamp."""
        return self._now

    def now_ptp(self) -> datetime:
        """Return the current fixed PTP timestamp."""
        return self._now

    def monotonic(self) -> float:
        """Return the current controllable monotonic value."""
        return self._monotonic

    def advance_monotonic(self, seconds: float) -> None:
        """Advance the monotonic clock by the given number of seconds."""
        self._monotonic += seconds


def _request(**overrides: object):
    from app.services.trading.contracts import (
        MutationCapability,
        PromotionStage,
        TradingAction,
        TradingRequestEnvelope,
    )

    defaults: dict[str, object] = {
        "route": TradingRoute.LIVE,
        "action": TradingAction.SUBMIT_ORDER,
        "promotion_stage": PromotionStage.MICRO_LIVE,
        "mutation_capability": MutationCapability.MICRO_LIVE,
        "request_id": "req-1",
        "correlation_id": "corr-1",
        "symbol": "EURUSD",
        "quote_snapshot": QuoteSnapshot(
            symbol="EURUSD",
            bid=Decimal("1.1000"),
            ask=Decimal("1.1002"),
            spread=Decimal("0.0002"),
            timestamp="2026-07-09T10:00:00Z",
            source="test",
            freshness_age_ms=10,
        ),
    }
    defaults.update(overrides)
    return TradingRequestEnvelope(**defaults)  # type: ignore[arg-type]


def test_evaluate_compliance_gate_passes_without_symbol() -> None:
    """No symbol on the request means no restriction can apply."""
    result = evaluate_compliance_gate(evidence=ComplianceEvidence(), symbol=None)
    assert result.status is GateStepStatus.PASSED


def test_evaluate_compliance_gate_passes_for_unrestricted_symbol() -> None:
    """An unrestricted symbol passes the compliance gate."""
    evidence = ComplianceEvidence(restricted_symbols=("XYZ",))
    result = evaluate_compliance_gate(evidence=evidence, symbol="EURUSD")
    assert result.status is GateStepStatus.PASSED


def test_evaluate_compliance_gate_blocks_restricted_symbol() -> None:
    """A restricted symbol is blocked."""
    evidence = ComplianceEvidence(restricted_symbols=("EURUSD",))
    result = evaluate_compliance_gate(evidence=evidence, symbol="EURUSD")
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "POLICY_BLOCKED"


def test_market_turbulence_monitor_rejects_small_window() -> None:
    """The monitor requires at least a 2-price window."""
    with pytest.raises(ValueError, match="window_size"):
        MarketTurbulenceMonitor(window_size=1, velocity_threshold_bps=Decimal(50))


def test_market_turbulence_monitor_blocks_when_already_suspended() -> None:
    """A suspended symbol blocks immediately without observing a new price."""
    monitor = MarketTurbulenceMonitor(window_size=3, velocity_threshold_bps=Decimal(50))
    monitor._suspended.add("EURUSD")
    result = monitor.observe(symbol="EURUSD", mid_price=Decimal("1.10000"))
    assert result.status is GateStepStatus.BLOCKED


def test_market_turbulence_monitor_passes_on_first_observation() -> None:
    """A single observation cannot yet compute velocity and passes."""
    monitor = MarketTurbulenceMonitor(window_size=3, velocity_threshold_bps=Decimal(50))
    result = monitor.observe(symbol="EURUSD", mid_price=Decimal("1.10000"))
    assert result.status is GateStepStatus.PASSED


def test_market_turbulence_monitor_passes_within_threshold() -> None:
    """A small price change within the threshold passes."""
    monitor = MarketTurbulenceMonitor(window_size=3, velocity_threshold_bps=Decimal(50))
    monitor.observe(symbol="EURUSD", mid_price=Decimal("1.10000"))
    result = monitor.observe(symbol="EURUSD", mid_price=Decimal("1.10010"))
    assert result.status is GateStepStatus.PASSED
    assert monitor.is_suspended(symbol="EURUSD") is False


def test_market_turbulence_monitor_blocks_and_suspends_on_excess_velocity() -> None:
    """A price change beyond the threshold blocks and suspends the symbol."""
    monitor = MarketTurbulenceMonitor(window_size=3, velocity_threshold_bps=Decimal(50))
    monitor.observe(symbol="EURUSD", mid_price=Decimal("1.10000"))
    result = monitor.observe(symbol="EURUSD", mid_price=Decimal("1.20000"))
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "CIRCUIT_OPEN"
    assert monitor.is_suspended(symbol="EURUSD") is True


def test_market_turbulence_monitor_resume_clears_suspension() -> None:
    """resume() clears a symbol's suspension."""
    monitor = MarketTurbulenceMonitor(window_size=3, velocity_threshold_bps=Decimal(50))
    monitor._suspended.add("EURUSD")
    monitor.resume(symbol="EURUSD")
    assert monitor.is_suspended(symbol="EURUSD") is False


def _capability_profile(**overrides: object) -> BrokerCapabilityProfile:
    defaults: dict[str, object] = {
        "provider": "mt5",
        "supported_order_types": ("market",),
        "supported_filling_modes": ("IOC",),
        "price_precision_digits": 5,
        "volume_precision_step": Decimal("0.01"),
        "max_requests_per_second": Decimal(10),
    }
    defaults.update(overrides)
    return BrokerCapabilityProfile(**defaults)  # type: ignore[arg-type]


def test_evaluate_adapter_permission_gate_passes() -> None:
    """A supported order type/filling mode/precision passes the gate."""
    result = evaluate_adapter_permission_gate(
        profile=_capability_profile(),
        order_type="market",
        filling_mode="IOC",
        price=Decimal("1.10000"),
        volume=Decimal("0.10"),
    )
    assert result.status is GateStepStatus.PASSED


def test_evaluate_adapter_permission_gate_blocks() -> None:
    """An unsupported order type blocks the gate."""
    result = evaluate_adapter_permission_gate(
        profile=_capability_profile(),
        order_type="stop_limit",
        filling_mode="IOC",
        price=Decimal("1.10000"),
        volume=Decimal("0.10"),
    )
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "VALIDATION_FAILED"


def test_evaluate_seam_gate_fails_closed_without_evaluator() -> None:
    """A seam gate with no injected evaluator fails closed."""
    result = evaluate_seam_gate(gate=GateName.SESSION_STATUS, evaluator=None)
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "LIVE_GATE_FAILED"


def test_evaluate_seam_gate_delegates_to_injected_evaluator() -> None:
    """A seam gate with an injected evaluator delegates to it."""
    result = evaluate_seam_gate(
        gate=GateName.SESSION_STATUS,
        evaluator=lambda: passed_step(gate=GateName.SESSION_STATUS),
    )
    assert result.status is GateStepStatus.PASSED


def test_compute_effective_deadline_uses_request_value() -> None:
    """An explicit request deadline is used verbatim."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    request = _request(deadline_utc="2026-07-09T10:00:05Z")
    deadline = compute_effective_deadline(
        request=request, clock=clock, default_budget_ms=Decimal(500)
    )
    assert deadline == datetime(2026, 7, 9, 10, 0, 5, tzinfo=UTC)


def test_compute_effective_deadline_defaults_from_budget() -> None:
    """An absent request deadline defaults from the configured gate budget."""
    now = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
    clock = MutableClock(now=now)
    request = _request()
    deadline = compute_effective_deadline(
        request=request, clock=clock, default_budget_ms=Decimal(500)
    )
    assert deadline == now + timedelta(milliseconds=500)


def test_run_gate_pipeline_passes_when_every_step_passes() -> None:
    """The pipeline accepts when every step passes."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    steps = (
        (GateName.COMPLIANCE, lambda: passed_step(gate=GateName.COMPLIANCE)),
        (
            GateName.MARKET_TURBULENCE,
            lambda: passed_step(gate=GateName.MARKET_TURBULENCE),
        ),
    )
    decision = run_gate_pipeline(
        steps=steps, clock=clock, deadline=clock.now_utc() + timedelta(seconds=1)
    )
    assert decision.status is TradingStatus.ACCEPTED
    assert decision.blocked_at_gate is None
    assert len(decision.steps) == 2


def test_run_gate_pipeline_short_circuits_on_first_failure() -> None:
    """Downstream steps are skipped once a gate blocks."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    steps = (
        (GateName.COMPLIANCE, lambda: passed_step(gate=GateName.COMPLIANCE)),
        (
            GateName.KILL_SWITCH,
            lambda: blocked_step(
                gate=GateName.KILL_SWITCH,
                reason_code="LIVE_KILL_SWITCH_ACTIVE",
                message="blocked",
            ),
        ),
        (
            GateName.OPERATOR_APPROVAL,
            lambda: passed_step(gate=GateName.OPERATOR_APPROVAL),
        ),
    )
    decision = run_gate_pipeline(
        steps=steps, clock=clock, deadline=clock.now_utc() + timedelta(seconds=1)
    )
    assert decision.status is TradingStatus.BLOCKED
    assert decision.blocked_at_gate is GateName.KILL_SWITCH
    assert decision.steps[0].status is GateStepStatus.PASSED
    assert decision.steps[1].status is GateStepStatus.BLOCKED
    assert decision.steps[2].status is GateStepStatus.SKIPPED
    assert decision.steps[2].diagnostic_after_failure is True


def test_run_gate_pipeline_blocks_when_deadline_already_exceeded() -> None:
    """A deadline already in the past blocks the very first gate."""
    now = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
    clock = MutableClock(now=now)
    steps = ((GateName.COMPLIANCE, lambda: passed_step(gate=GateName.COMPLIANCE)),)
    decision = run_gate_pipeline(
        steps=steps, clock=clock, deadline=now - timedelta(seconds=1)
    )
    assert decision.status is TradingStatus.BLOCKED
    assert decision.error_code == "DEADLINE_EXCEEDED"


def test_run_gate_pipeline_passes_with_fresh_quote_and_ttl() -> None:
    """A fresh quote snapshot within its TTL does not block the pipeline."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    quote = QuoteSnapshot(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        spread=Decimal("0.0002"),
        timestamp="2026-07-09T10:00:00Z",
        source="test",
        freshness_age_ms=10,
    )
    steps = ((GateName.COMPLIANCE, lambda: passed_step(gate=GateName.COMPLIANCE)),)
    decision = run_gate_pipeline(
        steps=steps,
        clock=clock,
        deadline=clock.now_utc() + timedelta(seconds=1),
        quote_snapshot=quote,
        quote_ttl_ms=1000,
    )
    assert decision.status is TradingStatus.ACCEPTED


def test_run_gate_pipeline_passes_with_quote_when_ttl_not_configured() -> None:
    """A quote snapshot without a configured TTL skips the staleness check."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    quote = QuoteSnapshot(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        spread=Decimal("0.0002"),
        timestamp="2026-07-09T10:00:00Z",
        source="test",
        freshness_age_ms=999_999,
    )
    steps = ((GateName.COMPLIANCE, lambda: passed_step(gate=GateName.COMPLIANCE)),)
    decision = run_gate_pipeline(
        steps=steps,
        clock=clock,
        deadline=clock.now_utc() + timedelta(seconds=1),
        quote_snapshot=quote,
        quote_ttl_ms=None,
    )
    assert decision.status is TradingStatus.ACCEPTED


def test_run_gate_pipeline_blocks_when_quote_goes_stale_mid_pipeline() -> None:
    """Cumulative elapsed pipeline time can push a quote past its TTL."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    quote = QuoteSnapshot(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        spread=Decimal("0.0002"),
        timestamp="2026-07-09T10:00:00Z",
        source="test",
        freshness_age_ms=900,
    )

    def _slow_step() -> GateStepResult:
        clock.advance_monotonic(0.2)
        return passed_step(gate=GateName.COMPLIANCE)

    steps = (
        (GateName.COMPLIANCE, _slow_step),
        (
            GateName.MARKET_TURBULENCE,
            lambda: passed_step(gate=GateName.MARKET_TURBULENCE),
        ),
    )
    decision = run_gate_pipeline(
        steps=steps,
        clock=clock,
        deadline=clock.now_utc() + timedelta(seconds=10),
        quote_snapshot=quote,
        quote_ttl_ms=1000,
    )
    assert decision.status is TradingStatus.BLOCKED
    assert decision.error_code == "QUOTE_STALE"
    assert decision.blocked_at_gate is GateName.MARKET_TURBULENCE


def test_run_gate_pipeline_accepts_empty_steps() -> None:
    """An empty step sequence trivially passes."""
    clock = MutableClock(now=datetime(2026, 7, 9, 10, 0, tzinfo=UTC))
    decision = run_gate_pipeline(
        steps=(), clock=clock, deadline=clock.now_utc() + timedelta(seconds=1)
    )
    assert decision.status is TradingStatus.ACCEPTED
    assert decision.steps == ()
