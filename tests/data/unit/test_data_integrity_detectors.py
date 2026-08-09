"""Unit tests for the data-integrity taxonomy detectors (TC-IMP-DATA-06)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data import (
    detect_clock_drift,
    detect_out_of_order_records,
    detect_source_disagreement,
    detect_stale_quote,
)
from app.services.data.contracts.records import OHLCVRecord, TickRecord

_T0 = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


def _tick(t: datetime, *, available_at: datetime | None = None) -> TickRecord:
    """Return one minimal valid tick fixture."""
    return TickRecord(
        timestamp=t,
        source="mt5",
        source_symbol="EURUSD",
        available_at=available_at or t,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1001"),
        price_unit="quote_currency",
    )


def _bar(t: datetime, close: str, source: str) -> OHLCVRecord:
    """Return one minimal valid OHLCV fixture."""
    return OHLCVRecord(
        timestamp=t,
        source=source,
        source_symbol="EURUSD",
        available_at=t,
        open=Decimal("1.10"),
        high=Decimal("1.20"),
        low=Decimal("1.09"),
        close=Decimal(close),
        price_unit="quote_currency",
        volume=Decimal(100),
        volume_unit="lots",
    )


def test_detect_out_of_order_records_flags_a_timestamp_reversal() -> None:
    """A record whose timestamp precedes its predecessor is flagged."""
    records = (_tick(_T0), _tick(_T0 - timedelta(seconds=1)))
    response = detect_out_of_order_records(records)
    assert response.status == "success"
    assert response.data is not None
    assert response.data.code == "OUT_OF_ORDER"
    assert response.data.affected_count == 1


def test_detect_out_of_order_records_returns_none_when_monotonic() -> None:
    """A strictly increasing series raises no issue."""
    records = (_tick(_T0), _tick(_T0 + timedelta(seconds=1)))
    response = detect_out_of_order_records(records)
    assert response.data is None


def test_detect_clock_drift_flags_delayed_receive_time() -> None:
    """A record received well after its event time is flagged."""
    records = (_tick(_T0, available_at=_T0 + timedelta(seconds=30)),)
    response = detect_clock_drift(records, max_drift_seconds=5.0)
    assert response.data is not None
    assert response.data.code == "CLOCK_DRIFT"


def test_detect_clock_drift_returns_none_within_bound() -> None:
    """A record received promptly raises no issue."""
    records = (_tick(_T0, available_at=_T0 + timedelta(seconds=1)),)
    response = detect_clock_drift(records, max_drift_seconds=5.0)
    assert response.data is None


def test_detect_stale_quote_flags_an_aged_receive_time() -> None:
    """The newest record's age beyond the bound is flagged."""
    records = (_tick(_T0, available_at=_T0),)
    response = detect_stale_quote(
        records, _T0 + timedelta(seconds=120), max_age_seconds=60.0
    )
    assert response.data is not None
    assert response.data.code == "STALE_QUOTE"


def test_detect_stale_quote_returns_none_when_fresh() -> None:
    """A recently received record raises no issue."""
    records = (_tick(_T0, available_at=_T0),)
    response = detect_stale_quote(
        records, _T0 + timedelta(seconds=10), max_age_seconds=60.0
    )
    assert response.data is None


def test_detect_source_disagreement_flags_beyond_tolerance() -> None:
    """A primary/backup close difference beyond tolerance is flagged."""
    primary = (_bar(_T0, "1.1050", "mt5"),)
    backup = (_bar(_T0, "1.1200", "binance"),)
    response = detect_source_disagreement(primary, backup, tolerance=Decimal("0.01"))
    assert response.data is not None
    assert response.data.code == "SOURCE_DISAGREEMENT"


def test_detect_source_disagreement_returns_none_within_tolerance() -> None:
    """A close difference within tolerance raises no issue."""
    primary = (_bar(_T0, "1.1050", "mt5"),)
    backup = (_bar(_T0, "1.1051", "binance"),)
    response = detect_source_disagreement(primary, backup, tolerance=Decimal("0.01"))
    assert response.data is None


def test_detect_source_disagreement_ignores_unmatched_timestamps() -> None:
    """A timestamp present only in one source is not evidence of disagreement."""
    primary = (_bar(_T0, "1.1050", "mt5"),)
    backup = (_bar(_T0 + timedelta(minutes=1), "1.1900", "binance"),)
    response = detect_source_disagreement(primary, backup, tolerance=Decimal("0.01"))
    assert response.data is None
