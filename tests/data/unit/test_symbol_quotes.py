"""Unit tests for bounded exact-symbol market quotes."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.kernel.identity import generate_id
from app.services.data.market_data import directory_projection as projection
from app.services.data.market_data import symbol_discovery
from app.services.data.market_data import symbol_quotes as quotes
from app.services.data.market_data.directory_contracts import SymbolsQuoteRequest
from app.services.data.market_data.level1 import Level1Snapshot
from app.services.data.market_data.snapshot import MarketSnapshot

_T0 = datetime(2026, 8, 10, 12, tzinfo=UTC)


def _success(data: object) -> object:
    """Wrap data in a structural success response.

    Args:
        data: Response payload.

    Returns:
        Structural success response.
    """
    return SimpleNamespace(status="success", data=data, error=None)


def _failure() -> object:
    """Return one structural failed response.

    Returns:
        Structural failed response.
    """
    return SimpleNamespace(
        status="error",
        data=None,
        error=SimpleNamespace(code="SYMBOL_NOT_FOUND"),
    )


def _metadata(symbol: str) -> object:
    """Build normalized metadata for one symbol.

    Args:
        symbol: Provider-native symbol.

    Returns:
        Structural metadata value.
    """
    path = "Indices\\US500" if symbol == "US500" else "Forex\\Majors"
    return SimpleNamespace(
        canonical_symbol=symbol,
        provider_symbol=symbol,
        asset_class="mt5",
        source_id="mt5",
        path=path,
        name=symbol,
        digits=5,
        bid=1.0999,
        ask=1.1001,
        last=1.1,
        volume=1000.0,
    )


def _snapshot(symbol: str) -> MarketSnapshot:
    """Build one quote-only composite snapshot.

    Args:
        symbol: Provider-native symbol.

    Returns:
        Composite snapshot with explicit missing bar evidence.
    """
    return MarketSnapshot(
        symbol=symbol,
        level1=Level1Snapshot(
            symbol=symbol,
            bid=Decimal("1.0999"),
            ask=Decimal("1.1001"),
            last=Decimal("1.1000"),
            spread=Decimal("0.0002"),
            volume=Decimal(1000),
            price_unit="quote_currency",
            source_time=_T0,
            receive_time=_T0,
            quote_age_seconds=0.0,
            request_id=generate_id("req"),
        ),
        latest_bar=None,
        generated_at=_T0,
        request_id=generate_id("req"),
    )


@pytest.fixture
def isolated_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace provider reads and reset quote cache.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    quotes._reset_quote_cache_for_tests()

    def _fake_metadata(*, source_id: str, symbol: str, request_id: str) -> object:
        del source_id, request_id
        return _success(_metadata(symbol))

    def _fake_snapshot(
        *, source_id: str, symbol: str, timeframe: str, request_id: str
    ) -> object:
        del source_id, timeframe, request_id
        return _success(_snapshot(symbol))

    monkeypatch.setattr(symbol_discovery, "get_symbol_metadata", _fake_metadata)
    monkeypatch.setattr(projection, "get_market_snapshot", _fake_snapshot)


def test_get_symbols_quotes_enriches_exact_requested_symbols(
    isolated_quotes: None,
) -> None:
    """Quote retrieval enriches exactly the requested symbols."""
    del isolated_quotes
    response = quotes.get_symbols_quotes(
        SymbolsQuoteRequest(
            source_id="mt5",
            symbols=("EURUSD", "US500"),
            request_id=generate_id("req"),
        )
    )

    assert response.status == "success"
    assert response.data is not None
    assert response.data.limit == 2
    rows = {row.symbol: row for row in response.data.rows}
    assert set(rows) == {"EURUSD", "US500"}
    assert rows["EURUSD"].asset_class == "Forex"
    assert rows["US500"].asset_class == "Indices"


def test_get_symbols_quotes_skips_unreadable_symbol(
    isolated_quotes: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unreadable symbol is omitted without failing the whole request."""
    del isolated_quotes
    real_metadata = symbol_discovery.get_symbol_metadata

    def _fake_metadata(*, source_id: str, symbol: str, request_id: str) -> object:
        if symbol == "XAUUSD":
            return _failure()
        return real_metadata(source_id=source_id, symbol=symbol, request_id=request_id)

    monkeypatch.setattr(symbol_discovery, "get_symbol_metadata", _fake_metadata)
    response = quotes.get_symbols_quotes(
        SymbolsQuoteRequest(
            source_id="mt5",
            symbols=("EURUSD", "XAUUSD"),
            request_id=generate_id("req"),
        )
    )

    assert response.status == "success"
    assert response.data is not None
    assert [row.symbol for row in response.data.rows] == ["EURUSD"]
