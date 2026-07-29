"""Unit tests for symbol-to-economic-event profiles (FR-DATA-125)."""

from __future__ import annotations

from types import MappingProxyType

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.economic_calendar.profiling import (
    SYMBOL_EVENT_PROFILES,
    SymbolEventProfile,
    get_symbol_event_profile,
)


def test_symbol_event_profile_is_frozen_and_set_typed() -> None:
    """Profiles carry immutable frozenset currencies/countries."""
    profile = SymbolEventProfile(
        symbol="EURUSD",
        currencies=frozenset({"EUR", "USD"}),
        countries=frozenset({"EU", "US"}),
    )
    assert isinstance(profile.currencies, frozenset)
    assert isinstance(profile.countries, frozenset)
    assert "USD" in profile.currencies
    assert "US" in profile.countries


@pytest.mark.parametrize(
    ("symbol", "currencies", "countries"),
    [
        ("EURUSD", {"EUR", "USD"}, {"EU", "US"}),
        ("GBPJPY", {"GBP", "JPY"}, {"GB", "JP"}),
        ("XAUUSD", {"USD"}, {"US"}),
        ("NAS100", {"USD"}, {"US"}),
        ("GER40", {"EUR"}, {"DE", "EU"}),
    ],
)
def test_canonical_profiles_are_registered(
    symbol: str, currencies: set[str], countries: set[str]
) -> None:
    """The canonical five symbols exist with the documented memberships."""
    profile = SYMBOL_EVENT_PROFILES[symbol]
    assert profile.symbol == symbol
    assert set(profile.currencies) == currencies
    assert set(profile.countries) == countries




def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_get_symbol_event_profile_returns_registered_instance() -> None:
    """Lookup returns the same object referenced by the registry."""
    profile = _unwrap(get_symbol_event_profile("EURUSD"))
    assert profile == SYMBOL_EVENT_PROFILES["EURUSD"]


def test_get_symbol_event_profile_rejects_unknown_symbol() -> None:
    """Unregistered symbols raise fail-closed VALIDATION_FAILED."""
    with pytest.raises(DataError) as error:
        _unwrap(get_symbol_event_profile("NOTREAL"))
    assert error.value.code == "VALIDATION_FAILED"


def test_profile_registry_is_immutable() -> None:
    """The canonical symbol registry cannot be mutated at runtime."""
    assert isinstance(SYMBOL_EVENT_PROFILES, MappingProxyType)
    with pytest.raises(TypeError):
        SYMBOL_EVENT_PROFILES["NEW"] = SYMBOL_EVENT_PROFILES["EURUSD"]  # type: ignore[index]
