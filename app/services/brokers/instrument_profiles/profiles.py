# ruff: noqa: DOC501, N812
"""InstrumentVenueProfile v1 cross-domain contract transport.

The application Phase 0 reconciliation (``feature``) requires an
authoritative ``InstrumentVenueProfile`` covering symbol identity, asset class,
venue, tick size, price precision, quantity step, contract multiplier, session
calendar, order types, time-in-force, margin, shorting, settlement, halt state,
and lifecycle eligibility rules.

Per settled decision D-1 the contract travels as a validated JSON-safe mapping
behind a ``build_instrument_venue_profile``/``parse_instrument_venue_profile``
function pair. The mapping is fail-closed: an undeclared trait is reported as
the explicit ``UNKNOWN`` / ``False`` evidence and never as a plausible default.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from app.kernel.errors import create_validation_error as ValidationError
from app.kernel.redaction import redact_mapping_value as redact_contract_mapping
from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.brokers.canonical_contracts.enums import BrokerId

CONTRACT_VERSION = "v1"
SCHEMA_ID = "brokers.instrument_venue_profile.v1"

_ASSET_CLASSES = frozenset(
    {"FX", "EQUITY", "COMMODITY", "INDEX", "CRYPTO", "METAL", "BOND", "UNKNOWN"}
)
_SETTLEMENTS = frozenset({"T+0", "T+1", "T+2", "T+3", "CASH", "UNKNOWN"})
_HALT_STATES = frozenset({"OPEN", "HALTED", "PRE_OPEN", "UNKNOWN"})
_LIFECYCLES = frozenset(
    {"TRADEABLE", "READ_ONLY", "CLOSE_ONLY", "WATCH_ONLY", "UNKNOWN"}
)
_ORDER_TYPES = frozenset(
    {
        "MARKET",
        "LIMIT",
        "STOP",
        "STOP_LIMIT",
        "TRAILING_STOP",
        "MARKET_ON_OPEN",
        "MARKET_ON_CLOSE",
        "UNKNOWN",
    }
)
_TIME_IN_FORCE = frozenset({"GTC", "IOC", "FOK", "GTD", "DAY", "UNKNOWN"})
_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "broker",
        "provider_symbol",
        "canonical_symbol",
        "asset_class",
        "venue",
        "tick_size",
        "price_precision",
        "quantity_step",
        "contract_multiplier",
        "currency",
        "session_calendar",
        "order_types",
        "time_in_force",
        "margin_eligible",
        "shortable",
        "settlement",
        "halt_state",
        "lifecycle_eligibility",
        "source_timestamp",
        "integrity_hash",
    }
)


def _require_text(value: object, name: str) -> str:
    """Validate a non-empty text field.

    Args:
        value: Candidate value.
        name: Field name for diagnostics.

    Returns:
        Validated non-empty text.

    Raises:
        ValidationError: If the value is not non-empty text.
    """
    del name
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    return value


def _require_decimal(value: object, name: str) -> str:
    """Validate a finite non-negative decimal encoded as text.

    Args:
        value: Candidate value.
        name: Field name for diagnostics.

    Returns:
        Canonical decimal text.

    Raises:
        ValidationError: If the value is not a finite non-negative decimal.
    """
    del name
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID") from error
    if not parsed.is_finite() or parsed < 0:
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    return str(parsed)


def _require_choice(value: object, allowed: frozenset[str], name: str) -> str:
    """Validate an enumeration value.

    Args:
        value: Candidate value.
        allowed: Permitted values.
        name: Field name for diagnostics.

    Returns:
        Validated choice.

    Raises:
        ValidationError: If the value is not permitted.
    """
    text = _require_text(value, name)
    if text not in allowed:
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    return text


def _require_timestamp(value: datetime, name: str) -> None:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        name: Field name for diagnostics.

    Raises:
        ValidationError: If the timestamp is naive or non-UTC.
    """
    del name
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")


def _require_str_tuple(
    value: object, allowed: frozenset[str], name: str
) -> tuple[str, ...]:
    """Validate a non-empty sequence of enumeration members.

    A JSON transport canonicalizes Python tuples to lists, so both tuples and
    lists are accepted; the validated canonical form is always a tuple.

    Args:
        value: Candidate value.
        allowed: Permitted members.
        name: Field name for diagnostics.

    Returns:
        Validated tuple.

    Raises:
        ValidationError: If the value is malformed or contains unknown members.
    """
    del name
    if not isinstance(value, tuple | list) or not value:
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    validated: list[str] = []
    for item in value:
        validated.append(_require_choice(item, allowed, ""))
    return tuple(validated)


