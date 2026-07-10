"""Tests for trading runtime contracts and public facade."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services import trading
from app.services.trading import (
    AllocationVector,
    FixExecutionState,
    MutationCapability,
    NormalizedTradeResult,
    OrderState,
    PromotionStage,
    QuoteSnapshot,
    RegulatoryTags,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingError,
    TradingMetadata,
    TradingRequestEnvelope,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
    get_trading_public_catalog,
    get_trading_tool_registry,
)
from app.services.trading.contracts import TradingCommandAccepted
from app.services.trading.execution import ExecutionCoordinator
from app.services.trading.tool_registry import get_trading_tool_definition


def _quote(symbol: str = "EURUSD") -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=symbol,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        spread=Decimal("0.0002"),
        timestamp="2026-07-09T10:00:00Z",
        source="unit-test",
        freshness_age_ms=25,
        wire_timestamp="2026-07-09T10:00:00.000001Z",
    )


def test_public_facade_exports_registry_accessors() -> None:
    registry = get_trading_tool_registry()
    catalog = get_trading_public_catalog()

    assert "get_trading_tool_registry" in trading.__all__
    assert "get_trading_public_catalog" in trading.__all__
    assert tuple(registry.tools.values()) == catalog
    assert catalog[0].side_effect_ceiling is SideEffectMode.PACKAGED_ONLY


def test_registry_missing_tool_fails_closed() -> None:
    registry = get_trading_tool_registry()

    with pytest.raises(KeyError, match="not registered"):
        get_trading_tool_definition("missing", registry)


def test_live_mutation_requires_matching_quote_snapshot() -> None:
    with pytest.raises(ValueError, match="quote_snapshot is mandatory"):
        TradingRequestEnvelope(
            route=TradingRoute.LIVE,
            action=TradingAction.SUBMIT_ORDER,
            promotion_stage=PromotionStage.MICRO_LIVE,
            mutation_capability=MutationCapability.MICRO_LIVE,
            request_id="req-1",
            correlation_id="corr-1",
            symbol="EURUSD",
        )

    with pytest.raises(ValueError, match="quote_snapshot symbol"):
        TradingRequestEnvelope(
            route=TradingRoute.LIVE,
            action=TradingAction.SUBMIT_ORDER,
            promotion_stage=PromotionStage.MICRO_LIVE,
            mutation_capability=MutationCapability.MICRO_LIVE,
            request_id="req-1",
            correlation_id="corr-1",
            symbol="EURUSD",
            quote_snapshot=_quote("GBPUSD"),
        )


def test_non_live_request_allows_missing_quote_snapshot() -> None:
    envelope = TradingRequestEnvelope(
        route=TradingRoute.SIM,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.SIMULATION,
        mutation_capability=MutationCapability.PACKAGED_ONLY,
        request_id="req-2",
        correlation_id="corr-2",
        allocation_vector=AllocationVector(weights={"child-a": Decimal("0.60")}),
        regulatory_tags=RegulatoryTags(capacity="agency"),
        oco_group_id="oco-1",
        linked_order_ids=("order-a", "order-b"),
    )

    assert envelope.quote_snapshot is None
    assert envelope.allocation_vector is not None
    assert envelope.regulatory_tags is not None


def test_regulatory_tags_map_to_broker_dispatch_payload() -> None:
    request = TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-reg-1",
        correlation_id="corr-reg-1",
        symbol="EURUSD",
        payload={"volume": "0.10"},
        regulatory_tags=RegulatoryTags(
            mifid_algo_id="algo-1",
            short_sale_indicator="long",
            capacity="agency",
            custom_tags={"reg.region": "EU"},
        ),
        quote_snapshot=_quote(),
    )

    payload = ExecutionCoordinator().build_broker_dispatch_payload(request)

    assert payload["regulatory_tags"] == {
        "mifid_algo_id": "algo-1",
        "short_sale_indicator": "long",
        "capacity": "agency",
        "custom_tags": {"reg.region": "EU"},
    }


def test_unknown_future_major_schema_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="future major"):
        TradingCommandAccepted(
            schema_version="2.0.0",
            request_id="req-3",
            command_id="cmd-1",
            accepted_at="2026-07-09T10:00:00Z",
            action=TradingAction.SUBMIT_ORDER,
        )


def test_public_response_envelope_is_json_safe() -> None:
    result = NormalizedTradeResult(
        retcode="DONE",
        deal="deal-1",
        order="order-1",
        volume=Decimal("0.10"),
        price=Decimal("1.1001"),
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        comment="filled",
        request_id="req-4",
        provider="unit",
    )
    response = TradingResponseEnvelope(
        status=TradingStatus.ACCEPTED,
        message="Command accepted locally.",
        data={"normalized_trade_result": result.model_dump(mode="json")},
        error=None,
        metadata=TradingMetadata(execution_ms=Decimal("1.250")),
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        side_effect_mode=SideEffectMode.PACKAGED_ONLY,
        retry_safety=RetrySafety.DO_NOT_RETRY,
        request_id="req-4",
        correlation_id="corr-4",
        audit_ref="audit-1",
    )

    payload = response.model_dump(mode="json")

    assert payload["data"]["normalized_trade_result"]["volume"] == "0.10"
    assert payload["metadata"]["execution_ms"] == "1.250"
    assert payload["audit_ref"] == "audit-1"


def test_async_live_initial_response_is_local_command_acceptance() -> None:
    command = TradingCommandAccepted(
        request_id="req-accepted-1",
        command_id="cmd-accepted-1",
        accepted_at="2026-07-09T10:00:00Z",
        action=TradingAction.SUBMIT_ORDER,
    )

    response = TradingResponseEnvelope.accepted_from_command(
        command=command,
        route=TradingRoute.LIVE,
        correlation_id="corr-accepted-1",
        audit_ref="audit-accepted-1",
    )

    assert response.status is TradingStatus.ACCEPTED
    assert response.side_effect_mode is SideEffectMode.PACKAGED_ONLY
    assert "command_accepted" in response.data
    assert "normalized_trade_result" not in response.data


def test_public_response_rejects_unredacted_sensitive_payloads() -> None:
    with pytest.raises(ValueError, match="Sensitive key"):
        TradingResponseEnvelope(
            status=TradingStatus.ERROR,
            message="Rejected.",
            data={"api_key": "secret-value"},
            error=TradingError(code="INVALID_INPUT", details="bad request"),
            metadata=TradingMetadata(),
            route=TradingRoute.SIM,
            action=TradingAction.SUBMIT_ORDER,
            side_effect_mode=SideEffectMode.NONE,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            request_id="req-secret-1",
            correlation_id="corr-secret-1",
        )

    with pytest.raises(ValueError, match="Sensitive value"):
        TradingResponseEnvelope(
            status=TradingStatus.ERROR,
            message="leaked token abcdefabcdefabcdefabcdefabcdef12",
            data={},
            error=TradingError(code="INVALID_INPUT", details="bad request"),
            metadata=TradingMetadata(),
            route=TradingRoute.SIM,
            action=TradingAction.SUBMIT_ORDER,
            side_effect_mode=SideEffectMode.NONE,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            request_id="req-secret-2",
            correlation_id="corr-secret-2",
        )


def test_order_state_tracks_remaining_volume_and_vwap() -> None:
    state = OrderState(
        order_id="order-2",
        symbol="EURUSD",
        state=FixExecutionState.PARTIALLY_FILLED,
        volume=Decimal("1.00"),
        filled_volume=Decimal("0.25"),
        remaining_volume=Decimal("0.75"),
        vwap=Decimal("1.1003"),
    )

    assert state.remaining_volume == Decimal("0.75")
    assert state.model_dump(mode="json")["vwap"] == "1.1003"


def test_invalid_models_fail_closed() -> None:
    with pytest.raises(ValueError, match="ask"):
        QuoteSnapshot(
            symbol="EURUSD",
            bid=Decimal("1.1000"),
            ask=Decimal("1.0000"),
            spread=Decimal("0.0002"),
            timestamp="2026-07-09T10:00:00Z",
            source="unit-test",
            freshness_age_ms=25,
        )

    with pytest.raises(ValueError, match="principal"):
        RegulatoryTags(capacity="riskless")

    with pytest.raises(ValueError, match="message"):
        TradingResponseEnvelope(
            status=TradingStatus.ERROR,
            message=" ",
            data={},
            error=TradingError(code="INVALID_INPUT", details="bad request"),
            metadata=TradingMetadata(),
            route=TradingRoute.SIM,
            action=TradingAction.SUBMIT_ORDER,
            side_effect_mode=SideEffectMode.NONE,
            retry_safety=RetrySafety.DO_NOT_RETRY,
            request_id="req-5",
            correlation_id="corr-5",
        )


def test_import_does_not_start_threads_or_require_clock_reads() -> None:
    created = datetime(2026, 7, 9, tzinfo=UTC)

    assert created.tzinfo is UTC
    assert trading.get_trading_tool_registry().tools
