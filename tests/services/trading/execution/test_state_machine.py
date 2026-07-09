"""Unit tests for the order/position lifecycle state machine."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.contracts import FixExecutionState, RetrySafety
from app.services.trading.execution.state_machine import (
    AmendmentKind,
    AmendmentOutcome,
    LifecycleKind,
    StateTransitionEvent,
    TransitionRecord,
    apply_execution_report,
    evaluate_amendment,
    initialize_transition_record,
    is_terminal_state,
    validate_transition,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)


def _record(**overrides: object) -> TransitionRecord:
    defaults: dict[str, object] = {
        "entity_id": "order-1",
        "kind": LifecycleKind.ORDER,
        "state": FixExecutionState.SUBMITTED,
        "version": 1,
        "filled_volume": Decimal(0),
        "remaining_volume": Decimal("1.00"),
    }
    defaults.update(overrides)
    return TransitionRecord(**defaults)  # type: ignore[arg-type]


def test_transition_record_rejects_blank_entity_id() -> None:
    """TransitionRecord fails closed on a blank entity_id."""
    with pytest.raises(ValueError, match="entity_id"):
        _record(entity_id=" ")


def test_initialize_transition_record_starts_at_version_one() -> None:
    """A freshly initialized record starts unfilled at version 1."""
    record = initialize_transition_record(
        entity_id="order-2", kind=LifecycleKind.ORDER, volume=Decimal("2.0")
    )
    assert record.version == 1
    assert record.state is FixExecutionState.SUBMITTED
    assert record.filled_volume == Decimal(0)
    assert record.remaining_volume == Decimal("2.0")


@pytest.mark.parametrize(
    "field_name",
    [
        "entity_id",
        "event_source",
        "timestamp",
        "broker_event_id",
        "request_id",
        "correlation_id",
    ],
)
def test_state_transition_event_rejects_blank_fields(field_name: str) -> None:
    """StateTransitionEvent fails closed when any identifier field is blank."""
    fields: dict[str, object] = {
        "entity_id": "order-1",
        "kind": LifecycleKind.ORDER,
        "event_source": "broker_execution_report",
        "timestamp": "2026-07-09T10:00:00Z",
        "broker_event_id": "evt-1",
        "request_id": "req-1",
        "correlation_id": "corr-1",
        "previous_state_version": 1,
        "from_state": FixExecutionState.SUBMITTED,
        "to_state": FixExecutionState.PARTIALLY_FILLED,
    }
    fields[field_name] = " "
    with pytest.raises(ValueError, match="must be non-empty"):
        StateTransitionEvent(**fields)  # type: ignore[arg-type]


def test_state_transition_event_accepts_fully_populated_fields() -> None:
    """StateTransitionEvent accepts a fully populated event."""
    event = StateTransitionEvent(
        entity_id="order-1",
        kind=LifecycleKind.ORDER,
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        broker_event_id="evt-1",
        request_id="req-1",
        correlation_id="corr-1",
        previous_state_version=1,
        from_state=FixExecutionState.SUBMITTED,
        to_state=FixExecutionState.PARTIALLY_FILLED,
    )
    assert event.broker_event_id == "evt-1"


@pytest.mark.parametrize(
    "state",
    [
        FixExecutionState.FILLED,
        FixExecutionState.CANCELLED,
        FixExecutionState.EXPIRED,
        FixExecutionState.REJECTED,
        FixExecutionState.REPLACED,
    ],
)
def test_is_terminal_state_true_for_terminal_states(state: FixExecutionState) -> None:
    """Terminal states report True."""
    assert is_terminal_state(state) is True


@pytest.mark.parametrize(
    "state",
    [
        FixExecutionState.SUBMITTED,
        FixExecutionState.PARTIALLY_FILLED,
        FixExecutionState.PENDING_CANCEL,
    ],
)
def test_is_terminal_state_false_for_open_states(state: FixExecutionState) -> None:
    """Open states report False."""
    assert is_terminal_state(state) is False


def test_validate_transition_accepts_enumerated_paths() -> None:
    """Enumerated transitions pass validation."""
    validate_transition(
        from_state=FixExecutionState.SUBMITTED,
        to_state=FixExecutionState.PARTIALLY_FILLED,
    )
    validate_transition(
        from_state=FixExecutionState.PARTIALLY_FILLED,
        to_state=FixExecutionState.FILLED,
    )
    validate_transition(
        from_state=FixExecutionState.PENDING_CANCEL,
        to_state=FixExecutionState.CANCELLED,
    )


def test_validate_transition_rejects_illegal_paths() -> None:
    """Illegal transitions fail closed (TRD-FR-126 examples)."""
    with pytest.raises(TradingValidationError):
        validate_transition(
            from_state=FixExecutionState.FILLED,
            to_state=FixExecutionState.SUBMITTED,
        )
    with pytest.raises(TradingValidationError):
        validate_transition(
            from_state=FixExecutionState.CANCELLED,
            to_state=FixExecutionState.PARTIALLY_FILLED,
        )


def test_evaluate_amendment_accepts_cancel_when_amendable_and_version_matches() -> None:
    """A cancel is accepted when the version matches and state is cancellable."""
    record = _record(state=FixExecutionState.SUBMITTED, version=3)
    result = evaluate_amendment(
        record=record, expected_state_version=3, amendment_kind=AmendmentKind.CANCEL
    )
    assert result.outcome is AmendmentOutcome.ACCEPTED
    assert result.retry_safety is RetrySafety.SAFE_TO_RETRY


def test_evaluate_amendment_accepts_modify_when_amendable_and_version_matches() -> None:
    """A modify is accepted when the version matches and state is modifiable."""
    record = _record(state=FixExecutionState.PARTIALLY_FILLED, version=2)
    result = evaluate_amendment(
        record=record, expected_state_version=2, amendment_kind=AmendmentKind.MODIFY
    )
    assert result.outcome is AmendmentOutcome.ACCEPTED
    assert result.retry_safety is RetrySafety.SAFE_TO_RETRY


def test_evaluate_amendment_cancel_too_late_when_state_not_cancellable() -> None:
    """A cancel against a non-cancellable state resolves to TOO_LATE_TO_CANCEL."""
    record = _record(state=FixExecutionState.PENDING_CANCEL, version=1)
    result = evaluate_amendment(
        record=record, expected_state_version=1, amendment_kind=AmendmentKind.CANCEL
    )
    assert result.outcome is AmendmentOutcome.TOO_LATE_TO_CANCEL
    assert result.retry_safety is RetrySafety.DO_NOT_RETRY


def test_evaluate_amendment_modify_too_late_when_state_not_modifiable() -> None:
    """A modify against a non-modifiable state resolves to TOO_LATE_TO_MODIFY."""
    record = _record(state=FixExecutionState.PENDING_CANCEL, version=1)
    result = evaluate_amendment(
        record=record, expected_state_version=1, amendment_kind=AmendmentKind.MODIFY
    )
    assert result.outcome is AmendmentOutcome.TOO_LATE_TO_MODIFY
    assert result.retry_safety is RetrySafety.DO_NOT_RETRY


def test_evaluate_amendment_cancel_after_partial_fill_version_mismatch() -> None:
    """A stale cancel against a partially filled order is AMENDED_AFTER_PARTIAL_FILL."""
    record = _record(state=FixExecutionState.PARTIALLY_FILLED, version=2)
    result = evaluate_amendment(
        record=record, expected_state_version=1, amendment_kind=AmendmentKind.CANCEL
    )
    assert result.outcome is AmendmentOutcome.AMENDED_AFTER_PARTIAL_FILL
    assert result.retry_safety is RetrySafety.DO_NOT_RETRY


def test_evaluate_amendment_modify_version_mismatch_on_open_state() -> None:
    """A stale modify against a version-advanced open order is TOO_LATE_TO_MODIFY."""
    record = _record(state=FixExecutionState.SUBMITTED, version=2)
    result = evaluate_amendment(
        record=record, expected_state_version=1, amendment_kind=AmendmentKind.MODIFY
    )
    assert result.outcome is AmendmentOutcome.TOO_LATE_TO_MODIFY
    assert result.retry_safety is RetrySafety.DO_NOT_RETRY


def test_apply_execution_report_rejects_blank_broker_event_id() -> None:
    """apply_execution_report rejects a blank broker_event_id."""
    record = _record()
    with pytest.raises(TradingMappedError):
        apply_execution_report(
            record=record,
            report_state=FixExecutionState.PARTIALLY_FILLED,
            broker_event_id=" ",
            event_source="broker_execution_report",
            timestamp="2026-07-09T10:00:00Z",
            request_id="req-1",
            correlation_id="corr-1",
            dedup_window_size=10,
        )


def test_apply_execution_report_rejects_invalid_dedup_window_size() -> None:
    """apply_execution_report rejects a non-positive dedup_window_size."""
    record = _record()
    with pytest.raises(TradingMappedError):
        apply_execution_report(
            record=record,
            report_state=FixExecutionState.PARTIALLY_FILLED,
            broker_event_id="evt-1",
            event_source="broker_execution_report",
            timestamp="2026-07-09T10:00:00Z",
            request_id="req-1",
            correlation_id="corr-1",
            dedup_window_size=0,
        )


def test_apply_execution_report_rejects_negative_filled_volume_delta() -> None:
    """apply_execution_report rejects a negative filled_volume_delta."""
    record = _record()
    with pytest.raises(TradingMappedError):
        apply_execution_report(
            record=record,
            report_state=FixExecutionState.PARTIALLY_FILLED,
            broker_event_id="evt-1",
            event_source="broker_execution_report",
            timestamp="2026-07-09T10:00:00Z",
            request_id="req-1",
            correlation_id="corr-1",
            dedup_window_size=10,
            filled_volume_delta=Decimal("-0.01"),
        )


def test_apply_execution_report_rejects_illegal_transition() -> None:
    """apply_execution_report propagates illegal-transition validation failures."""
    record = _record(state=FixExecutionState.FILLED, version=2)
    with pytest.raises(TradingValidationError):
        apply_execution_report(
            record=record,
            report_state=FixExecutionState.SUBMITTED,
            broker_event_id="evt-1",
            event_source="broker_execution_report",
            timestamp="2026-07-09T10:00:00Z",
            request_id="req-1",
            correlation_id="corr-1",
            dedup_window_size=10,
        )


def test_apply_execution_report_applies_partial_fill_and_tracks_vwap() -> None:
    """A partial fill updates filled/remaining volume, version, and VWAP."""
    record = _record(remaining_volume=Decimal("1.00"))
    result = apply_execution_report(
        record=record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="req-1",
        correlation_id="corr-1",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.40"),
        vwap=Decimal("1.10000"),
    )
    assert result.duplicate is False
    assert result.record.state is FixExecutionState.PARTIALLY_FILLED
    assert result.record.version == 2
    assert result.record.filled_volume == Decimal("0.40")
    assert result.record.remaining_volume == Decimal("0.60")
    assert result.record.vwap == Decimal("1.10000")
    assert result.event is not None
    assert result.event.previous_state_version == 1
    assert result.event.from_state is FixExecutionState.SUBMITTED
    assert result.event.to_state is FixExecutionState.PARTIALLY_FILLED


def test_apply_execution_report_preserves_vwap_when_not_reported() -> None:
    """VWAP is preserved from the prior record when not reported."""
    record = _record(remaining_volume=Decimal("1.00"), vwap=Decimal("1.09000"))
    result = apply_execution_report(
        record=record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="req-1",
        correlation_id="corr-1",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.10"),
    )
    assert result.record.vwap == Decimal("1.09000")


def test_apply_execution_report_clamps_remaining_volume_at_zero() -> None:
    """Remaining volume never goes negative on an over-reported fill."""
    record = _record(remaining_volume=Decimal("0.10"))
    result = apply_execution_report(
        record=record,
        report_state=FixExecutionState.FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="req-1",
        correlation_id="corr-1",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.50"),
    )
    assert result.record.remaining_volume == Decimal(0)


def test_apply_execution_report_deduplicates_repeated_broker_event_id() -> None:
    """A repeated broker_event_id is dropped without a state transition."""
    record = _record(remaining_volume=Decimal("1.00"))
    first = apply_execution_report(
        record=record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="req-1",
        correlation_id="corr-1",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.10"),
    )
    second = apply_execution_report(
        record=first.record,
        report_state=FixExecutionState.FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:01Z",
        request_id="req-2",
        correlation_id="corr-2",
        dedup_window_size=10,
        filled_volume_delta=Decimal("0.90"),
    )
    assert first.duplicate is False
    assert second.duplicate is True
    assert second.event is None
    assert second.record.version == first.record.version
    assert second.record.state is FixExecutionState.PARTIALLY_FILLED


def test_apply_execution_report_truncates_dedup_window() -> None:
    """The seen broker-event-id window is bounded to dedup_window_size."""
    record = _record(remaining_volume=Decimal("2.00"))
    first = apply_execution_report(
        record=record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="evt-1",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:00Z",
        request_id="req-1",
        correlation_id="corr-1",
        dedup_window_size=1,
        filled_volume_delta=Decimal("0.50"),
    )
    second = apply_execution_report(
        record=first.record,
        report_state=FixExecutionState.PARTIALLY_FILLED,
        broker_event_id="evt-2",
        event_source="broker_execution_report",
        timestamp="2026-07-09T10:00:01Z",
        request_id="req-2",
        correlation_id="corr-2",
        dedup_window_size=1,
        filled_volume_delta=Decimal("0.50"),
    )
    assert second.record.seen_broker_event_ids == ("evt-2",)
    assert "evt-1" not in second.record.seen_broker_event_ids
