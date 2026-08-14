"""Unit tests for the composed market snapshot feature (feature)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.data import build_market_snapshot_request, get_market_snapshot
from app.services.data.market_data import snapshot
from app.services.data.market_data.level1 import Level1Snapshot
from app.utils import generate_id

_T0 = datetime(2026, 8, 7, 12, tzinfo=UTC)


def _fake_level1(request: object) -> Level1Snapshot:
    """Return one genuine Level1Snapshot fixture."""
    return Level1Snapshot(
        symbol="EURUSD",
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        last=None,
        spread=Decimal("0.0002"),
        volume=None,
        price_unit="quote_currency",
        source_time=_T0,
        receive_time=_T0,
        quote_age_seconds=0.0,
        request_id=request.request_id,  # type: ignore[attr-defined]
    )


def _fake_bar_dataset() -> SimpleNamespace:
    """Return one structural single-bar dataset fixture."""
    bar = SimpleNamespace(timestamp=_T0, close=Decimal("1.1001"))
    return SimpleNamespace(records=(bar,))


@pytest.fixture
def isolated_snapshot(monkeypatch: pytest.MonkeyPatch):
    """Replace source access and retrieval with deterministic fakes."""
    from app.services.data.sources import composition

    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)
    monkeypatch.setattr(snapshot, "_get_level1_snapshot_raw", _fake_level1)
    monkeypatch.setattr(
        snapshot, "_fetch_market_dataset_raw", lambda _request: _fake_bar_dataset()
    )


def test_get_market_snapshot_composes_level1_and_latest_bar(
    isolated_snapshot: None,
) -> None:
    """The snapshot carries both the Level-1 quote and the latest closed bar."""
    del isolated_snapshot
    request = build_market_snapshot_request(
        source_id="mt5", symbol="EURUSD", timeframe="M1", request_id=generate_id("req")
    )
    response = get_market_snapshot(request)

    assert response.status == "success"
    assert response.data is not None
    assert response.data.symbol == "EURUSD"
    assert response.data.level1.bid == Decimal("1.1000")
    assert response.data.latest_bar is not None
    assert response.data.latest_bar.close == Decimal("1.1001")  # type: ignore[attr-defined]


def test_get_market_snapshot_synchronizes_history_before_level1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MT5 symbol selection/history completes before the first quote read."""
    from app.services.data.sources import composition

    calls: list[str] = []
    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)

    def _history(_request: object) -> SimpleNamespace:
        calls.append("history")
        return _fake_bar_dataset()

    def _level1(request: object) -> Level1Snapshot:
        calls.append("level1")
        return _fake_level1(request)

    monkeypatch.setattr(snapshot, "_fetch_market_dataset_raw", _history)
    monkeypatch.setattr(snapshot, "_get_level1_snapshot_raw", _level1)

    response = get_market_snapshot(
        source_id="mt5",
        symbol="XAUUSD",
        timeframe="D1",
        request_id=generate_id("req"),
    )

    assert response.status == "success"
    assert calls == ["history", "level1"]


def test_get_market_snapshot_supports_direct_keywords(
    isolated_snapshot: None,
) -> None:
    """Direct keyword calls build the same snapshot as a typed request."""
    del isolated_snapshot
    response = get_market_snapshot(source_id="mt5", symbol="EURUSD", timeframe="M1")

    assert response.status == "success"
    assert response.data is not None
    assert response.data.symbol == "EURUSD"


def test_get_market_snapshot_degrades_when_bar_leg_unavailable(
    isolated_snapshot: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing bar leg degrades to `latest_bar=None`, never a fabricated bar."""
    del isolated_snapshot

    def _raise(_request: object) -> object:
        raise RuntimeError("no bar evidence")

    monkeypatch.setattr(snapshot, "_fetch_market_dataset_raw", _raise)
    request = build_market_snapshot_request(
        source_id="mt5", symbol="EURUSD", timeframe="M1", request_id=generate_id("req")
    )

    response = get_market_snapshot(request)

    assert response.status == "success"
    assert response.data is not None
    assert response.data.latest_bar is None
