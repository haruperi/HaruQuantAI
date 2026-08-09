"""Normalize canonical Trading events into rebuildable table projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.utils import canonical_json, get_logger

if TYPE_CHECKING:
    from app.services.trading.state.events import TradingEvent
    from app.services.trading.state.projections import TradingProjection

logger = get_logger(__name__)


@dataclass(frozen=True)
class OrderRow:
    """One normalized order projection created from a submit intent."""

    values: tuple[object, ...]


@dataclass(frozen=True)
class OrderOutcome:
    """One normalized authority outcome applied to an existing order."""

    order_id: str
    lookup_by_broker_id: bool
    broker_order_id: str | None
    state: str
    filled_quantity: str
    average_price: str | None
    reject_reason: str | None
    terminal_at: str | None
    updated_at: str
    reason_code: str
    detail_json: str
    correlation_id: str


@dataclass(frozen=True)
class TransitionRow:
    """One append-only order transition supported by an authority event."""

    values: tuple[object, ...]


@dataclass(frozen=True)
class FillRow:
    """One append-only fill supported by broker receipt evidence."""

    values: tuple[object, ...]


@dataclass(frozen=True)
class MaterializationBatch:
    """Table projections attributable to one authoritative event."""

    order: OrderRow | None = None
    outcome: OrderOutcome | None = None
    transition: TransitionRow | None = None
    fill: FillRow | None = None


def _mapping(value: object, field: str) -> dict[str, Any]:
    """Return a required mapping without fabricating missing evidence.

    Args:
        value: Candidate event fact.
        field: Stable field name used in failure details.

    Returns:
        Plain mapping.

    Raises:
        TypeError: If the event does not carry the required mapping.
    """
    if not isinstance(value, dict):
        message = f"Trading materialization requires {field}"
        raise TypeError(message)
    return value


def _text(mapping: dict[str, Any], field: str) -> str:
    """Return one required non-empty textual fact.

    Raises:
        ValueError: If the fact is absent or not textual.
    """
    value = mapping.get(field)
    if not isinstance(value, str) or not value:
        message = f"Trading materialization requires {field}"
        raise ValueError(message)
    return value


def _optional_text(mapping: dict[str, Any], field: str) -> str | None:
    """Return one optional textual fact without coercion.

    Raises:
        ValueError: If a supplied fact is not textual.
    """
    value = mapping.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        message = f"Trading materialization {field} must be text"
        raise ValueError(message)
    return value


def _order_row(event: TradingEvent, intent: dict[str, Any]) -> OrderRow | None:
    """Normalize a new-order intent; other actions do not create orders.

    Returns:
        Normalized order row, or ``None`` for a non-submit action.
    """
    if intent.get("action") != "submit_order":
        return None
    client_order_id = _text(intent, "client_order_id")
    route = str(intent.get("route", event.route.value))
    runtime_profile = "simulation" if route == "sim" else route
    order_type = _text(intent, "order_type").lower()
    limit_price = _optional_text(intent, "price")
    stop_price = _optional_text(intent, "stop_price")
    # The stable Trading-owned client identifier is also the aggregate order key.
    values: tuple[object, ...] = (
        client_order_id,
        client_order_id,
        None,
        _text(intent, "account_id"),
        _text(intent, "symbol"),
        None,
        None,
        _optional_text(intent, "source_intent_id"),
        _text(intent, "risk_decision_id"),
        _text(intent, "side").lower(),
        order_type,
        (
            None
            if intent.get("time_in_force") is None
            else _text(intent, "time_in_force").lower()
        ),
        _text(intent, "approved_volume"),
        "0",
        limit_price,
        stop_price,
        None,
        _optional_text(intent, "stop_loss"),
        _optional_text(intent, "take_profit"),
        "STAGED",
        None,
        runtime_profile,
        event.occurred_at.isoformat(),
        None,
        event.correlation_id,
        event.occurred_at.isoformat(),
        event.occurred_at.isoformat(),
    )
    return OrderRow(values=values)


def _receipt_facts(
    event: TradingEvent,
    projection: TradingProjection,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return one receipt and its originating intent from projected evidence."""
    facts = _mapping(dict(event.payload), "receipt facts")
    receipt = _mapping(facts.get("receipt"), "receipt")
    attempt_id = _text(facts, "attempt_event_id")
    attempt = _mapping(projection.orders.get(attempt_id), "originating order attempt")
    intent = _mapping(attempt.get("intent"), "originating intent")
    return receipt, intent


