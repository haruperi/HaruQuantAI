# ruff: noqa: DOC501, N812
"""BrokerReconciliationSnapshot v1 cross-domain contract transport.

The application Phase 0 reconciliation (``feature``) extends the
existing ``execution_history`` read paths into one consolidated port returning
open orders, fills, positions, balances, and venue status for Trading and
Simulator recovery. The contract is fail-closed: when any component read is
absent or unknown, the corresponding section reports an explicit ``UNKNOWN``
verdict and never a fabricated record.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import cast

from app.services.brokers.canonical_contracts.enums import BrokerEnvironment, BrokerId
from app.utils import canonical_digest, to_json_safe
from app.utils import create_validation_error as ValidationError

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.reconciliation.v1"

_VENUE_STATES = frozenset({"OPEN", "HALTED", "PRE_OPEN", "CLOSED", "UNKNOWN"})
_SECTION_STATES = frozenset({"COMPLETE", "PARTIAL", "UNAVAILABLE", "UNKNOWN"})
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "broker",
        "environment",
        "account_reference",
        "as_of",
        "venue_state",
        "open_orders_state",
        "open_orders",
        "fills_state",
        "fills",
        "positions_state",
        "positions",
        "balances_state",
        "balances",
        "integrity_hash",
    }
)


def _require_text(value: object) -> str:
    """Validate non-empty text.

    Args:
        value: Candidate value.

    Returns:
        Validated text.

    Raises:
        ValidationError: If the value is not non-empty text.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    return value


def _require_choice(value: object, allowed: frozenset[str]) -> str:
    """Validate an enumeration member.

    Args:
        value: Candidate value.
        allowed: Permitted members.

    Returns:
        Validated member.

    Raises:
        ValidationError: If the value is not permitted.
    """
    text = _require_text(value)
    if text not in allowed:
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    return text


def _require_records(value: object) -> tuple[Mapping[str, object], ...]:
    """Validate a sequence of JSON-safe record mappings.

    A JSON transport canonicalizes Python tuples to lists, so both tuples and
    lists are accepted; the validated canonical form is always a tuple.

    Args:
        value: Candidate value.

    Returns:
        Validated record tuple.

    Raises:
        ValidationError: If the value is not a sequence of mappings.
    """
    if not isinstance(value, tuple | list):
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    records: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValidationError("BROKER_RECONCILIATION_INVALID")
        records.append(dict(item))
    return tuple(records)


def _require_timestamp(value: datetime) -> str:
    """Validate an aware UTC timestamp and return canonical text.

    Args:
        value: Candidate timestamp.

    Returns:
        Canonical ISO-8601 UTC text.

    Raises:
        ValidationError: If the timestamp is naive or non-UTC.
    """
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    return value.isoformat().replace("+00:00", "Z")


def build_broker_reconciliation_snapshot(
    *,
    broker: BrokerId | str,
    environment: BrokerEnvironment | str,
    account_reference: str | None,
    as_of: datetime,
    venue_state: str,
    open_orders_state: str,
    open_orders: Sequence[Mapping[str, object]],
    fills_state: str,
    fills: Sequence[Mapping[str, object]],
    positions_state: str,
    positions: Sequence[Mapping[str, object]],
    balances_state: str,
    balances: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build and hash a redacted BrokerReconciliationSnapshot v1 mapping.

    Args:
        broker: Owning broker identifier.
        environment: Configured broker environment.
        account_reference: Optional broker account reference.
        as_of: Aware UTC reconciliation instant.
        venue_state: Normalized venue state.
        open_orders_state: Open-orders section state.
        open_orders: Open-order records.
        fills_state: Fills section state.
        fills: Fill records.
        positions_state: Positions section state.
        positions: Position records.
        balances_state: Balances section state.
        balances: Balance records.

    Returns:
        BrokerReconciliationSnapshot v1 mapping.

    Raises:
        ValidationError: If any field evidence is invalid.
    """
    broker_value = (
        broker if isinstance(broker, BrokerId) else BrokerId(_require_text(broker))
    )
    env_value = (
        environment
        if isinstance(environment, BrokerEnvironment)
        else BrokerEnvironment(_require_text(environment))
    )
    if account_reference is not None:
        _require_text(account_reference)
    snapshot: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "broker": broker_value.value,
        "environment": env_value.value,
        "account_reference": account_reference,
        "as_of": _require_timestamp(as_of),
        "venue_state": _require_choice(venue_state, _VENUE_STATES),
        "open_orders_state": _require_choice(open_orders_state, _SECTION_STATES),
        "open_orders": _require_records(tuple(open_orders)),
        "fills_state": _require_choice(fills_state, _SECTION_STATES),
        "fills": _require_records(tuple(fills)),
        "positions_state": _require_choice(positions_state, _SECTION_STATES),
        "positions": _require_records(tuple(positions)),
        "balances_state": _require_choice(balances_state, _SECTION_STATES),
        "balances": _require_records(tuple(balances)),
    }
    snapshot["integrity_hash"] = canonical_digest(snapshot)
    return snapshot


def parse_broker_reconciliation_snapshot(
    value: Mapping[str, object],
) -> dict[str, object]:
    """Validate a BrokerReconciliationSnapshot v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached reconciliation snapshot.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("BROKER_RECONCILIATION_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("BROKER_RECONCILIATION_INTEGRITY_INVALID")
    as_of_text = value.get("as_of")
    account_reference = value.get("account_reference")
    if not isinstance(as_of_text, str):
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    if account_reference is not None and not isinstance(account_reference, str):
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    rebuilt = build_broker_reconciliation_snapshot(
        broker=cast("str", value["broker"]),
        environment=cast("str", value["environment"]),
        account_reference=account_reference,
        as_of=datetime.fromisoformat(as_of_text),
        venue_state=cast("str", value["venue_state"]),
        open_orders_state=cast("str", value["open_orders_state"]),
        open_orders=cast("Sequence[Mapping[str, object]]", value["open_orders"]),
        fills_state=cast("str", value["fills_state"]),
        fills=cast("Sequence[Mapping[str, object]]", value["fills"]),
        positions_state=cast("str", value["positions_state"]),
        positions=cast("Sequence[Mapping[str, object]]", value["positions"]),
        balances_state=cast("str", value["balances_state"]),
        balances=cast("Sequence[Mapping[str, object]]", value["balances"]),
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("BROKER_RECONCILIATION_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_broker_reconciliation_snapshot",
    "parse_broker_reconciliation_snapshot",
]
