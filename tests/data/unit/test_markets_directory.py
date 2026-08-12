"""Unit tests for the Data-owned market-directory aggregator.

The three Data public calls (``list_symbols``, ``get_symbol_metadata``,
``get_market_snapshot``) are monkeypatched at the module boundary so no
external source is contacted. Each case verifies one row-projection or
degradation behavior of ``list_market_directory``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.market_data import directory_projection as projection
from app.services.data.market_data import market_directory as directory
from app.services.data.market_data import symbol_quotes as quotes
from app.services.data.market_data.directory_contracts import MarketDirectoryRequest
from app.services.data.market_data.level1 import Level1Snapshot
from app.services.data.market_data.market_directory import list_market_directory
from app.services.data.market_data.snapshot import MarketSnapshot
from app.services.data.market_data.symbol_metadata import SymbolPage
from app.utils import generate_id

_T0 = datetime(2026, 8, 10, 12, tzinfo=UTC)
_REQ_ID = generate_id("req")


def _success(data: object) -> object:
    """Wrap one raw result in a minimal success standard response."""
    return SimpleNamespace(
        status="success",
        data=data,
        message="ok",
        error=None,
        metadata=SimpleNamespace(),
    )


def _failure(code: str = "SOURCE_UNAVAILABLE") -> object:
    """Wrap one failure standard response."""
    return SimpleNamespace(
        status="error",
        data=None,
        message="fail",
        error=SimpleNamespace(
            code=code, details={}, message="fail", request_id="req-x"
        ),
        metadata=SimpleNamespace(),
    )


def _page(symbols: tuple[str, ...], next_cursor: str | None = None) -> SymbolPage:
    """Build a symbol page fixture."""
    return SymbolPage(
        source_id="mt5",
        items=symbols,
        limit=100,
        next_cursor=next_cursor,
        revision="rev-1",
        request_id=_REQ_ID,
    )


def _metadata(
    symbol: str,
    *,
    path: str | None = "Forex\\Majors",
    name: str | None = None,
    description: str | None = None,
    digits: int | None = 5,
    last: float | None = 1.10,
    bid: float | None = 1.0999,
    ask: float | None = 1.1001,
    volume: float | None = 1000.0,
) -> dict[str, object]:
    """Build a plain metadata mapping fixture."""
    meta: dict[str, object] = {
        "canonical_symbol": symbol,
        "provider_symbol": symbol,
        "asset_class": "mt5",
        "source_id": "mt5",
    }
    if path is not None:
        meta["path"] = path
    if name is not None:
        meta["name"] = name
    if description is not None:
        meta["description"] = description
    if digits is not None:
        meta["digits"] = digits
    if last is not None:
        meta["last"] = last
    if bid is not None:
        meta["bid"] = bid
    if ask is not None:
        meta["ask"] = ask
    if volume is not None:
        meta["volume"] = volume
    return meta


def _level1(
    symbol: str, *, bid: Decimal, ask: Decimal, last: Decimal | None
) -> Level1Snapshot:
    """Build a Level1Snapshot fixture."""
    return Level1Snapshot(
        symbol=symbol,
        bid=bid,
        ask=ask,
        last=last,
        spread=ask - bid,
        volume=Decimal(1500),
        price_unit="quote_currency",
        source_time=_T0,
        receive_time=_T0,
        quote_age_seconds=0.0,
        request_id=_REQ_ID,
    )


def _snapshot(symbol: str) -> MarketSnapshot:
    """Build a market snapshot fixture with a D1 bar."""
    bar = OHLCVRecord(
        timestamp=_T0,
        source="mt5",
        source_symbol=symbol,
        available_at=_T0,
        open=Decimal("1.0950"),
        high=Decimal("1.1050"),
        low=Decimal("1.0900"),
        close=Decimal("1.1005"),
        volume=Decimal(2000),
        price_unit="quote_currency",
        volume_unit="lots",
    )
    return MarketSnapshot(
        symbol=symbol,
        level1=_level1(
            symbol, bid=Decimal("1.0999"), ask=Decimal("1.1001"), last=Decimal("1.1000")
        ),
        latest_bar=cast("object", bar),
        generated_at=_T0,
        request_id=_REQ_ID,
    )


@pytest.fixture
def isolated_directory(monkeypatch: pytest.MonkeyPatch):
    """Replace the three Data public calls with pass-through stubs.

    Individual tests override specific stubs to exercise failure modes. Also
    clears the in-process directory cache so one test's cached page can never
    leak into the next test's assertions.
    """
    directory._reset_directory_cache_for_tests()
    quotes._reset_quote_cache_for_tests()

    def _fake_list_symbols(request: object) -> object:
        # SymbolPage.items must be deterministically sorted; mirror the broker
        # adapter's behaviour so the fixture validates.
        return _success(_page(("EURUSD", "US500", "XAUUSD")))

    def _fake_get_symbol_metadata(
        *, source_id: str, symbol: str, request_id: str
    ) -> object:
        configs: dict[str, dict[str, object]] = {
            "EURUSD": _metadata("EURUSD"),
            "XAUUSD": _metadata("XAUUSD", path="Forex\\Metals"),
            "US500": _metadata(
                "US500",
                path="Indices\\US500",
                digits=2,
                last=5000.0,
                bid=4999.5,
                ask=5000.5,
            ),
        }
        return _success(SimpleNamespace(**configs[symbol]))

    def _fake_get_market_snapshot(
        *, source_id: str, symbol: str, timeframe: str, request_id: str
    ) -> object:
        return _success(_snapshot(symbol))

    monkeypatch.setattr(directory, "list_symbols", _fake_list_symbols)
    monkeypatch.setattr(projection, "get_market_snapshot", _fake_get_market_snapshot)
    # ``_fetch_symbol_metadata_raw`` imports get_symbol_metadata lazily; patch
    # the lazy import target inside symbol_discovery to avoid source contact.
    from app.services.data.market_data import symbol_discovery

    monkeypatch.setattr(
        symbol_discovery, "get_symbol_metadata", _fake_get_symbol_metadata
    )


def test_directory_classifies_and_projects_rows(isolated_directory: None) -> None:
    """Each symbol is classified and its quote/OHLC evidence projected."""
    del isolated_directory
    request = MarketDirectoryRequest(
        source_id="mt5", limit=100, request_id=generate_id("req")
    )
    response = list_market_directory(request)

    assert response.status == "success"
    directory_data = response.data
    assert directory_data is not None
    rows = {row.symbol: row for row in directory_data.rows}
    assert set(rows) == {"EURUSD", "XAUUSD", "US500"}
    assert rows["EURUSD"].asset_class == "Forex"
    assert rows["XAUUSD"].asset_class == "Commodities"  # metal override
    assert rows["US500"].asset_class == "Indices"
    eur = rows["EURUSD"]
    assert eur.last == pytest.approx(1.0999)
    assert eur.bid == pytest.approx(1.0999)
    assert eur.open == pytest.approx(1.0950)
    assert eur.close == pytest.approx(1.1005)
    assert eur.change == pytest.approx(1.0999 - 1.0950)
    assert eur.change_percent == pytest.approx((1.0999 - 1.0950) / 1.0950 * 100.0)


def test_directory_uses_bid_when_provider_last_trade_is_zero(
    isolated_directory: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OTC zero last-trade values never mask a usable Level-1 bid."""
    del isolated_directory

    def _zero_last_snapshot(symbol: str) -> MarketSnapshot:
        snapshot = _snapshot(symbol)
        return snapshot.model_copy(
            update={
                "level1": _level1(
                    symbol,
                    bid=Decimal("1.2345"),
                    ask=Decimal("1.2347"),
                    last=Decimal(0),
                )
            }
        )

    def _fake_snapshot(
        *, source_id: str, symbol: str, timeframe: str, request_id: str
    ) -> object:
        del source_id, timeframe, request_id
        return _success(_zero_last_snapshot(symbol))

    monkeypatch.setattr(projection, "get_market_snapshot", _fake_snapshot)

    response = list_market_directory(
        MarketDirectoryRequest(
            source_id="mt5", limit=100, request_id=generate_id("req")
        )
    )

    assert response.status == "success"
    rows = {row.symbol: row for row in response.data.rows}
    assert rows["EURUSD"].last == pytest.approx(1.2345)