def _outcome(event: TradingEvent, projection: TradingProjection) -> OrderOutcome:
    """Normalize an authority receipt into one order state transition.

    Returns:
        Normalized order outcome.

    Raises:
        ValueError: If the receipt status or identity is incomplete.
    """
    receipt, intent = _receipt_facts(event, projection)
    status = _text(receipt, "status")
    states = {
        "accepted": "ACKNOWLEDGED",
        "rejected": "REJECTED",
        "partial": "PARTIALLY_FILLED",
        "filled": "FILLED",
        "cancelled": "CANCELLED",
        "unknown_outcome": "UNKNOWN",
    }
    state = states.get(status)
    if state is None:
        raise ValueError("Trading materialization received an unknown receipt status")
    terminal_at = (
        event.occurred_at.isoformat()
        if state in {"REJECTED", "FILLED", "CANCELLED"}
        else None
    )
    reject_reason = (
        _text(receipt, "response_classification") if state == "REJECTED" else None
    )
    submit_order = intent.get("action") == "submit_order"
    order_id = (
        _text(intent, "client_order_id")
        if submit_order
        else _text(intent, "target_broker_order_id")
    )
    return OrderOutcome(
        order_id=order_id,
        lookup_by_broker_id=not submit_order,
        broker_order_id=_optional_text(receipt, "provider_order_id"),
        state=state,
        filled_quantity=_text(receipt, "filled_quantity"),
        average_price=_optional_text(receipt, "average_price"),
        reject_reason=reject_reason,
        terminal_at=terminal_at,
        updated_at=event.occurred_at.isoformat(),
        reason_code=f"receipt_{status}",
        detail_json=canonical_json(
            {
                "receipt_id": _text(receipt, "receipt_id"),
                "response_classification": _text(receipt, "response_classification"),
            }
        ),
        correlation_id=event.correlation_id,
    )


def _transition(
    event: TradingEvent,
    *,
    order_id: str,
    from_state: str | None,
    to_state: str,
    reason_code: str,
) -> TransitionRow:
    """Build one source-sequenced transition row from an authority event.

    Returns:
        Append-only transition materialization.
    """
    occurred_at = event.occurred_at.isoformat()
    return TransitionRow(
        values=(
            f"{event.event_id}:transition",
            order_id,
            from_state,
            to_state,
            event.aggregate_version + 1,
            reason_code,
            occurred_at,
            event.correlation_id,
            event.causation_id,
            occurred_at,
        )
    )


def _fill(event: TradingEvent, projection: TradingProjection) -> FillRow:
    """Normalize one fill without inventing missing receipt or order evidence.

    Returns:
        Append-only fill materialization.

    Raises:
        ValueError: If receipt, order, quantity, or price evidence is absent.
    """
    facts = _mapping(dict(event.payload), "fill facts")
    receipt_id = _text(facts, "receipt_id")
    receipt_facts: dict[str, Any] | None = None
    for value in projection.receipts.values():
        if not isinstance(value, dict):
            continue
        receipt = value.get("receipt")
        if isinstance(receipt, dict) and receipt.get("receipt_id") == receipt_id:
            receipt_facts = _mapping(value, "receipt event")
            break
    if receipt_facts is None:
        raise ValueError("Trading fill has no authoritative receipt")
    attempt_id = _text(receipt_facts, "attempt_event_id")
    attempt = _mapping(projection.orders.get(attempt_id), "originating order attempt")
    intent = _mapping(attempt.get("intent"), "originating intent")
    price = _optional_text(facts, "average_price")
    if price is None:
        raise ValueError("Trading fill requires an executed price")
    occurred_at = event.occurred_at.isoformat()
    return FillRow(
        values=(
            event.event_id,
            _text(intent, "client_order_id"),
            _text(facts, "provider_deal_id"),
            event.aggregate_version + 1,
            _text(facts, "filled_quantity"),
            price,
            None,
            occurred_at,
            event.correlation_id,
            occurred_at,
        )
    )


def build_materialization_batch(
    event: TradingEvent,
    projection: TradingProjection,
) -> MaterializationBatch:
    """Build only table rows supported by canonical event evidence.

    Args:
        event: Authoritative event being appended.
        projection: Deterministic projection after applying the event.

    Returns:
        Normalized rebuildable materialization records.

    Raises:
        ValueError: If an applicable event lacks required evidence.
    """
    logger.debug("Building Trading materialization for %s", event.event_type)
    if event.event_type == "send_attempted":
        intent = _mapping(dict(event.payload).get("intent"), "order intent")
        order = _order_row(event, intent)
        transition = None
        if order is not None:
            transition = _transition(
                event,
                order_id=_text(intent, "client_order_id"),
                from_state=None,
                to_state="STAGED",
                reason_code="intent_persisted",
            )
        return MaterializationBatch(order=order, transition=transition)
    if event.event_type == "receipt_recorded":
        outcome = _outcome(event, projection)
        return MaterializationBatch(
            outcome=outcome,
            transition=_transition(
                event,
                order_id=outcome.order_id,
                from_state="STAGED",
                to_state=outcome.state,
                reason_code=outcome.reason_code,
            ),
        )
    if event.event_type == "fill_recorded":
        return MaterializationBatch(fill=_fill(event, projection))
    return MaterializationBatch()


__all__: list[str] = []
