"""Unit tests for broker response and execution event classification."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.contracts import NormalizedTradeResult, RetrySafety
from app.services.trading.execution.response_classifier import (
    UNKNOWN_OUTCOME_RETCODE,
    BrokerInitiatedEventKind,
    BrokerOutcomeStatus,
    CorporateActionKind,
    classify_broker_initiated_event,
    classify_broker_outcome,
    classify_corporate_action,
    classify_stream_event,
    normalize_broker_response,
)
from app.services.trading.security.error_mapping import TradingMappedError


class RawResponse:
    """Simple attribute-carrying broker response double."""

    def __init__(self, **fields: object) -> None:
        for key, value in fields.items():
            setattr(self, key, value)


def _normalized(**overrides: object) -> NormalizedTradeResult:
    defaults: dict[str, object] = {
        "retcode": "10009",
        "request_id": "req-1",
        "provider": "mt5",
    }
    defaults.update(overrides)
    return NormalizedTradeResult(**defaults)  # type: ignore[arg-type]


def test_normalize_broker_response_rejects_blank_provider_or_request_id() -> None:
    """normalize_broker_response fails closed on blank identifiers."""
    with pytest.raises(TradingMappedError):
        normalize_broker_response(provider=" ", raw_response={}, request_id="req-1")
    with pytest.raises(TradingMappedError):
        normalize_broker_response(provider="mt5", raw_response={}, request_id=" ")


def test_normalize_broker_response_extracts_fields_from_object() -> None:
    """normalize_broker_response extracts fields from an attribute-based response."""
    raw = RawResponse(
        retcode="10009",
        deal="1001",
        order="2002",
        volume=0.10,
        price=1.1000,
        bid=1.0999,
        ask=1.1001,
        comment="ok",
    )
    result = normalize_broker_response(
        provider="mt5", raw_response=raw, request_id="req-1"
    )
    assert result.retcode == "10009"
    assert result.deal == "1001"
    assert result.volume == Decimal("0.1")
    assert result.provider == "mt5"


def test_normalize_broker_response_extracts_fields_from_mapping() -> None:
    """normalize_broker_response extracts fields from a plain mapping."""
    raw = {"retcode": "10006", "comment": "reject"}
    result = normalize_broker_response(
        provider="ctrader", raw_response=raw, request_id="req-2"
    )
    assert result.retcode == "10006"
    assert result.comment == "reject"
    assert result.deal is None


def test_normalize_broker_response_falls_back_to_unknown_retcode() -> None:
    """A missing retcode falls back to the unknown-outcome sentinel."""
    result = normalize_broker_response(
        provider="mt5", raw_response={}, request_id="req-3"
    )
    assert result.retcode == UNKNOWN_OUTCOME_RETCODE


def test_normalize_broker_response_ignores_unparsable_decimal_fields() -> None:
    """Unparsable numeric fields degrade to None instead of raising."""
    raw = {"retcode": "10009", "volume": "not-a-number"}
    result = normalize_broker_response(
        provider="mt5", raw_response=raw, request_id="req-4"
    )
    assert result.volume is None


def test_classify_stream_event_delegates_to_normalize_broker_response() -> None:
    """classify_stream_event normalizes a streamed execution event."""
    raw = {"retcode": "10009", "deal": "9001"}
    result = classify_stream_event(provider="mt5", raw_event=raw, request_id="req-5")
    assert result.deal == "9001"


def test_classify_broker_outcome_unknown_on_timeout_or_disconnect_or_malformed() -> (
    None
):
    """Timeout, disconnect, and malformed responses all classify as unknown."""
    normalized = _normalized()
    for kwargs in (
        {"timed_out": True},
        {"transport_disconnected": True},
        {"malformed": True},
    ):
        outcome = classify_broker_outcome(normalized=normalized, **kwargs)
        assert outcome.status is BrokerOutcomeStatus.UNKNOWN
        assert outcome.retry_safety is RetrySafety.DO_NOT_RETRY
        assert outcome.requires_reconciliation is True


def test_classify_broker_outcome_success() -> None:
    """A known success retcode classifies as success."""
    normalized = _normalized(retcode="10009")
    outcome = classify_broker_outcome(normalized=normalized)
    assert outcome.status is BrokerOutcomeStatus.SUCCESS
    assert outcome.requires_reconciliation is False


def test_classify_broker_outcome_rejected_transient() -> None:
    """A transient error retcode classifies as rejected with retry-after-delay."""
    normalized = _normalized(retcode="10004")
    outcome = classify_broker_outcome(normalized=normalized)
    assert outcome.status is BrokerOutcomeStatus.REJECTED
    assert outcome.retry_safety is RetrySafety.RETRY_AFTER_DELAY
    assert outcome.error_code == "TIMEOUT"


def test_classify_broker_outcome_rejected_permanent() -> None:
    """A permanent error retcode classifies as rejected with do-not-retry."""
    normalized = _normalized(retcode="10014")
    outcome = classify_broker_outcome(normalized=normalized)
    assert outcome.status is BrokerOutcomeStatus.REJECTED
    assert outcome.retry_safety is RetrySafety.DO_NOT_RETRY
    assert outcome.error_code == "VALIDATION_FAILED"


@pytest.mark.parametrize(
    ("comment", "expected_kind"),
    [
        ("Margin Call warning issued", BrokerInitiatedEventKind.MARGIN_CALL_ACTION),
        ("Stop Out triggered", BrokerInitiatedEventKind.STOP_OUT),
        ("so", BrokerInitiatedEventKind.STOP_OUT),
        ("Order expiration reached", BrokerInitiatedEventKind.EXPIRATION),
        ("sl triggered", BrokerInitiatedEventKind.SERVER_SIDE_SL_TP_FILL),
        ("tp triggered", BrokerInitiatedEventKind.SERVER_SIDE_SL_TP_FILL),
        ("manual broker adjustment", BrokerInitiatedEventKind.BROKER_ADMIN_ACTION),
    ],
)
def test_classify_broker_initiated_event_kinds(
    comment: str, expected_kind: BrokerInitiatedEventKind
) -> None:
    """Broker-initiated events classify by comment keyword matching."""
    normalized = _normalized(comment=comment)
    event = classify_broker_initiated_event(normalized=normalized)
    assert event.kind is expected_kind


def test_classify_broker_initiated_event_flags_critical_incident() -> None:
    """stop_out and margin_call_action require a critical incident."""
    stop_out = classify_broker_initiated_event(
        normalized=_normalized(comment="stop out")
    )
    margin_call = classify_broker_initiated_event(
        normalized=_normalized(comment="margin call")
    )
    admin = classify_broker_initiated_event(normalized=_normalized(comment="manual"))
    assert stop_out.requires_critical_incident is True
    assert stop_out.recommended_operational_mode == "close_only"
    assert margin_call.requires_critical_incident is True
    assert admin.requires_critical_incident is False
    assert admin.recommended_operational_mode is None


def test_classify_corporate_action_rejects_unknown_action_type() -> None:
    """classify_corporate_action fails closed for an unrecognized action_type."""
    with pytest.raises(TradingMappedError):
        classify_corporate_action(raw_event={"action_type": "unknown"})


def test_classify_corporate_action_split_requires_ratio() -> None:
    """A split corporate action requires a ratio."""
    with pytest.raises(ValueError, match="ratio"):
        classify_corporate_action(
            raw_event={
                "action_type": "split",
                "symbol": "AAPL",
                "effective_at": "2026-07-09",
            }
        )
    event = classify_corporate_action(
        raw_event={
            "action_type": "split",
            "symbol": "AAPL",
            "ratio": "2",
            "effective_at": "2026-07-09",
        }
    )
    assert event.kind is CorporateActionKind.SPLIT
    assert event.ratio == Decimal(2)


def test_classify_corporate_action_symbol_change_requires_new_symbol() -> None:
    """A symbol_change corporate action requires new_symbol."""
    with pytest.raises(ValueError, match="new_symbol"):
        classify_corporate_action(
            raw_event={
                "action_type": "symbol_change",
                "symbol": "OLD",
                "effective_at": "2026-07-09",
            }
        )
    event = classify_corporate_action(
        raw_event={
            "action_type": "symbol_change",
            "symbol": "OLD",
            "new_symbol": "NEW",
            "effective_at": "2026-07-09",
        }
    )
    assert event.kind is CorporateActionKind.SYMBOL_CHANGE
    assert event.new_symbol == "NEW"
