"""Focused unit evidence for FEAT-BRK-00 Instrument and Venue Profiles."""

from datetime import UTC, datetime

import pytest
from app.kernel.errors import ValidationError
from app.services.brokers import (
    build_instrument_venue_profile,
    parse_instrument_venue_profile,
    persistence,
)
from app.services.brokers.canonical_contracts.enums import BrokerId
from app.services.brokers.instrument_profiles import symbols

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)
_NAIVE = datetime(2026, 8, 7)  # noqa: DTZ001 - intentional invalid evidence.
_RESULT = {"status": "success"}


def _profile_kwargs() -> dict[str, object]:
    """Return complete valid profile evidence."""
    return {
        "broker": BrokerId.MT5,
        "provider_symbol": "EURUSD",
        "canonical_symbol": "EUR/USD",
        "asset_class": "FX",
        "venue": "mt5-demo",
        "tick_size": "0.00001",
        "price_precision": 5,
        "quantity_step": "0.01",
        "contract_multiplier": "100000",
        "currency": "USD",
        "session_calendar": {"mon_open": "00:00"},
        "order_types": ("MARKET", "LIMIT"),
        "time_in_force": ("GTC", "DAY"),
        "margin_eligible": True,
        "shortable": False,
        "settlement": "T+2",
        "halt_state": "OPEN",
        "lifecycle_eligibility": "TRADEABLE",
        "source_timestamp": _NOW,
    }


def test_profile_round_trip_preserves_authoritative_evidence() -> None:
    """Build and parse preserve all authoritative profile evidence."""
    profile = build_instrument_venue_profile(**_profile_kwargs())
    parsed = parse_instrument_venue_profile(profile)
    assert parsed["schema_id"] == "brokers.instrument_venue_profile.v1"
    assert parsed["broker"] == "mt5"
    assert list(parsed["order_types"]) == ["MARKET", "LIMIT"]
    assert parsed["integrity_hash"] == profile["integrity_hash"]


def test_profile_tamper_detection_fails_closed() -> None:
    """A modified profile field invalidates its integrity evidence."""
    profile = build_instrument_venue_profile(**_profile_kwargs())
    tampered = dict(profile)
    tampered["tick_size"] = "0.001"
    with pytest.raises(ValidationError):
        parse_instrument_venue_profile(tampered)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider_symbol", ""),
        ("asset_class", "DERIVATIVE"),
        ("tick_size", "not-a-number"),
        ("quantity_step", "NaN"),
        ("price_precision", -1),
        ("margin_eligible", "yes"),
        ("order_types", ("MARKET", 1)),
        ("source_timestamp", _NAIVE),
    ],
)
def test_profile_rejects_malformed_or_undeclared_evidence(
    field: str, value: object
) -> None:
    """Malformed or undeclared profile evidence fails closed."""
    kwargs = _profile_kwargs()
    kwargs[field] = value
    with pytest.raises(ValidationError):
        build_instrument_venue_profile(**kwargs)


def test_symbol_identity_reads_reach_private_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Current, reverse, and historical reads reach their CRUD executors."""
    calls: list[tuple[str, tuple[object, ...], str]] = []

    def capture(name: str):
        def operation(*args: object, request_id: str) -> object:
            calls.append((name, args, request_id))
            return _RESULT

        return operation

    monkeypatch.setattr(persistence, "read_provider_symbol", capture("forward"))
    monkeypatch.setattr(persistence, "read_canonical_symbol", capture("reverse"))
    monkeypatch.setattr(
        persistence, "read_provider_symbol_as_of", capture("historical")
    )

    assert (
        symbols.resolve_broker_provider_symbol("mt5", "EURUSD", request_id="req-1")
        is _RESULT
    )
    assert (
        symbols.resolve_broker_canonical_symbol("mt5", "EURUSD.r", request_id="req-2")
        is _RESULT
    )
    assert (
        symbols.resolve_broker_provider_symbol_as_of(
            "mt5", "EURUSD", "2024-01-01", request_id="req-3"
        )
        is _RESULT
    )
    assert [call[0] for call in calls] == ["forward", "reverse", "historical"]


def test_symbol_identity_reads_reject_empty_identifiers() -> None:
    """Empty symbol identity evidence fails before persistence."""
    with pytest.raises(ValueError, match="provider_code"):
        symbols.resolve_broker_provider_symbol(" ", "EURUSD", request_id="req-1")
