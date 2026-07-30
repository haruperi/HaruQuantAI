"""Unit tests for FEAT-DATA-01 canonical market records."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import OHLCVRecord, SpreadRecord, TickRecord
from pydantic import ValidationError

START = datetime(2026, 1, 1, tzinfo=UTC)
AVAILABLE = START + timedelta(minutes=1, seconds=1)


def make_bar() -> OHLCVRecord:
    """Return one exact canonical OHLCV record for record validation."""
    return OHLCVRecord(
        timestamp=START,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=AVAILABLE,
    )


def test_ohlcv_record_rejects_invalid_range() -> None:
    """Open and close must remain inside the measured low/high range."""
    values = make_bar().model_dump()
    values["open"] = Decimal(12)
    with pytest.raises(ValidationError, match="open must be within"):
        OHLCVRecord(**values)


def test_tick_record_rejects_crossed_quote() -> None:
    """A canonical tick never normalizes a crossed quote silently."""
    with pytest.raises(ValidationError, match="ask must not be below bid"):
        TickRecord(
            timestamp=START,
            bid=Decimal(11),
            ask=Decimal(10),
            price_unit="USD",
            source="fixture",
            source_symbol="ABC",
            available_at=AVAILABLE,
        )


def test_spread_record_requires_unit() -> None:
    """Spread scale and unit are mandatory evidence."""
    with pytest.raises(ValidationError):
        SpreadRecord(
            timestamp=START,
            spread=Decimal("0.1"),
            scale=2,
            source="fixture",
            source_symbol="ABC",
            available_at=AVAILABLE,
        )  # type: ignore[call-arg]
