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
class FillRow:
    """One immutable normalized broker fill projection."""

    values: tuple[object, ...]


@dataclass(frozen=True)
class PositionRow:
    """One normalized position projection supplied by authority evidence."""

    values: tuple[object, ...]


@dataclass(frozen=True)
class MaterializationBatch:
    """Table projections attributable to one authoritative event."""

    order: OrderRow | None = None
    outcome: OrderOutcome | None = None
    fill: FillRow | None = None
    position: PositionRow | None = None


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
        "pending_new",
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
        "accepted": "new",
        "rejected": "rejected",
        "partial": "partially_filled",
        "filled": "filled",
        "cancelled": "cancelled",
        "unknown_outcome": "pending_new",
    }
    state = states.get(status)
    if state is None:
        raise ValueError("Trading materialization received an unknown receipt status")
    terminal_at = (
        event.occurred_at.isoformat()
        if state in {"rejected", "filled", "cancelled"}
        else None
    )
    reject_reason = (
        _text(receipt, "response_classification") if state == "rejected" else None
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


def _fill(event: TradingEvent, projection: TradingProjection) -> FillRow:
    """Normalize a fill event by resolving its stored authority receipt.

    Returns:
        Immutable normalized fill row.

    Raises:
        ValueError: If authority fill evidence is incomplete.
    """
    facts = dict(event.payload)
    receipt_id = _text(facts, "receipt_id")
    receipt_facts: dict[str, Any] | None = None
    for candidate in projection.receipts.values():
        if not isinstance(candidate, dict):
            continue
        receipt_candidate = candidate.get("receipt")
        if (
            isinstance(receipt_candidate, dict)
            and receipt_candidate.get("receipt_id") == receipt_id
        ):
            receipt_facts = candidate
            break
    if receipt_facts is None:
        raise ValueError("Trading fill requires its stored authority receipt")
    receipt = _mapping(receipt_facts.get("receipt"), "stored receipt payload")
    attempt_id = _text(receipt_facts, "attempt_event_id")
    attempt = _mapping(projection.orders.get(attempt_id), "originating order attempt")
    intent = _mapping(attempt.get("intent"), "originating intent")
    deal_id = _text(facts, "provider_deal_id")
    deal_ids = receipt.get("provider_deal_ids")
    if not isinstance(deal_ids, list) or deal_id not in deal_ids:
        raise ValueError("Trading fill is absent from its authority receipt")
    price = _optional_text(facts, "average_price")
    if price is None:
        raise ValueError("Trading fill requires an authority-reported price")
    values: tuple[object, ...] = (
        event.event_id,
        _text(intent, "client_order_id"),
        deal_id,
        deal_ids.index(deal_id) + 1,
        _text(facts, "filled_quantity"),
        price,
        "0",
        "0",
        None,
        "unknown",
        _text(receipt, "authority_timestamp"),
        _text(receipt, "received_at"),
        event.correlation_id,
        event.occurred_at.isoformat(),
    )
    return FillRow(values=values)


def _position(event: TradingEvent) -> PositionRow | None:
    """Normalize an explicitly supplied complete position snapshot.

    Returns:
        Normalized row, or ``None`` when no position was reported.
    """
    facts = dict(event.payload)
    value = facts.get("position")
    if value is None:
        return None
    position = _mapping(value, "position")
    position_id = _text(facts, "position_id")
    values: tuple[object, ...] = (
        position_id,
        _text(position, "account_id"),
        _text(position, "symbol_id"),
        _text(position, "direction"),
        _text(position, "quantity_decimal"),
        _text(position, "avg_entry_price_decimal"),
        _optional_text(position, "current_price_decimal"),
        _text(position, "unrealized_pnl_decimal"),
        _text(position, "realized_pnl_decimal"),
        _text(position, "commission_total_decimal"),
        _text(position, "swap_total_decimal"),
        _optional_text(position, "stop_loss_decimal"),
        _optional_text(position, "take_profit_decimal"),
        _optional_text(position, "strategy_version_id"),
        _text(position, "state"),
        _text(position, "opened_at"),
        _optional_text(position, "closed_at"),
        int(position.get("position_version", 0)),
        _text(position, "created_at"),
        _text(position, "updated_at"),
    )
    return PositionRow(values=values)


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
        return MaterializationBatch(order=_order_row(event, intent))
    if event.event_type == "receipt_recorded":
        return MaterializationBatch(outcome=_outcome(event, projection))
    if event.event_type == "fill_recorded":
        return MaterializationBatch(
            fill=_fill(event, projection),
            position=_position(event),
        )
    return MaterializationBatch()


__all__: list[str] = []
