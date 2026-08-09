"""Unit tests for the Level-1 quote snapshot feature (TC-IMP-DATA-02)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.data import build_level1_snapshot_request, get_level1_snapshot
from app.services.data.market_data import level1
from app.utils import generate_id


def _fake_tick(*, bid: str, ask: str, timestamp: datetime) -> SimpleNamespace:
    """Return one structural tick-record fixture."""
    return SimpleNamespace(
        bid=Decimal(bid),
        ask=Decimal(ask),
        last=None,
        volume=Decimal("12.5"),
        price_unit="quote_currency",
        timestamp=timestamp,
    )


@pytest.fixture
def isolated_level1(monkeypatch: pytest.MonkeyPatch):
    """Replace source access and dataset retrieval with deterministic fakes."""
    from app.services.data.sources import composition

    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)

    def _fake_fetch(request: object) -> SimpleNamespace:
        timestamp = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
        return SimpleNamespace(
            records=(_fake_tick(bid="1.1000", ask="1.1002", timestamp=timestamp),),
            available_at=timestamp,
        )

    monkeypatch.setattr(level1, "_fetch_market_dataset_raw", _fake_fetch)


def test_get_level1_snapshot_composes_bid_ask_spread_and_freshness(
    isolated_level1: None,
) -> None:
    """The snapshot discloses bid/ask/spread, source/receive time, and freshness."""
    del isolated_level1
    request = build_level1_snapshot_request(
        source_id="mt5", symbol="EURUSD", request_id=generate_id("req")
    )
    response = get_level1_snapshot(request)

    assert response.status == "success"
    assert response.data is not None
    snapshot = response.data
    assert snapshot.symbol == "EURUSD"
    assert snapshot.bid == Decimal("1.1000")
    assert snapshot.ask == Decimal("1.1002")
    assert snapshot.spread == Decimal("0.0002")
    assert snapshot.source_time == datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    assert snapshot.receive_time == datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    assert snapshot.quote_age_seconds >= 0.0


def test_get_level1_snapshot_supports_direct_keywords(
    isolated_level1: None,
) -> None:
    """Direct keyword calls build the same snapshot as a typed request."""
    del isolated_level1
    response = get_level1_snapshot(source_id="mt5", symbol="EURUSD")

    assert response.status == "success"
    assert response.data is not None
    assert response.data.symbol == "EURUSD"


def test_level1_snapshot_request_rejects_missing_keywords() -> None:
    """A direct call without both required keywords fails closed."""
    with pytest.raises(ValueError, match="source_id and symbol are required"):
        level1._level1_snapshot_request(
            None, source_id=None, symbol=None, request_id=None
        )


def test_level1_snapshot_freshness_reflects_receive_time_age(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An older receive time produces a strictly positive freshness value."""
    from app.services.data.sources import composition

    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)
    stale_time = datetime.now(UTC) - timedelta(seconds=5)

    def _fake_fetch(request: object) -> SimpleNamespace:
        return SimpleNamespace(
            records=(_fake_tick(bid="1.1000", ask="1.1002", timestamp=stale_time),),
            available_at=stale_time,
        )

    monkeypatch.setattr(level1, "_fetch_market_dataset_raw", _fake_fetch)
    request = build_level1_snapshot_request(
        source_id="mt5", symbol="EURUSD", request_id=generate_id("req")
    )
    response = get_level1_snapshot(request)

    assert response.data is not None
    assert response.data.quote_age_seconds >= 5.0
