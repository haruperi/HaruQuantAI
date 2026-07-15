"""Dukascopy BI5 mapping tests."""

import struct
from datetime import UTC, datetime

from app.services.brokers.dukascopy.mapping import _map_ticks


def test_dukascopy_mapping_is_tick_only() -> None:
    """BI5 values produce genuine quote ticks without sequence invention."""
    payload = struct.pack(">3I2f", 1000, 110001, 110000, 1.5, 2.5)
    ticks = _map_ticks(
        payload,
        symbol="EURUSD",
        hour=datetime(2026, 1, 1, tzinfo=UTC),
        price_divisor=100000,
        limit=1,
    )
    assert ticks[0].provider_sequence_id is None
    assert str(ticks[0].bid) == "1.1"


def test_dukascopy_mapping_malformed_length() -> None:
    """_map_ticks raises ValueError for malformed record length."""
    import pytest

    with pytest.raises(ValueError, match="malformed Dukascopy BI5 record length"):
        _map_ticks(
            b"\x00" * 5,  # not divisible by 20 bytes
            symbol="EURUSD",
            hour=datetime(2026, 1, 1, tzinfo=UTC),
            price_divisor=100000,
            limit=10,
        )


def test_dukascopy_mapping_naive_datetime() -> None:
    """_map_ticks raises ValueError for naive datetime."""
    import pytest

    with pytest.raises(ValueError, match="Dukascopy hour must be timezone-aware"):
        _map_ticks(
            b"",
            symbol="EURUSD",
            hour=datetime(2026, 1, 1),  # naive  # noqa: DTZ001
            price_divisor=100000,
            limit=10,
        )


def test_dukascopy_mapping_under_limit() -> None:
    """_map_ticks stops decoding when payload is empty or limit is not reached."""
    payload = struct.pack(">3I2f", 1000, 110001, 110000, 1.5, 2.5)
    ticks = _map_ticks(
        payload,
        symbol="EURUSD",
        hour=datetime(2026, 1, 1, tzinfo=UTC),
        price_divisor=100000,
        limit=10,  # limit is 10, but only 1 record is present
    )
    assert len(ticks) == 1
