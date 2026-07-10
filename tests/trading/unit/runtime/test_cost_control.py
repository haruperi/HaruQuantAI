"""Unit tests for the cost control and budget evaluation runtime module."""

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
)
from app.services.trading.runtime.cost_control import CostController
from app.services.trading.security.error_mapping import TradingValidationError


class MockSignalsManager:
    """Mock incident signals manager."""

    def __init__(self) -> None:
        self.signals: list[tuple[str, str, str]] = []

    def emit_signal(self, incident_class: str, severity: str, message: str) -> None:
        self.signals.append((incident_class, severity, message))


def test_cost_controller_pre_dispatch_budget_validation() -> None:
    """Verify pre-dispatch budget validation check checks all scopes (TRD-FR-077, TRD-FR-078)."""
    controller = CostController()
    req = TradingRequestEnvelope(
        route=TradingRoute.SIM,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.READ_ONLY,
        request_id="req-1",
        correlation_id="wf-123",
        payload={"strategy_id": "strat-1", "tenant_id": "acct-1"},
    )

    limits = {
        "request_max": Decimal("10.0"),
        "workflow_max": Decimal("500.0"),
        "strategy_max": Decimal("100.0"),
        "account_max": Decimal("500.0"),
        "session_max": Decimal("500.0"),
    }

    # 1. Under limit succeeds
    controller.validate_pre_dispatch_budget(
        request=req, estimated_cost=Decimal("5.0"), limits=limits
    )

    # 2. Exceeding request_max -> Fail
    with pytest.raises(TradingValidationError, match="request budget limit"):
        controller.validate_pre_dispatch_budget(
            request=req, estimated_cost=Decimal("15.0"), limits=limits
        )

    # 3. Exceeding strategy_max -> Fail
    controller.record_cost(request=req, actual_cost=Decimal("96.0"), limits=limits)
    with pytest.raises(TradingValidationError, match="strategy budget limit"):
        controller.validate_pre_dispatch_budget(
            request=req, estimated_cost=Decimal("5.0"), limits=limits
        )

    # Reset
    controller.reset_accumulated_costs()
    controller.validate_pre_dispatch_budget(
        request=req, estimated_cost=Decimal("5.0"), limits=limits
    )


def test_cost_controller_post_dispatch_breach() -> None:
    """Verify post-dispatch actual cost breach raises a critical incident signal (TRD-FR-078)."""
    signals = MockSignalsManager()
    controller = CostController(signals_manager=signals)

    quote = QuoteSnapshot(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        spread=Decimal("0.0002"),
        timestamp="2026-07-09T10:00:00Z",
        source="test",
        freshness_age_ms=10,
    )

    req = TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="wf-123",
        quote_snapshot=quote,
        payload={"strategy_id": "strat-1", "tenant_id": "acct-1"},
    )

    limits = {
        "strategy_max": Decimal("50.0"),
    }

    # Record cost under limit -> No signal
    controller.record_cost(
        request=req, actual_cost=Decimal("40.0"), limits=limits, post_dispatch=True
    )
    assert len(signals.signals) == 0

    # Record cost exceeding limit -> Emits CRITICAL signal
    controller.record_cost(
        request=req, actual_cost=Decimal("15.0"), limits=limits, post_dispatch=True
    )
    assert len(signals.signals) == 1
    assert "cost_budget_breach" in signals.signals[0][0]
    assert signals.signals[0][1] == "CRITICAL"