def build_instrument_venue_profile(
    *,
    broker: BrokerId | str,
    provider_symbol: str,
    canonical_symbol: str,
    asset_class: str,
    venue: str,
    tick_size: Decimal | float | str,
    price_precision: int,
    quantity_step: Decimal | float | str,
    contract_multiplier: Decimal | float | str,
    currency: str,
    session_calendar: Mapping[str, object],
    order_types: tuple[str, ...],
    time_in_force: tuple[str, ...],
    margin_eligible: bool,
    shortable: bool,
    settlement: str,
    halt_state: str,
    lifecycle_eligibility: str,
    source_timestamp: datetime,
) -> dict[str, object]:
    """Build and hash a redacted InstrumentVenueProfile v1 mapping.

    Args:
        broker: Owning broker identifier.
        provider_symbol: Exact provider-native symbol.
        canonical_symbol: Normalized reference symbol.
        asset_class: Asset classification.
        venue: Venue identifier.
        tick_size: Minimum price increment.
        price_precision: Decimal price precision.
        quantity_step: Minimum quantity increment.
        contract_multiplier: Contract size multiplier.
        currency: Settlement/quote currency.
        session_calendar: Bounded session-calendar mapping.
        order_types: Supported order types.
        time_in_force: Supported time-in-force policies.
        margin_eligible: Margin trading eligibility.
        shortable: Short-selling eligibility.
        settlement: Settlement convention.
        halt_state: Current halt state.
        lifecycle_eligibility: Trading lifecycle eligibility.
        source_timestamp: Aware UTC observation instant.

    Returns:
        InstrumentVenueProfile v1 mapping.

    Raises:
        ValidationError: If any field evidence is invalid.
    """
    broker_value = (
        broker
        if isinstance(broker, BrokerId)
        else BrokerId(_require_text(broker, "broker"))
    )
    if isinstance(price_precision, bool) or not isinstance(price_precision, int):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    if price_precision < 0:
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    _require_timestamp(source_timestamp, "source_timestamp")
    if not isinstance(margin_eligible, bool) or not isinstance(shortable, bool):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    if not isinstance(session_calendar, Mapping):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    profile: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "schema_id": SCHEMA_ID,
        "broker": broker_value.value,
        "provider_symbol": _require_text(provider_symbol, "provider_symbol"),
        "canonical_symbol": _require_text(canonical_symbol, "canonical_symbol"),
        "asset_class": _require_choice(asset_class, _ASSET_CLASSES, "asset_class"),
        "venue": _require_text(venue, "venue"),
        "tick_size": _require_decimal(tick_size, "tick_size"),
        "price_precision": price_precision,
        "quantity_step": _require_decimal(quantity_step, "quantity_step"),
        "contract_multiplier": _require_decimal(
            contract_multiplier, "contract_multiplier"
        ),
        "currency": _require_text(currency, "currency"),
        "session_calendar": dict(redact_contract_mapping(session_calendar)),
        "order_types": _require_str_tuple(order_types, _ORDER_TYPES, "order_types"),
        "time_in_force": _require_str_tuple(
            time_in_force, _TIME_IN_FORCE, "time_in_force"
        ),
        "margin_eligible": margin_eligible,
        "shortable": shortable,
        "settlement": _require_choice(settlement, _SETTLEMENTS, "settlement"),
        "halt_state": _require_choice(halt_state, _HALT_STATES, "halt_state"),
        "lifecycle_eligibility": _require_choice(
            lifecycle_eligibility, _LIFECYCLES, "lifecycle_eligibility"
        ),
        "source_timestamp": source_timestamp.isoformat().replace("+00:00", "Z"),
    }
    profile["integrity_hash"] = canonical_digest(profile)
    return profile


def parse_instrument_venue_profile(value: Mapping[str, object]) -> dict[str, object]:
    """Validate an InstrumentVenueProfile v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached profile.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != CONTRACT_VERSION
        or value.get("schema_id") != SCHEMA_ID
    ):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INTEGRITY_INVALID")
    source_timestamp = value.get("source_timestamp")
    if not isinstance(source_timestamp, str):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    rebuilt = build_instrument_venue_profile(
        broker=cast("str", value["broker"]),
        provider_symbol=cast("str", value["provider_symbol"]),
        canonical_symbol=cast("str", value["canonical_symbol"]),
        asset_class=cast("str", value["asset_class"]),
        venue=cast("str", value["venue"]),
        tick_size=cast("str", value["tick_size"]),
        price_precision=cast("int", value["price_precision"]),
        quantity_step=cast("str", value["quantity_step"]),
        contract_multiplier=cast("str", value["contract_multiplier"]),
        currency=cast("str", value["currency"]),
        session_calendar=cast("Mapping[str, object]", value["session_calendar"]),
        order_types=cast("tuple[str, ...]", value["order_types"]),
        time_in_force=cast("tuple[str, ...]", value["time_in_force"]),
        margin_eligible=cast("bool", value["margin_eligible"]),
        shortable=cast("bool", value["shortable"]),
        settlement=cast("str", value["settlement"]),
        halt_state=cast("str", value["halt_state"]),
        lifecycle_eligibility=cast("str", value["lifecycle_eligibility"]),
        source_timestamp=datetime.fromisoformat(source_timestamp),
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("INSTRUMENT_VENUE_PROFILE_INVALID")
    return dict(safe)


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_ID",
    "build_instrument_venue_profile",
    "parse_instrument_venue_profile",
]
