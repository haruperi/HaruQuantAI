"""Deterministic provider-shaped Simulation lifecycle evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from app.utils import canonical_digest

type FillPolicy = Literal["FOK", "IOC", "RETURN", "BOC"]
type TimePolicy = Literal["GTC", "DAY", "SPECIFIED", "SPECIFIED_DAY"]


def deterministic_lifecycle_ticket(kind: str, material: Mapping[str, object]) -> str:
    """Return a stable ticket derived only from canonical lifecycle evidence.

    Args:
        kind: Bounded ticket namespace.
        material: Complete causal identity material.

    Returns:
        Stable lowercase digest-backed ticket.

    Raises:
        ValueError: If the namespace or material is empty.
    """
    if not kind or kind != kind.strip() or not material:
        raise ValueError("lifecycle ticket material is incomplete")
    return f"sim-{kind}-{canonical_digest(dict(material))}"


def resolve_order_expiration(
    *,
    policy: TimePolicy,
    submitted_at: datetime,
    specified_at: datetime | None,
    session_closes: Sequence[datetime],
) -> datetime | None:
    """Resolve exact provider-policy expiration from evidenced session closes.

    Args:
        policy: Provider time policy.
        submitted_at: Order admission instant.
        specified_at: Explicit expiry for specified policies.
        session_closes: Ordered provider-session closing instants.

    Returns:
        Expiration instant, or ``None`` for GTC.

    Raises:
        ValueError: If UTC, chronology, or session evidence is incomplete.
    """
    instants = (submitted_at, specified_at, *session_closes)
    if any(
        value is not None
        and (value.tzinfo is None or value.utcoffset() != timedelta(0))
        for value in instants
    ):
        raise ValueError("expiration evidence must use aware UTC instants")
    closes = tuple(sorted(set(session_closes)))
    if policy == "GTC":
        if specified_at is not None:
            raise ValueError("GTC cannot carry an explicit expiration")
        return None
    if policy == "SPECIFIED":
        if specified_at is None or specified_at <= submitted_at:
            raise ValueError("SPECIFIED requires a future expiration")
        return specified_at
    target_date = (
        submitted_at.date()
        if policy == "DAY"
        else specified_at.date()
        if specified_at is not None
        else None
    )
    if policy not in {"DAY", "SPECIFIED_DAY"} or target_date is None:
        raise ValueError("expiration policy is unsupported or incomplete")
    candidates = tuple(
        close
        for close in closes
        if close.date() == target_date and close > submitted_at
    )
    if not candidates:
        raise ValueError("session-close expiration evidence is uncovered")
    return candidates[-1]


def resolve_fill_remainder(
    *,
    policy: FillPolicy,
    requested: Decimal,
    available: Decimal,
    remainder_evidenced: bool,
) -> Mapping[str, object]:
    """Resolve fill, cancellation, and residual quantities for one policy.

    Args:
        policy: Exact provider fill policy.
        requested: Remaining requested volume.
        available: Immediately executable evidenced volume.
        remainder_evidenced: Whether a RETURN residual may remain pending.

    Returns:
        Detached status and quantity mapping.

    Raises:
        ValueError: If quantities or residual evidence are invalid.
    """
    if any(not value.is_finite() or value < 0 for value in (requested, available)):
        raise ValueError("fill quantities must be finite and non-negative")
    if requested <= 0:
        raise ValueError("requested fill quantity must be positive")
    executable = min(requested, available)
    if policy == "BOC":
        return {
            "status": "cancelled" if executable > 0 else "pending",
            "filled": Decimal(0),
            "cancelled": requested if executable > 0 else Decimal(0),
            "remaining": requested if executable == 0 else Decimal(0),
        }
    if policy == "FOK" and executable < requested:
        executable = Decimal(0)
    remaining = requested - executable
    if policy == "RETURN" and remaining > 0:
        if not remainder_evidenced:
            raise ValueError("RETURN residual requires provider evidence")
        cancelled = Decimal(0)
        status = "partial" if executable > 0 else "pending"
    else:
        cancelled = remaining
        status = (
            "filled"
            if executable == requested
            else "partial"
            if executable > 0
            else "cancelled"
        )
        remaining = Decimal(0)
    return {
        "status": status,
        "filled": executable,
        "cancelled": cancelled,
        "remaining": remaining,
    }


def build_lifecycle_deal(
    *,
    order_id: str,
    account_id: str,
    position_id: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    entry: str,
    reason: str,
    occurred_at: datetime,
    economic_at: datetime,
    available_at: datetime,
    source_sequence: int,
    fee_evidence: Mapping[str, object],
    authority_snapshot: Mapping[str, object],
    ledger_reference: str,
) -> Mapping[str, object]:
    """Build one referentially complete deterministic deal projection.

    Args:
        order_id: Causal order ticket.
        account_id: Exact simulated account identity.
        position_id: Affected position ticket.
        side: BUY or SELL authority side.
        quantity: Positive executed volume.
        price: Positive execution price.
        entry: Provider-shaped DEAL_ENTRY value.
        reason: Exact authority reason code.
        occurred_at: Authority timestamp.
        economic_at: Economic effect timestamp.
        available_at: Earliest timestamp when the event is observable.
        source_sequence: Durable authority sequence.
        fee_evidence: Itemized immutable fee evidence.
        authority_snapshot: Complete post-event position and account authority.
        ledger_reference: Stable reference to the post-event ledger state.

    Returns:
        Detached provider-shaped deal mapping.

    Raises:
        TypeError: If authority snapshot containers have invalid types.
        ValueError: If identity, quantities, vocabulary, or time is invalid.
    """
    if (
        side not in {"BUY", "SELL"}
        or entry not in {"DEAL_ENTRY_IN", "DEAL_ENTRY_OUT", "DEAL_ENTRY_INOUT"}
        or any(
            not value or value != value.strip()
            for value in (order_id, account_id, position_id, reason, ledger_reference)
        )
        or not quantity.is_finite()
        or quantity <= 0
        or not price.is_finite()
        or price <= 0
        or occurred_at.tzinfo is None
        or occurred_at.utcoffset() != timedelta(0)
        or economic_at.tzinfo is None
        or economic_at.utcoffset() != timedelta(0)
        or available_at.tzinfo is None
        or available_at.utcoffset() != timedelta(0)
        or economic_at > occurred_at
        or occurred_at > available_at
        or source_sequence < 0
    ):
        raise ValueError("deal lifecycle evidence is invalid")
    if set(authority_snapshot) != {"position", "account"}:
        raise ValueError("deal authority snapshot is incomplete")
    position = authority_snapshot["position"]
    account = authority_snapshot["account"]
    if not isinstance(position, Mapping) or not isinstance(account, Mapping):
        raise TypeError("deal authority snapshot is invalid")
    required_position = {
        "position_id",
        "symbol",
        "side",
        "state",
        "quantity",
        "source_sequence",
    }
    if (
        set(position) != required_position
        or position.get("position_id") != position_id
        or position.get("source_sequence") != source_sequence
        or position.get("state") not in {"OPEN", "FLAT"}
        or position.get("side") not in {"LONG", "SHORT", "UNKNOWN"}
        or not isinstance(position.get("quantity"), Decimal)
        or not account
    ):
        raise ValueError("deal authority snapshot is invalid")
    material = {
        "order_id": order_id,
        "position_id": position_id,
        "entry": entry,
        "source_sequence": source_sequence,
        "occurred_at": occurred_at,
    }
    deal_id = deterministic_lifecycle_ticket("deal", material)
    trading_reason = (
        "REVERSAL"
        if entry == "DEAL_ENTRY_INOUT"
        else "PROTECTION"
        if reason in {"STOP_LOSS", "TAKE_PROFIT"}
        else "LIQUIDATION"
        if reason in {"STOP_OUT", "LIQUIDATION"}
        else "ORDER"
    )
    authority_event = {
        "event_id": deal_id,
        "route": "sim",
        "account_id": account_id,
        "authority_id": "simulator",
        "deal_id": deal_id,
        "position_id": position_id,
        "symbol": position["symbol"],
        "side": position["side"],
        "state": position["state"],
        "quantity": position["quantity"],
        "source_sequence": source_sequence,
        "available_at": available_at,
        "activity_origin": "owned",
        "reason": trading_reason,
    }
    return {
        "deal_id": deal_id,
        **material,
        "side": side,
        "quantity": quantity,
        "price": price,
        "reason": reason,
        "economic_at": economic_at,
        "available_at": available_at,
        "fee_evidence": dict(fee_evidence),
        "authority_snapshot": {
            "position": dict(position),
            "account": dict(account),
        },
        "ledger_reference": ledger_reference,
        "trading_authority_event": authority_event,
        "event_category": "authority_deal",
    }


def build_protection_projection(
    *,
    position_id: str,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
    triggered_reason: str | None,
) -> Mapping[str, object]:
    """Return internal protection/OCO evidence without an ordinary order.

    Args:
        position_id: Protected position identity.
        stop_loss: Optional stop-loss trigger.
        take_profit: Optional take-profit trigger.
        triggered_reason: Winning protection reason, when triggered.

    Returns:
        Detached protection projection with OCO cancellation evidence.

    Raises:
        ValueError: If identity or trigger evidence is invalid.
    """
    if not position_id or triggered_reason not in {None, "STOP_LOSS", "TAKE_PROFIT"}:
        raise ValueError("protection lifecycle evidence is invalid")
    sibling = (
        None
        if triggered_reason is None
        else {
            "STOP_LOSS": "TAKE_PROFIT",
            "TAKE_PROFIT": "STOP_LOSS",
        }[triggered_reason]
    )
    return {
        "position_id": position_id,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "triggered_reason": triggered_reason,
        "oco_cancelled_reason": sibling,
        "exposed_as_pending_order": False,
    }


def describe_lifecycle_race(
    *,
    left_event_id: str,
    right_event_id: str,
    left_at: datetime,
    right_at: datetime,
    evidenced_predecessor: str | None,
) -> Mapping[str, object]:
    """Represent an evidenced causal edge or explicit concurrent relation.

    Args:
        left_event_id: First compared event identity.
        right_event_id: Second compared event identity.
        left_at: Left authority timestamp.
        right_at: Right authority timestamp.
        evidenced_predecessor: Event proven to precede the other, if any.

    Returns:
        Detached partial-order relation without invented provider sequence.

    Raises:
        ValueError: If identities, UTC timestamps, or causal evidence conflict.
    """
    if (
        not left_event_id
        or not right_event_id
        or left_event_id == right_event_id
        or any(
            value.tzinfo is None or value.utcoffset() != timedelta(0)
            for value in (left_at, right_at)
        )
        or evidenced_predecessor not in {None, left_event_id, right_event_id}
    ):
        raise ValueError("race evidence is invalid")
    if evidenced_predecessor is not None:
        relation = (
            "LEFT_BEFORE_RIGHT"
            if evidenced_predecessor == left_event_id
            else "RIGHT_BEFORE_LEFT"
        )
    elif left_at < right_at:
        relation = "LEFT_BEFORE_RIGHT"
    elif right_at < left_at:
        relation = "RIGHT_BEFORE_LEFT"
    else:
        relation = "CONCURRENT"
    return {
        "left_event_id": left_event_id,
        "right_event_id": right_event_id,
        "relation": relation,
        "provider_sequence_claimed": evidenced_predecessor is not None,
    }


__all__ = [
    "build_lifecycle_deal",
    "build_protection_projection",
    "describe_lifecycle_race",
    "deterministic_lifecycle_ticket",
    "resolve_fill_remainder",
    "resolve_order_expiration",
]