def test_directory_excludes_uncategorizable_symbols(
    isolated_directory: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Symbols classifying as Other are excluded from the directory."""
    del isolated_directory

    def _fake_list_symbols(_request: object) -> object:
        return _success(_page(("EURUSD", "WEIRD1")))

    monkeypatch.setattr(directory, "list_symbols", _fake_list_symbols)

    from app.services.data.market_data import symbol_discovery

    def _fake_meta(*, source_id: str, symbol: str, request_id: str) -> object:
        meta = (
            _metadata(symbol)
            if symbol == "EURUSD"
            else _metadata(symbol, path="Custom\\Bonds")
        )
        return _success(SimpleNamespace(**meta))

    monkeypatch.setattr(symbol_discovery, "get_symbol_metadata", _fake_meta)

    response = list_market_directory(
        MarketDirectoryRequest(
            source_id="mt5", limit=100, request_id=generate_id("req")
        )
    )
    assert response.status == "success"
    rows = [row.symbol for row in response.data.rows]
    assert rows == ["EURUSD"]


def test_directory_degrades_when_snapshot_fails(
    isolated_directory: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed snapshot leaves OHLC null but keeps the row with metadata quotes."""
    del isolated_directory

    def _raise(
        *, source_id: str, symbol: str, timeframe: str, request_id: str
    ) -> object:
        return _failure("SNAPSHOT_UNAVAILABLE")

    monkeypatch.setattr(projection, "get_market_snapshot", _raise)

    response = list_market_directory(
        MarketDirectoryRequest(
            source_id="mt5", limit=100, request_id=generate_id("req")
        )
    )
    assert response.status == "success"
    rows = {row.symbol: row for row in response.data.rows}
    assert "EURUSD" in rows
    eur = rows["EURUSD"]
    assert eur.open is None  # OHLC comes from the snapshot
    assert eur.high is None
    assert eur.last == pytest.approx(1.0999)  # falls back to metadata bid


def test_directory_skips_symbol_when_metadata_fails(
    isolated_directory: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symbol whose metadata cannot be resolved is skipped entirely."""
    del isolated_directory
    from app.services.data.market_data import symbol_discovery

    real_meta = symbol_discovery.get_symbol_metadata

    def _fake_meta(*, source_id: str, symbol: str, request_id: str) -> object:
        if symbol == "XAUUSD":
            return _failure("SYMBOL_NOT_FOUND")
        return real_meta(source_id=source_id, symbol=symbol, request_id=request_id)

    monkeypatch.setattr(symbol_discovery, "get_symbol_metadata", _fake_meta)

    response = list_market_directory(
        MarketDirectoryRequest(
            source_id="mt5", limit=100, request_id=generate_id("req")
        )
    )
    assert response.status == "success"
    rows = [row.symbol for row in response.data.rows]
    assert "XAUUSD" not in rows
    assert "EURUSD" in rows


def test_directory_requires_keywords_without_typed_request() -> None:
    """Direct-call style without source_id/limit surfaces a failure response.

    The boundary runner normalizes the raised ValueError into a standard
    error response, so the assertion is on the response status, not a raise.
    """
    response = list_market_directory(source_id=None, limit=None)
    assert response.status == "error"
