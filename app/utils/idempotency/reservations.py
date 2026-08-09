"""Explicit-TTL idempotency reservation evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from app.utils.errors.exceptions import ValidationError
from app.utils.idempotency.keys import get_key_owner, parse_idempotency_key


def build_reservation(
    *,
    key: Mapping[str, object],
    reserved_at: datetime,
    ttl_seconds: int,
    state: str = "IN_FLIGHT",
    prior_result: object = None,
) -> dict[str, object]:
    """Build a reservation with explicit positive TTL.

    Args:
        key: Idempotency key.
        reserved_at: Aware UTC reservation instant.
        ttl_seconds: Positive explicit TTL.
        state: Reservation state.
        prior_result: Recorded completed result.

    Returns:
        Reservation mapping.

    Raises:
        ValidationError: If reservation evidence is invalid.
    """
    parsed_key = parse_idempotency_key(key)
    if (
        reserved_at.tzinfo is None
        or reserved_at.utcoffset() != UTC.utcoffset(reserved_at)
        or isinstance(ttl_seconds, bool)
        or ttl_seconds <= 0
        or state not in {"IN_FLIGHT", "COMPLETED"}
    ):
        raise ValidationError("RESERVATION_INVALID")
    if state == "IN_FLIGHT" and prior_result is not None:
        raise ValidationError("RESERVATION_INVALID")
    return {
        "contract_version": "v1",
        "schema_id": "utils.idempotency_reservation.v1",
        "key": parsed_key,
        "reserved_at": reserved_at.isoformat().replace("+00:00", "Z"),
        "ttl_seconds": ttl_seconds,
        "state": state,
        "prior_result": prior_result,
    }


def is_reservation_expired(
    reservation: Mapping[str, object], *, observed_at: datetime
) -> bool:
    """Return expiry against an injected aware UTC instant.

    Args:
        reservation: Prior reservation.
        observed_at: Injected observation instant.

    Returns:
        Whether the reservation expired.

    Raises:
        ValidationError: If evidence is malformed.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() != UTC.utcoffset(
        observed_at
    ):
        raise ValidationError("RESERVATION_INSTANT_INVALID")
    try:
        reserved_at = datetime.fromisoformat(str(reservation["reserved_at"]))
        raw_ttl = reservation["ttl_seconds"]
        if not isinstance(raw_ttl, int) or isinstance(raw_ttl, bool):
            raise ValidationError("RESERVATION_INVALID")
        ttl = raw_ttl
    except (KeyError, TypeError, ValueError) as error:
        raise ValidationError("RESERVATION_INVALID") from error
    return observed_at >= reserved_at + timedelta(seconds=ttl)


def evaluate_reservation(
    *,
    key: Mapping[str, object],
    owner: str,
    prior_reservation: Mapping[str, object] | None,
    observed_at: datetime,
) -> dict[str, object]:
    """Return a fail-closed exactly-once reservation verdict.

    Args:
        key: Presented idempotency key.
        owner: Expected owner scope.
        prior_reservation: Caller-supplied prior state.
        observed_at: Injected observation instant.

    Returns:
        Duplicate verdict and prior-result evidence.

    Raises:
        ValidationError: If owner or state evidence conflicts.
    """
    if get_key_owner(key) != owner:
        raise ValidationError("IDEMPOTENCY_OWNER_MISMATCH")
    if prior_reservation is None:
        return {"verdict": "NEW", "prior_result": None, "may_apply_effect": True}
    prior_key = prior_reservation.get("key")
    if (
        not isinstance(prior_key, Mapping)
        or get_key_owner(prior_key) != owner
        or parse_idempotency_key(prior_key) != parse_idempotency_key(key)
    ):
        raise ValidationError("IDEMPOTENCY_OWNER_MISMATCH")
    if is_reservation_expired(prior_reservation, observed_at=observed_at):
        return {"verdict": "EXPIRED", "prior_result": None, "may_apply_effect": True}
    state = prior_reservation.get("state")
    if state == "IN_FLIGHT":
        return {
            "verdict": "DUPLICATE_IN_FLIGHT",
            "prior_result": None,
            "may_apply_effect": False,
        }
    if state == "COMPLETED":
        return {
            "verdict": "DUPLICATE_COMPLETED",
            "prior_result": prior_reservation.get("prior_result"),
            "may_apply_effect": False,
        }
    raise ValidationError("RESERVATION_INVALID")
