# ruff: noqa: ARG002, ARG005 -- test doubles mirror real port signatures.
"""Integration tests: actions/* dispatch for real once a pipeline is injected.

BF-TRD-005. ``trader.Trade.set_kill_switch(flatten_positions=True)`` genuinely
cancelled orders and closed positions through the broker. The ``trading``
equivalents package the intent. These tests prove that behavior returns as soon
as a ``LiveGatePipeline`` is injected -- and, crucially, that it stays
``packaged_only`` when one is not.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.trading.actions._common import TradingActionDependencies
from app.services.trading.actions.emergency import flatten_account
from app.services.trading.actions.orders import buy
from app.services.trading.actions.positions import position_close
from app.services.trading.actions.validation import (
    AccountMarginContext,
    DailyRailState,
    DefenseInDepthRailLimits,
    MarketSessionEvidence,
    OrderValidationContext,
    SymbolTradingConstraints,
)
from app.services.trading.contracts import (
    MutationCapability,
    PromotionStage,
    SideEffectMode,
    TradingAction,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.gates.policy_matrix import PolicyMatrix, PolicyMatrixEntry

from tests.services.trading.gates.test_live_pipeline import (
    SYMBOL,
    FakeClock,
    LiveGatePipelineImpl,
    _evidence,
    _pipeline,
    _quote,
)


class RNG:
    def random(self) -> float:
        return 0.5

    def randint(self, lo: int, hi: int) -> int:
        return lo


def _all_actions_policy(**kw) -> PolicyMatrix:
    return PolicyMatrix(
        entries={
            action: PolicyMatrixEntry(
                action=action, requires_approval=False, **kw
            )
            for action in TradingAction
        }
    )


def _context() -> OrderValidationContext:
    return OrderValidationContext(
        route=TradingRoute.LIVE,
        reference_price=Decimal("1.10000"),
        constraints=SymbolTradingConstraints(
            symbol=SYMBOL,
            digits=5,
            volume_min=Decimal("0.01"),
            volume_max=Decimal(100),
            volume_step=Decimal("0.01"),
            tick_size=Decimal("0.00001"),
            contract_size=Decimal(100000),
            quote_currency="USD",
        ),
        account_margin=AccountMarginContext(
            account_currency="USD", leverage=100, free_margin=Decimal(100000)
        ),
        market_session=MarketSessionEvidence(
            symbol=SYMBOL,
            source="test",
            is_open=True,
            freshness_age_ms=5,
            ttl_ms=60000,
        ),
        fat_finger_ceiling=Decimal(1000000),
        rail_limits=DefenseInDepthRailLimits(
            max_mutation_attempts_per_window=100,
            window_seconds=60,
            max_open_positions=100,
            daily_notional_ceiling=Decimal(10000000),
        ),
        rail_state=DailyRailState(
            mutation_attempts_in_window=0,
            open_positions_count=0,
            cumulative_daily_notional=Decimal(0),
        ),
    )


def _deps(pipeline: LiveGatePipelineImpl | None) -> TradingActionDependencies:
    return TradingActionDependencies(
        clock=FakeClock(),
        rng=RNG(),
        tenant_id="tenant-1",
        gate_pipeline=pipeline,
    )


def test_buy_is_packaged_only_without_a_pipeline() -> None:
    """The fail-closed default must survive this refactor."""
    response = buy(
        symbol=SYMBOL,
        volume=Decimal("0.10"),
        deviation_points=20,
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        context=_context(),
        deps=_deps(None),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.PACKAGED_ONLY


def test_buy_dispatches_with_a_pipeline_injected() -> None:
    pipeline, broker = _pipeline(policy_matrix=_all_actions_policy())
    response = buy(
        symbol=SYMBOL,
        volume=Decimal("0.10"),
        deviation_points=20,
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        context=_context(),
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_CONFIRMED
    assert response.status is TradingStatus.SUCCESS
    assert len(broker.payloads) == 1


def test_buy_dispatch_payload_carries_the_validated_intent() -> None:
    pipeline, broker = _pipeline(policy_matrix=_all_actions_policy())
    buy(
        symbol=SYMBOL,
        volume=Decimal("0.10"),
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        deviation_points=20,
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        context=_context(),
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    intent = broker.payloads[0]["intent"]
    assert intent["symbol"] == SYMBOL
    assert intent["side"] == "buy"
    assert Decimal(intent["volume"]) == Decimal("0.10")


def test_position_close_partial_volume_dispatches() -> None:
    """trader had no partial-close API; the usage example reached into
    the private ``Trade._send_request``. ``position_close(volume=...)`` is the
    public replacement (BF-TRD-007).
    """
    from app.services.trading.actions.positions import NettingMode

    pipeline, broker = _pipeline(policy_matrix=_all_actions_policy())
    response = position_close(
        netting_mode=NettingMode.HEDGING,
        ticket="pos-1",
        volume=Decimal("0.01"),
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-close",
        correlation_id="corr-1",
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_CONFIRMED
    assert Decimal(broker.payloads[0]["volume"]) == Decimal("0.01")


def test_flatten_account_is_packaged_only_without_a_pipeline(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.trading.actions.emergency.broker_call",
        lambda name, *a, **k: [],
    )
    response = flatten_account(
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-flat",
        correlation_id="corr-1",
        deps=_deps(None),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.PACKAGED_ONLY


def test_flatten_account_dispatches_with_a_pipeline(monkeypatch) -> None:
    """Kill-switch flattening reaches the broker again once wired."""
    monkeypatch.setattr(
        "app.services.trading.actions.emergency.broker_call",
        lambda name, *a, **k: [],
    )
    pipeline, broker = _pipeline(policy_matrix=_all_actions_policy())
    response = flatten_account(
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-flat",
        correlation_id="corr-1",
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.BROKER_MUTATION_CONFIRMED
    # A flatten is cancel_all_orders + close_all_positions: two dispatches.
    assert len(broker.payloads) == 2


def test_flatten_account_reports_dispatch_not_packaged_only(monkeypatch) -> None:
    """Regression: _flatten used to hardcode PACKAGED_ONLY regardless of
    what its children did, so an emergency flatten that reached the broker
    reported that nothing happened.
    """
    monkeypatch.setattr(
        "app.services.trading.actions.emergency.broker_call",
        lambda name, *a, **k: [],
    )
    pipeline, _ = _pipeline(policy_matrix=_all_actions_policy())
    response = flatten_account(
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-flat",
        correlation_id="corr-1",
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is not SideEffectMode.PACKAGED_ONLY
    assert response.status is TradingStatus.SUCCESS
    assert response.metadata.trades is True
    assert "packaged" not in response.message.lower()


def test_flatten_account_is_blocked_by_a_failing_gate(monkeypatch) -> None:
    """Emergency actions still pass through every gate; they are not a bypass."""
    monkeypatch.setattr(
        "app.services.trading.actions.emergency.broker_call",
        lambda name, *a, **k: [],
    )
    from app.services.trading.gates.readiness import BrokerReadinessEvidence

    pipeline, broker = _pipeline(
        policy_matrix=_all_actions_policy(),
        evidence=_evidence(
            broker_readiness=BrokerReadinessEvidence(
                connected=False,
                trade_allowed=True,
                account_permissions_ok=True,
                rate_limit_available=True,
            )
        ),
    )
    response = flatten_account(
        route=TradingRoute.LIVE,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-flat",
        correlation_id="corr-1",
        deps=_deps(pipeline),
        quote_snapshot=_quote(),
    )
    assert response.side_effect_mode is SideEffectMode.NONE
    assert broker.payloads == []
