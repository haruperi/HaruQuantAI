"""Order and position lifecycle state machine primitives.

This module enforces valid FIX-style lifecycle transitions, version-gated
amendment resolution, and idempotent execution-report deduplication for both
order and position projections (TRD-FR-126 through TRD-FR-131). It performs
no broker calls and holds no process-wide state; callers own persistence of
the returned :class:`TransitionRecord` through the injected ``TradeStore``
and journaling of the returned :class:`StateTransitionEvent` through the
injected ``EventJournal``.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from app.services.trading.contracts import (
    FixExecutionState,
    RetrySafety,
    TradingContract,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)
from app.utils.logger import logger
from pydantic import Field, model_validator

_TERMINAL_STATES = frozenset(
    {
        FixExecutionState.FILLED,
        FixExecutionState.CANCELLED,
        FixExecutionState.EXPIRED,
        FixExecutionState.REJECTED,
        FixExecutionState.REPLACED,
    }
)

_VALID_TRANSITIONS: dict[FixExecutionState, frozenset[FixExecutionState]] = {
    FixExecutionState.SUBMITTED: frozenset(
        {
            FixExecutionState.PARTIALLY_FILLED,
            FixExecutionState.FILLED,
            FixExecutionState.PENDING_CANCEL,
            FixExecutionState.CANCELLED,
            FixExecutionState.EXPIRED,
            FixExecutionState.REPLACED,
            FixExecutionState.REJECTED,
        }
    ),
    FixExecutionState.PARTIALLY_FILLED: frozenset(
        {
            FixExecutionState.PARTIALLY_FILLED,
            FixExecutionState.FILLED,
            FixExecutionState.PENDING_CANCEL,
            FixExecutionState.CANCELLED,
            FixExecutionState.EXPIRED,
            FixExecutionState.REPLACED,
        }
    ),
    FixExecutionState.PENDING_CANCEL: frozenset(
        {
            FixExecutionState.CANCELLED,
            FixExecutionState.PARTIALLY_FILLED,
            FixExecutionState.FILLED,
        }
    ),
    FixExecutionState.FILLED: frozenset(),
    FixExecutionState.CANCELLED: frozenset(),
    FixExecutionState.EXPIRED: frozenset(),
    FixExecutionState.REJECTED: frozenset(),
    FixExecutionState.REPLACED: frozenset(),
}

_CANCELLABLE_STATES = frozenset(
    {FixExecutionState.SUBMITTED, FixExecutionState.PARTIALLY_FILLED}
)
_MODIFIABLE_STATES = frozenset(
    {FixExecutionState.SUBMITTED, FixExecutionState.PARTIALLY_FILLED}
)


class LifecycleKind(StrEnum):
    """Entity kind tracked by the state machine."""

    ORDER = "order"
    POSITION = "position"


class AmendmentKind(StrEnum):
    """Requested amendment kind for version-gated evaluation."""

    CANCEL = "cancel"
    MODIFY = "modify"


class AmendmentOutcome(StrEnum):
    """Explicit terminal outcome for a version-gated amendment request."""

    ACCEPTED = "accepted"
    TOO_LATE_TO_CANCEL = "too_late_to_cancel"
    TOO_LATE_TO_MODIFY = "too_late_to_modify"
    AMENDED_AFTER_PARTIAL_FILL = "amended_after_partial_fill"


class TransitionRecord(TradingContract):
    """Versioned lifecycle projection for one order or position.

    Attributes:
        entity_id: Local order or position identifier.
        kind: Whether this record tracks an order or a position.
        state: Current FIX-style lifecycle state.
        version: Monotonically increasing state version, starting at 1.
        filled_volume: Cumulative filled volume.
        remaining_volume: Remaining open volume.
        vwap: Volume-weighted average fill price.
        seen_broker_event_ids: Bounded window of recently applied broker
            execution event identifiers, used for duplicate detection.
    """

    entity_id: str
    kind: LifecycleKind
    state: FixExecutionState
    version: int = Field(ge=1)
    filled_volume: Decimal = Field(default=Decimal(0), ge=0)
    remaining_volume: Decimal = Field(default=Decimal(0), ge=0)
    vwap: Decimal | None = None
    seen_broker_event_ids: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_record(self) -> TransitionRecord:
        """Validate transition record identifiers.

        Returns:
            TransitionRecord: Validated transition record.

        Raises:
            ValueError: If ``entity_id`` is blank.
        """
        logger.info("Validating transition record for {}.", self.entity_id)
        if not self.entity_id.strip():
            raise ValueError("entity_id must be non-empty.")
        return self


class StateTransitionEvent(TradingContract):
    """Forensic record of one applied lifecycle state transition.

    Attributes:
        entity_id: Local order or position identifier.
        kind: Whether this event tracks an order or a position.
        event_source: Origin of the transition (e.g. broker execution report,
            reconciliation resolution, watchdog cancellation).
        timestamp: UTC timestamp supplied by an injected Clock.
        broker_event_id: Unique broker execution event identifier.
        request_id: Request identifier associated with the transition.
        correlation_id: Correlation identifier.
        previous_state_version: Version of the record before this transition.
        from_state: Prior lifecycle state.
        to_state: New lifecycle state.
    """

    entity_id: str
    kind: LifecycleKind
    event_source: str
    timestamp: str
    broker_event_id: str
    request_id: str
    correlation_id: str
    previous_state_version: int = Field(ge=1)
    from_state: FixExecutionState
    to_state: FixExecutionState

    @model_validator(mode="after")
    def validate_event(self) -> StateTransitionEvent:
        """Validate state transition event identifiers.

        Returns:
            StateTransitionEvent: Validated transition event.

        Raises:
            ValueError: If any required identifier field is blank.
        """
        logger.info("Validating state transition event for {}.", self.entity_id)
        for field_name in (
            "entity_id",
            "event_source",
            "timestamp",
            "broker_event_id",
            "request_id",
            "correlation_id",
        ):
            if not getattr(self, field_name).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self


class AmendmentResult(TradingContract):
    """Version-gated amendment evaluation outcome.

    Attributes:
        outcome: Explicit amendment outcome classification.
        retry_safety: Retry safety classification for the outcome.
    """

    outcome: AmendmentOutcome
    retry_safety: RetrySafety


class TransitionApplyResult(TradingContract):
    """Outcome of applying one execution report to a transition record.

    Attributes:
        record: Updated (or unchanged, if duplicate) transition record.
        event: Forensic transition event, or ``None`` when the report was a
            duplicate and no transition occurred.
        duplicate: Whether the report was dropped as a duplicate.
    """

    record: TransitionRecord
    event: StateTransitionEvent | None
    duplicate: bool


def is_terminal_state(state: FixExecutionState) -> bool:
    """Return whether a FIX-style lifecycle state is terminal.

    Args:
        state: Lifecycle state to check.

    Returns:
        bool: True when no further transitions are valid from this state.
    """
    logger.debug("Checking terminal state for {}.", state.value)
    return state in _TERMINAL_STATES


def validate_transition(
    *,
    from_state: FixExecutionState,
    to_state: FixExecutionState,
) -> None:
    """Validate a lifecycle state transition against the canonical table.

    Args:
        from_state: Current lifecycle state.
        to_state: Requested next lifecycle state.

    Raises:
        TradingValidationError: If the transition is not enumerated as valid.
    """
    logger.info("Validating transition {}->{}.", from_state.value, to_state.value)
    allowed = _VALID_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise TradingValidationError(
            "Illegal lifecycle state transition.",
            details={"from_state": from_state.value, "to_state": to_state.value},
        )
    logger.debug("Transition {}->{} is valid.", from_state.value, to_state.value)


def initialize_transition_record(
    *,
    entity_id: str,
    kind: LifecycleKind,
    volume: Decimal,
    initial_state: FixExecutionState = FixExecutionState.SUBMITTED,
) -> TransitionRecord:
    """Build a fresh version-1 transition record for a new order or position.

    Args:
        entity_id: Local order or position identifier.
        kind: Whether this record tracks an order or a position.
        volume: Initial requested volume, fully unfilled.
        initial_state: Starting lifecycle state.

    Returns:
        TransitionRecord: Freshly initialized transition record.
    """
    logger.info("Initializing transition record for {} ({}).", entity_id, kind.value)
    return TransitionRecord(
        entity_id=entity_id,
        kind=kind,
        state=initial_state,
        version=1,
        filled_volume=Decimal(0),
        remaining_volume=volume,
    )


def evaluate_amendment(
    *,
    record: TransitionRecord,
    expected_state_version: int,
    amendment_kind: AmendmentKind,
) -> AmendmentResult:
    """Evaluate a version-gated order amendment request (TRD-FR-129/130).

    If the authoritative state has advanced beyond ``expected_state_version``,
    or the current state is not in the enumerated amendable set for this
    amendment kind, resolution is an explicit terminal outcome with
    ``retry_safety=DO_NOT_RETRY`` rather than a generic rejection.

    Args:
        record: Current transition record.
        expected_state_version: Version the caller last observed.
        amendment_kind: Whether this is a cancel or modify request.

    Returns:
        AmendmentResult: Explicit amendment outcome and retry safety.
    """
    logger.info(
        "Evaluating {} amendment for {} at expected version {}.",
        amendment_kind.value,
        record.entity_id,
        expected_state_version,
    )
    if amendment_kind is AmendmentKind.CANCEL:
        amendable_states = _CANCELLABLE_STATES
    else:
        amendable_states = _MODIFIABLE_STATES

    version_matches = expected_state_version == record.version
    state_amendable = record.state in amendable_states

    if version_matches and state_amendable:
        logger.debug("Amendment accepted for {}.", record.entity_id)
        return AmendmentResult(
            outcome=AmendmentOutcome.ACCEPTED,
            retry_safety=RetrySafety.SAFE_TO_RETRY,
        )

    if record.state is FixExecutionState.PARTIALLY_FILLED:
        outcome = AmendmentOutcome.AMENDED_AFTER_PARTIAL_FILL
    elif amendment_kind is AmendmentKind.CANCEL:
        outcome = AmendmentOutcome.TOO_LATE_TO_CANCEL
    else:
        outcome = AmendmentOutcome.TOO_LATE_TO_MODIFY
    logger.debug(
        "Amendment rejected for {} with outcome {}.",
        record.entity_id,
        outcome.value,
    )
    return AmendmentResult(outcome=outcome, retry_safety=RetrySafety.DO_NOT_RETRY)


def apply_execution_report(
    *,
    record: TransitionRecord,
    report_state: FixExecutionState,
    broker_event_id: str,
    event_source: str,
    timestamp: str,
    request_id: str,
    correlation_id: str,
    dedup_window_size: int,
    filled_volume_delta: Decimal = Decimal(0),
    vwap: Decimal | None = None,
) -> TransitionApplyResult:
    """Apply a broker execution report as an authoritative state transition.

    Execution reports are deduplicated idempotently on ``broker_event_id``:
    a duplicate within the bounded dedup window is dropped without any state
    transition (TRD-FR-131). Otherwise the transition is validated against
    the canonical table (TRD-FR-126) before the record and forensic event are
    built (TRD-FR-127/128).

    Args:
        record: Current transition record.
        report_state: Lifecycle state reported by the broker.
        broker_event_id: Unique broker execution event identifier.
        event_source: Origin of the transition.
        timestamp: UTC timestamp supplied by an injected Clock.
        request_id: Request identifier associated with the transition.
        correlation_id: Correlation identifier.
        dedup_window_size: Maximum number of recent broker event IDs retained
            for duplicate detection.
        filled_volume_delta: Newly filled volume reported by this event.
        vwap: Updated volume-weighted average fill price, if reported.

    Returns:
        TransitionApplyResult: Updated record, forensic event (or ``None``
        when deduplicated), and duplicate flag.

    Raises:
        TradingMappedError: If ``broker_event_id`` is blank or
            ``dedup_window_size``/``filled_volume_delta`` is invalid.
        TradingValidationError: If the reported transition is illegal.
    """
    logger.info(
        "Applying execution report {} for {}.",
        broker_event_id,
        record.entity_id,
    )
    if not broker_event_id.strip():
        raise TradingMappedError(
            "broker_event_id must be non-empty.",
            code="INVALID_INPUT",
        )
    if dedup_window_size < 1:
        raise TradingMappedError(
            "dedup_window_size must be at least 1.",
            code="INVALID_INPUT",
        )
    if filled_volume_delta < 0:
        raise TradingMappedError(
            "filled_volume_delta must not be negative.",
            code="INVALID_INPUT",
        )

    if broker_event_id in record.seen_broker_event_ids:
        logger.info(
            "Duplicate broker_event_id {} dropped for {}.",
            broker_event_id,
            record.entity_id,
        )
        return TransitionApplyResult(record=record, event=None, duplicate=True)

    validate_transition(from_state=record.state, to_state=report_state)

    new_remaining = record.remaining_volume - filled_volume_delta
    if new_remaining < 0:
        new_remaining = Decimal(0)

    updated_seen = (*record.seen_broker_event_ids, broker_event_id)
    if len(updated_seen) > dedup_window_size:
        updated_seen = updated_seen[-dedup_window_size:]

    updated_vwap = record.vwap if vwap is None else vwap
    new_version = record.version + 1
    updated_record = record.model_copy(
        update={
            "state": report_state,
            "version": new_version,
            "filled_volume": record.filled_volume + filled_volume_delta,
            "remaining_volume": new_remaining,
            "vwap": updated_vwap,
            "seen_broker_event_ids": updated_seen,
        }
    )
    event = StateTransitionEvent(
        entity_id=record.entity_id,
        kind=record.kind,
        event_source=event_source,
        timestamp=timestamp,
        broker_event_id=broker_event_id,
        request_id=request_id,
        correlation_id=correlation_id,
        previous_state_version=record.version,
        from_state=record.state,
        to_state=report_state,
    )
    logger.info(
        "Applied transition {}->{} for {} (v{}->v{}).",
        record.state.value,
        report_state.value,
        record.entity_id,
        record.version,
        new_version,
    )
    return TransitionApplyResult(record=updated_record, event=event, duplicate=False)
